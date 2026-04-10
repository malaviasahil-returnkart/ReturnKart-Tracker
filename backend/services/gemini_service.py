"""
RETURNKART.IN — GEMINI AI SERVICE (v2)

Simplified: strip HTML, 5-field prompt, Python handles deadlines.
Model: gemini-2.5-flash via REST (no SDK)
"""
import json
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from backend.config import GEMINI_API_KEY
from backend.models.order import AIOrderContext

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.5-flash:generateContent"
)


def strip_html(raw_text: str) -> str:
    """Strip all HTML tags, return clean readable text."""
    if "<" in raw_text and ">" in raw_text:
        soup = BeautifulSoup(raw_text, "html.parser")
        for tag in soup(["script", "style", "head", "meta", "link"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
    else:
        text = raw_text
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text[:6000]


EXTRACTION_PROMPT = """You are a data extraction bot for ReturnKart.in, an Indian e-commerce return tracker.

Your job: determine if this email is a REAL PRODUCT ORDER, and if so, extract the details.

ONLY extract orders for PHYSICAL PRODUCTS bought from Indian e-commerce platforms.

REJECT and return all nulls for:
- Event tickets (Eventbrite, BookMyShow, Paytm Insider, etc.)
- Food delivery (Swiggy, Zomato, Blinkit, BigBasket, Zepto)
- Cab rides (Uber, Ola, Rapido)
- Bill payments, recharges, subscriptions
- Promotional/marketing emails with no actual order
- Informational emails (account updates, policy changes, recommendations)
- Newsletter or sale announcements
- Emails that mention products but have NO order ID or NO purchase confirmation
- SaaS subscriptions and digital service purchases (Replit, GitHub, Notion, Figma, Canva, Vercel, AWS, Adobe, ChatGPT, etc.)
ONLY process emails that are ACTUAL ORDER CONFIRMATIONS or DELIVERY NOTIFICATIONS for physical products from:
Amazon, Flipkart, Myntra, Meesho, Ajio, Nykaa, Croma, Tata CLiQ, Snapdeal, JioMart, Temu,,
H&M, Zara, Uniqlo, Mango, Forever 21, Marks & Spencer, GAP, Superdry, Benetton,
Tommy Hilfiger, Calvin Klein, Ralph Lauren, Michael Kors, Hugo Boss, Guess, Charles & Keith, Aldo, Coach,
Nike, Adidas, Puma, Reebok, Skechers, New Balance, ASICS, Under Armour, Crocs, Decathlon,
Levis, Pepe Jeans, Wrangler, US Polo, Jack & Jones, Vero Moda,
FabIndia, Biba, Libas, Bewakoof, The Souled Store, Snitch, Urbanic, Rare Rabbit,
Bata, Woodland, Clarks, Lenskart, Titan

Return ONLY a valid JSON object. No markdown, no explanation, no code fences.

JSON schema:
{"order_id": "string or null", "brand": "string or null", "item_name": "string or null", "purchase_price": 0.00, "delivery_date": "YYYY-MM-DD or null"}

Rules:
- If this is NOT a real product order, return: {"order_id": null, "brand": null, "item_name": null, "purchase_price": 0, "delivery_date": null}
- order_id: the platform order/transaction ID from a confirmed purchase
- brand: the e-commerce platform (Amazon, Flipkart, Myntra, etc.)
- item_name: the actual physical product ordered
- purchase_price: amount in INR, numeric only. 0 if not found.
- delivery_date: in YYYY-MM-DD format. null if not found.
- Do NOT invent data. Do NOT guess. Only extract what is explicitly stated.

Email text:
"""


async def _call_gemini_api(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
        },
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()


async def call_gemini(prompt: str) -> str:
    """Public helper for other services."""
    return await _call_gemini_api(prompt)


async def extract_order_from_email(
    email_text: str,
    platform_slug: str = "unknown",
) -> Optional[AIOrderContext]:
    try:
        clean_text = strip_html(email_text)
        if len(clean_text.strip()) < 20:
            print("[Gemini] Email too short after stripping, skipping")
            return None

        prompt = EXTRACTION_PROMPT + clean_text + "\n\nJSON:"
        raw = await _call_gemini_api(prompt)

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)

        # Validate: must have order_id AND item_name to be a real order
        order_id = data.get("order_id")
        item_name = data.get("item_name")
        brand = data.get("brand")

        if not order_id or not item_name:
            print(f"[Gemini] Skipped: no order_id or item_name (brand={brand})")
            return None

        return AIOrderContext(
            order_id=order_id,
            brand=brand,
            item_name=item_name,
            total_amount=data.get("purchase_price") or 0.0,
            currency="INR",
            order_date=data.get("delivery_date"),
            category=None,
            courier_partner=None,
            delivery_pincode=None,
            confidence=0.8,
        )

    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[Gemini] Extraction error: {e}")
        return None
