"""
RETURNKART.IN — PLATFORMS API
AI-powered platform onboarding. User enters a platform name + URL,
Gemini researches it and auto-generates email domains, return policies,
communication channels. Saves to `platforms` table.

Endpoints:
  POST   /api/platforms/add      → AI-research + save new platform
  GET    /api/platforms           → list all platforms for a user (+ global)
  DELETE /api/platforms/{id}      → delete a user-added platform
"""
import json
from fastapi import APIRouter, HTTPException, Request

from backend.config import GEMINI_API_KEY
from backend.services.supabase_service import (
    save_platform,
    get_platforms_for_user,
    delete_platform,
)

router = APIRouter()


def _slugify(name: str) -> str:
    return name.lower().strip().replace(' ', '_').replace('.', '_').replace('-', '_')


async def _research_platform_with_gemini(platform_name: str, website_url: str = None) -> dict:
    """
    Ask Gemini to research an ecommerce platform and return structured data
    about email domains, return policies, and communication channels.
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are an Indian ecommerce research assistant for ReturnKart.in.

Research the ecommerce platform "{platform_name}"{f' (website: {website_url})' if website_url else ''} and return a JSON object with this EXACT structure (no markdown, no backticks, just raw JSON):

{{
  "platform_name": "Display name of the platform",
  "website_url": "https://...",
  "email_domains": ["list of domains they send order/shipping emails from, e.g. amazon.in, amazon.com"],
  "email_sender_patterns": ["list of sender email patterns, e.g. shipment-tracking@amazon.in, auto-confirm@amazon.in"],
  "return_policy": {{
    "fashion": {{"window_days": 10, "refund_type": "full", "notes": "any special conditions"}},
    "electronics": {{"window_days": 7, "refund_type": "replacement_only", "notes": ""}},
    "general": {{"window_days": 7, "refund_type": "full", "notes": "default policy"}}
  }},
  "communication_channels": {{
    "order_confirmation": ["email", "sms", "app_notification", "whatsapp"],
    "shipping_update": ["email", "sms", "app_notification", "whatsapp"],
    "delivery_confirmation": ["email", "sms", "app_notification"],
    "return_reminder": ["email", "app_notification"]
  }}
}}

If you're not sure about specific details, use reasonable defaults based on Indian ecommerce norms. Always include at least one email domain and the general return policy."""

        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean any markdown backticks
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        if text.endswith('```'):
            text = text[:-3]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()

        result = json.loads(text)
        return result

    except json.JSONDecodeError as e:
        print(f"Gemini returned invalid JSON: {e}")
        # Return minimal defaults
        return {
            "platform_name": platform_name,
            "website_url": website_url or "",
            "email_domains": [],
            "email_sender_patterns": [],
            "return_policy": {"general": {"window_days": 7, "refund_type": "full", "notes": "AI could not determine specific policy"}},
            "communication_channels": {"order_confirmation": ["email"], "shipping_update": ["email"], "delivery_confirmation": ["email"]},
        }
    except Exception as e:
        print(f"Gemini research error: {e}")
        return {
            "platform_name": platform_name,
            "website_url": website_url or "",
            "email_domains": [],
            "email_sender_patterns": [],
            "return_policy": {"general": {"window_days": 7, "refund_type": "full", "notes": "Default"}},
            "communication_channels": {"order_confirmation": ["email"]},
        }


@router.post("/add")
async def add_platform(request: Request):
    """
    User submits a platform name + optional URL.
    Gemini researches it, generates structured data, saves to DB.
    """
    body = await request.json()
    user_id = body.get("user_id")
    platform_name = body.get("platform_name", "").strip()
    website_url = body.get("website_url", "").strip()

    if not user_id or not platform_name:
        raise HTTPException(status_code=400, detail="user_id and platform_name are required")

    slug = _slugify(platform_name)

    # AI research
    ai_data = await _research_platform_with_gemini(platform_name, website_url or None)

    # Save to DB
    result = await save_platform(
        user_id=user_id,
        platform_name=ai_data.get("platform_name", platform_name),
        platform_slug=slug,
        website_url=ai_data.get("website_url", website_url),
        email_domains=ai_data.get("email_domains", []),
        email_sender_patterns=ai_data.get("email_sender_patterns", []),
        return_policy=ai_data.get("return_policy", {}),
        communication_channels=ai_data.get("communication_channels", {}),
    )

    return {
        "platform": result,
        "ai_research": ai_data,
        "message": f"Platform '{platform_name}' added successfully. AI has configured email tracking and return policies."
    }


@router.get("")
async def list_platforms(request: Request):
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    platforms = await get_platforms_for_user(user_id)
    return {"platforms": platforms, "count": len(platforms)}


@router.delete("/{platform_id}")
async def remove_platform(platform_id: str, request: Request):
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    await delete_platform(platform_id, user_id)
    return {"status": "deleted", "message": "Platform removed"}
