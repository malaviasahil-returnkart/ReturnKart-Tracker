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

Extract order information from the email text below.
Return ONLY a valid JSON object. No markdown, no explanation, no code fences, no extra text.

JSON schema (return EXACTLY this structure):
{"order_id": "string or null", "brand": "string or null", "item_name": "string or null", "purchase_price": 0.00, "delivery_date": "YYYY-MM-DD or null"}

Rules:
- order_id: the platform order/transaction ID
- brand: e-commerce platform name (Amazon, Flipkart, Myntra, Meesho, Ajio, Nykaa, Temu, etc.)
- item_name: main product name, keep short
- purchase_price: numeric amount in INR, no symbols. 0 if not found.
- delivery_date: actual or estimated delivery date in YYYY-MM-DD. null if not found.
- If a field is not found, use null (or 0 for purchase_price)
- Do NOT invent data. Only extract what is explicitly present.
- Do NOT calculate return deadlines.

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

        return AIOrderContext(
            order_id=data.get("order_id"),
            brand=data.get("brand"),
            item_name=data.get("item_name"),
            total_amount=data.get("purchase_price") or 0.0,
            currency="INR",
            order_date=data.get("delivery_date"),
            category=None,
            courier_partner=None,
            delivery_pincode=None,
            confidence=0.8 if data.get("order_id") else 0.3,
        )

    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[Gemini] Extraction error: {e}")
        return None
