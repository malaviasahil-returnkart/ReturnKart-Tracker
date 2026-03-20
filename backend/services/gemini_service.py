"""
RETURNKART.IN — GEMINI AI SERVICE
Extract structured order data from invoice emails using Gemini 2.5 Flash.

Fixes for Gemini 2.5 Flash (thinking model):
  - maxOutputTokens increased to 8192 (thinking uses many tokens internally)
  - Reads LAST text part from response (thinking models return thinking + text)
  - URL built at call time to avoid bytecode cache issues
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
    fb = kb.get("fallback_policy", {})
    return f"Fallback: {fb.get('return_window_days', 7)} day return window"


def _build_prompt(email_text: str, platform_slug: str, policy_snippet: str) -> str:
    return f"""You are an AI for ReturnKart.in, an Indian e-commerce return tracker.
Extract order info from this email. Return ONLY valid JSON, nothing else.

Return policy for {platform_slug}: {policy_snippet}

JSON format:
{{"order_id": "string or null", "brand": "string or null", "item_name": "string or null", "total_amount": number or null, "currency": "INR", "order_date": "YYYY-MM-DD or null", "category": "Fashion & Apparel|Electronics|Home & Kitchen|Books|Default or null", "courier_partner": "string or null", "delivery_pincode": "string or null", "confidence": 0.0 to 1.0}}

Rules: order_date=YYYY-MM-DD, total_amount=number only, null for missing, confidence 1.0=sure 0.5=guess.

Email:
{email_text}

JSON:"""


def _extract_json_from_response(data: dict) -> Optional[str]:
    """Extract the JSON text from Gemini response.
    Gemini 2.5 Flash is a thinking model — it returns multiple parts:
      parts[0] = thinking/reasoning (may be empty or internal)
      parts[-1] = actual text output
    We search all parts for valid JSON."""
    candidates = data.get("candidates", [])
    if not candidates:
        return None

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return None

    # Try each part, starting from the LAST (most likely to be the actual output)
    for part in reversed(parts):
        text = part.get("text", "").strip()
        if not text:
            continue
        # Strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        # Check if it looks like JSON
        if text.startswith("{") and "}" in text:
            return text

    # Fallback: return whatever text we find
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
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192,
            }
        }

        url = _get_gemini_url()

        response = requests.post(
            url, json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 200:
            print(f"[Gemini] API error {response.status_code}: {response.text[:300]}")
            return None

        data = response.json()
        raw = _extract_json_from_response(data)

        if not raw:
            print(f"[Gemini] No JSON found in response. Parts: {len(data.get('candidates', [{}])[0].get('content', {}).get('parts', []))}")
            return None

        parsed = json.loads(raw)
        print(f"[Gemini] OK: {parsed.get('brand', '?')} - {parsed.get('item_name', '?')} (conf={parsed.get('confidence', 0)})")
        return AIOrderContext(**parsed)

    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None
