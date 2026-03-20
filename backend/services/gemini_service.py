"""
RETURNKART.IN — GEMINI AI SERVICE
Extract structured order data from invoice emails using Gemini 2.5 Flash + RAG.

Uses Gemini REST API directly (no Python SDK needed).
URL is built at CALL TIME (not import time) to avoid bytecode caching issues.
"""
import json
import re
import requests
from pathlib import Path
from typing import Optional

from backend.config import GEMINI_API_KEY
from backend.models.order import AIOrderContext

# Model name — change this ONE place to upgrade
GEMINI_MODEL = "gemini-2.5-flash"

# Load knowledge base once at module import
_KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
_knowledge_base: Optional[dict] = None


def _get_gemini_url() -> str:
    """Build Gemini URL at call time — avoids Python bytecode cache issues."""
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
                lines.append(
                    f"  - {cat['category']}: {cat['return_window_days']} days "
                    f"({'replacement only' if cat['is_replacement_only'] else 'refund'})"
                )
            return "\n".join(lines)
    fb = kb.get("fallback_policy", {})
    return f"Fallback: {fb.get('return_window_days', 7)} day return window"


def _build_prompt(email_text: str, platform_slug: str, policy_snippet: str) -> str:
    return f"""You are an AI assistant for ReturnKart.in, an Indian e-commerce return tracker.

Your job: extract structured order information from the email below.
Return ONLY valid JSON. No markdown, no explanation, no code fences.

Return policy context for {platform_slug}:
{policy_snippet}

Extract this JSON structure:
{{
  "order_id": "platform order ID string or null",
  "brand": "the brand/store name or null",
  "item_name": "product name string or null",
  "total_amount": number or null,
  "currency": "INR",
  "order_date": "YYYY-MM-DD or null",
  "category": "Fashion & Apparel | Electronics | Home & Kitchen | Books | Default or null",
  "courier_partner": "courier name or null",
  "delivery_pincode": "6-digit pincode or null",
  "confidence": 0.0 to 1.0
}}

Rules:
- order_date MUST be in YYYY-MM-DD format
- total_amount MUST be a number (no currency symbols)
- If you cannot find a field, use null
- confidence: 1.0 = very sure, 0.5 = guessing, 0.0 = not found
- Only extract data explicitly present in the email — never invent data

Email:
{email_text}

JSON:"""


async def extract_order_from_email(
    email_text: str,
    platform_slug: str = "amazon",
) -> Optional[AIOrderContext]:
    """
    Main extraction function.
    Sends email to Gemini 2.5 Flash via REST API.
    URL is built at call time to avoid bytecode cache issues.
    """
    try:
        policy_snippet = _get_platform_policy(platform_slug)
        prompt = _build_prompt(email_text, platform_slug, policy_snippet)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}
        }

        # Build URL at call time — NOT at import time
        url = _get_gemini_url()
        print(f"[Gemini] Calling {GEMINI_MODEL} for platform={platform_slug}")

        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 200:
            print(f"[Gemini] API error {response.status_code}: {response.text[:300]}")
            return None

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            print("[Gemini] No candidates returned")
            return None

        raw = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        if not raw:
            print("[Gemini] Empty text returned")
            return None

        # Strip markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        print(f"[Gemini] Extracted: {parsed.get('brand', '?')} - {parsed.get('item_name', '?')} (conf={parsed.get('confidence', 0)})")
        return AIOrderContext(**parsed)

    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON parse error: {e} | raw: {raw[:200]}")
        return None
    except Exception as e:
        print(f"[Gemini] Extraction error: {e}")
        return None
