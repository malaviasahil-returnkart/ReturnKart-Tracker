"""
RETURNKART.IN — WHATSAPP EXTRACTION SERVICE

Uses Gemini via REST API (no SDK) — no Python 3.10 import issues.

Two ingestion channels:
  1. Android NotificationListenerService -> short notification text
  2. Meta WhatsApp Business API webhook  -> forwarded message text (iOS + Android)

Both call extract_order_from_whatsapp() which runs Gemini extraction
then upserts to Supabase — identical pipeline to gmail_service.
"""
import json
import re
from typing import Optional

from backend.config import GEMINI_API_KEY
from backend.models.order import OrderCreate
from backend.services.supabase_service import upsert_order
from backend.services.gemini_service import call_gemini

from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))

ECOMMERCE_SENDERS = {
    "amazon", "amazon india", "flipkart", "myntra",
    "meesho", "ajio", "nykaa", "snapdeal", "tata cliq", "jiomart",
}

KNOWN_ECOMMERCE_WABIZ_NUMBERS = {
    "+918069067777",
    "+918010100999",
}


def is_ecommerce_notification(sender: str, text: str) -> bool:
    sender_lower = sender.lower().strip()
    if any(brand in sender_lower for brand in ECOMMERCE_SENDERS):
        return True
    if sender in KNOWN_ECOMMERCE_WABIZ_NUMBERS:
        return True
    keywords = [
        "order", "delivered", "return", "refund", "shipment",
        "dispatch", "out for delivery", "expected delivery",
        "return window", "exchange", "replacement",
    ]
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower) >= 2


def _build_whatsapp_prompt(message_text: str) -> str:
    return f"""You are an AI assistant for ReturnKart.in, an Indian e-commerce return tracker.

Extract order information from the WhatsApp message below.
These messages are SHORT and informal — extract whatever is present.
Return ONLY valid JSON. No markdown, no explanation, no code fences.

Extract this JSON structure:
{{
  "order_id": "order ID string or null",
  "brand": "Amazon India | Flipkart | Myntra | Meesho | Ajio | Nykaa | JioMart | Snapdeal | TataCliq or null",
  "item_name": "product name if mentioned or null",
  "total_amount": number or null,
  "currency": "INR",
  "order_date": "YYYY-MM-DD or null",
  "delivery_date": "YYYY-MM-DD or null",
  "return_deadline": "YYYY-MM-DD or null",
  "category": "Fashion & Apparel | Electronics | Home & Kitchen | Books | Default or null",
  "message_type": "order_placed | shipped | delivered | return_reminder | refund_processed | other",
  "confidence": 0.0 to 1.0
}}

Rules:
- Dates MUST be YYYY-MM-DD format
- total_amount is a number only, no rupee symbol
- confidence: 0.9+ if order_id found, 0.5 if only brand+message_type found
- NEVER invent data. null is better than a guess.

WhatsApp message:
{message_text}

JSON:"""


async def extract_order_from_whatsapp(
    message_text: str,
    user_id: str,
    sender: str = "unknown",
    source_channel: str = "whatsapp_notification",
) -> Optional[dict]:
    if not message_text or not message_text.strip():
        return None
    try:
        prompt = _build_whatsapp_prompt(message_text)
        raw = await call_gemini(prompt)
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)

        if data.get("confidence", 0) < 0.3:
            print(f"[WhatsApp] Low confidence ({data.get('confidence')}) — skipping")
            return None

        from backend.services.date_utils import resolve_order_date
        order = OrderCreate(
            user_id=user_id,
            order_id=data.get("order_id") or f"wa_{sender}_{hash(message_text) % 10**8}",
            brand=data.get("brand") or sender,
            item_name=data.get("item_name") or "Unknown item",
            price=data.get("total_amount") or 0.0,
            order_date=resolve_order_date(
                gemini_date=data.get("order_date"),
                fallback_date=None,
                context=f"whatsapp {sender}",
            ),
            category=data.get("category") or "Default",
            purpose_id="return_tracking",
            consent_timestamp=datetime.now(IST),
            source=source_channel,
        )
        saved = await upsert_order(order)
        return saved

    except json.JSONDecodeError as e:
        print(f"[WhatsApp] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[WhatsApp] Extraction error: {e}")
        return None
