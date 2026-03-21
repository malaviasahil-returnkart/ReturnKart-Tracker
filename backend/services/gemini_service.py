"""
RETURNKART.IN — GEMINI AI SERVICE
Extract order data + return policy from emails using Gemini 2.5 Flash.

For unknown brands, Gemini researches the return policy from its training data.
No extra API call needed — it's part of the same extraction prompt.
"""
import json
import re
import requests
from pathlib import Path
from typing import Optional

from backend.config import GEMINI_API_KEY
from backend.models.order import AIOrderContext

GEMINI_MODEL = "gemini-2.5-flash"

_KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
_knowledge_base: Optional[dict] = None


def _get_gemini_url() -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


def _load_knowledge_base() -> dict:
    global _knowledge_base
    if _knowledge_base is None:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            _knowledge_base = json.load(f)
    return _knowledge_base


def _get_platform_policy(platform_slug: str) -> str:
    kb = _load_knowledge_base()
    for p in kb.get("platforms", []):
        if p["brand_slug"] == platform_slug:
            lines = [f"Platform: {p['brand']}"]
            for cat in p.get("categories", []):
                lines.append(f"  - {cat['category']}: {cat['return_window_days']} days ({'replacement only' if cat['is_replacement_only'] else 'refund'})")
            return "\n".join(lines)
    return ""


def _build_prompt(email_text: str, platform_slug: str, policy_snippet: str) -> str:
    policy_context = ""
    if policy_snippet:
        policy_context = f"\nKnown return policy:\n{policy_snippet}\n"

    return f"""You are an AI for ReturnKart.in, an Indian e-commerce return tracker.
Extract order info AND return policy from this email. Return ONLY valid JSON.
{policy_context}
JSON format:
{{"order_id": "string or null", "brand": "string or null", "item_name": "string or null", "total_amount": number or null, "currency": "INR", "order_date": "YYYY-MM-DD or null", "category": "Fashion & Apparel|Electronics|Home & Kitchen|Books|Default or null", "courier_partner": "string or null", "delivery_pincode": "string or null", "return_window_days": number or null, "is_replacement_only": boolean or null, "confidence": 0.0 to 1.0}}

Rules:
- order_date=YYYY-MM-DD, total_amount=number only, null for missing
- return_window_days: If the email mentions a return policy, use that number. If not mentioned, use your knowledge of this brand's standard return policy in India. Common defaults: Amazon 7-10 days, Flipkart 7-10 days, Myntra 7-30 days, Ajio 15 days, Meesho 7 days, H&M 15 days, Zara 30 days, Nike 30 days. If completely unknown, use 10.
- is_replacement_only: true if this brand/category only offers replacement (not refund). Amazon electronics = true. Most fashion = false.
- confidence: 1.0=certain, 0.5=guess, 0.0=not found
- Only extract data from the email — never invent order IDs or prices

Email:
{email_text}

JSON:"""


def _extract_json_from_response(data: dict) -> Optional[str]:
    """Extract JSON from Gemini 2.5 Flash response (thinking model returns multiple parts)."""
    candidates = data.get("candidates", [])
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return None
    for part in reversed(parts):
        text = part.get("text", "").strip()
        if not text:
            continue
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        if text.startswith("{") and "}" in text:
            return text
    for part in parts:
        text = part.get("text", "").strip()
        if text:
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            return text
    return None


async def extract_order_from_email(
    email_text: str,
    platform_slug: str = "amazon",
) -> Optional[AIOrderContext]:
    try:
        policy_snippet = _get_platform_policy(platform_slug)
        prompt = _build_prompt(email_text, platform_slug, policy_snippet)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
        }

        url = _get_gemini_url()
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)

        if response.status_code != 200:
            print(f"[Gemini] API error {response.status_code}: {response.text[:300]}")
            return None

        data = response.json()
        raw = _extract_json_from_response(data)

        if not raw:
            print(f"[Gemini] No JSON in response")
            return None

        parsed = json.loads(raw)
        print(f"[Gemini] OK: {parsed.get('brand', '?')} - {parsed.get('item_name', '?')} (return={parsed.get('return_window_days', '?')}d, conf={parsed.get('confidence', 0)})")
        return AIOrderContext(**parsed)

    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None
