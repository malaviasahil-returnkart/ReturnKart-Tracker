"""
RETURNKART.IN — ORDERS API ROUTES
Fixed for Gemini 2.5 Flash (thinking model): maxOutputTokens=8192, read last part.
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Optional
import traceback
import json
import re

from backend.services.supabase_service import (
    get_orders_by_user,
    update_order_status,
    get_expiring_soon,
)
from backend.services.gmail_service import sync_gmail_orders

router = APIRouter()


@router.get("")
async def list_orders(request: Request, status: Optional[str] = None):
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    orders = await get_orders_by_user(user_id, status=status)
    return {"orders": orders, "count": len(orders)}


@router.get("/urgent")
async def urgent_orders(request: Request, days: int = 3):
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    orders = await get_expiring_soon(user_id, days=days)
    return {"orders": orders, "count": len(orders)}


@router.patch("/{order_id}")
async def patch_order(order_id: str, request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    status = body.get("status")
    if not user_id or not status:
        raise HTTPException(status_code=400, detail="user_id and status are required")
    if status not in ("kept", "returned", "active", "expired"):
        raise HTTPException(status_code=400, detail="Invalid status value")
    updated = await update_order_status(order_id, user_id, status)
    return {"order": updated}


@router.post("/sync")
async def trigger_sync(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    background_tasks.add_task(sync_gmail_orders, user_id)
    return {"status": "sync_started", "message": "Gmail sync running in background"}


@router.post("/debug-sync")
async def debug_sync(request: Request):
    """Runs Gmail sync SYNCHRONOUSLY with full debug output."""
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    debug = {}
    from backend.services.supabase_service import get_gmail_token
    from backend.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GEMINI_API_KEY

    debug["google_client_id_set"] = bool(GOOGLE_CLIENT_ID and len(GOOGLE_CLIENT_ID) > 10)
    debug["google_client_secret_set"] = bool(GOOGLE_CLIENT_SECRET and len(GOOGLE_CLIENT_SECRET) > 5)
    debug["gemini_key_set"] = bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 5)

    token_row = await get_gmail_token(user_id)
    if not token_row:
        return {"success": False, "message": "Gmail not connected", "debug": debug}

    debug["gmail_token"] = "FOUND"
    debug["has_refresh_token"] = bool(token_row.get("refresh_token"))

    try:
        result = await sync_gmail_orders(user_id)
        return {"success": True, "sync_result": result, "debug": debug}
    except Exception as e:
        debug["sync_error"] = str(e)
        debug["sync_traceback"] = traceback.format_exc()[:500]
        return {"success": False, "message": f"Sync crashed: {e}", "debug": debug}


@router.post("/test-parse")
async def test_parse_email(request: Request):
    """
    Test Gemini parser directly. Fixed for 2.5 Flash thinking model:
    - maxOutputTokens=8192 (thinking uses tokens internally)
    - Reads LAST part from response (thinking models output thinking + text)
    """
    import requests as http_requests
    from backend.config import GEMINI_API_KEY

    body = await request.json()
    email_text = body.get("email_text", "")
    platform = body.get("platform", "unknown")

    if not email_text:
        raise HTTPException(status_code=400, detail="email_text is required")

    debug = {}
    debug["gemini_key_set"] = bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 5)
    debug["gemini_key_prefix"] = GEMINI_API_KEY[:10] + "..." if GEMINI_API_KEY else "EMPTY"

    if not GEMINI_API_KEY:
        return {"success": False, "extracted": None, "message": "GEMINI_API_KEY not set!", "debug": debug}

    prompt = f"""You are an AI for ReturnKart.in, an Indian e-commerce return tracker.
Extract order info from this email. Return ONLY valid JSON, nothing else.

JSON format:
{{"order_id": "string or null", "brand": "string or null", "item_name": "string or null", "total_amount": number or null, "currency": "INR", "order_date": "YYYY-MM-DD or null", "category": "Fashion & Apparel|Electronics|Home & Kitchen|Default or null", "courier_partner": "string or null", "delivery_pincode": "string or null", "confidence": 0.0 to 1.0}}

Rules: order_date=YYYY-MM-DD, total_amount=number only, null for missing, confidence 1.0=sure 0.5=guess.

Email:
{email_text}

JSON:"""

    debug["prompt_length"] = len(prompt)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    debug["model"] = "gemini-2.5-flash"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
    }

    try:
        response = http_requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        debug["gemini_status"] = response.status_code
        debug["gemini_response_length"] = len(response.text)

        if response.status_code != 200:
            debug["gemini_error"] = response.text[:500]
            return {"success": False, "extracted": None, "message": f"Gemini API returned {response.status_code}", "debug": debug}

        data = response.json()
        candidates = data.get("candidates", [])
        debug["candidates_count"] = len(candidates)

        if not candidates:
            return {"success": False, "extracted": None, "message": "No candidates", "debug": debug}

        # Gemini 2.5 Flash returns multiple parts: thinking + text
        # Find the part containing JSON (usually the last one)
        parts = candidates[0].get("content", {}).get("parts", [])
        debug["parts_count"] = len(parts)

        raw = None
        for part in reversed(parts):
            text = part.get("text", "").strip()
            if text:
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
                if text.startswith("{") and "}" in text:
                    raw = text
                    break

        if not raw:
            # Fallback: just get any text
            for part in parts:
                text = part.get("text", "").strip()
                if text:
                    raw = re.sub(r"^```(?:json)?\s*", "", text)
                    raw = re.sub(r"\s*```$", "", raw)
                    break

        debug["raw_output"] = (raw or "")[:500]

        if not raw:
            return {"success": False, "extracted": None, "message": "No text in response", "debug": debug}

        parsed = json.loads(raw)
        debug["parsed_ok"] = True
        return {"success": True, "extracted": parsed, "platform_hint": platform, "debug": debug}

    except json.JSONDecodeError as e:
        debug["json_error"] = str(e)
        return {"success": False, "extracted": None, "message": f"JSON parse failed: {e}", "debug": debug}
    except Exception as e:
        debug["exception"] = str(e)
        return {"success": False, "extracted": None, "message": f"Error: {e}", "debug": debug}
