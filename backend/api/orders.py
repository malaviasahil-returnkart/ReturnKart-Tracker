"""
RETURNKART.IN — ORDERS API ROUTES
Includes test-parse with direct Gemini API debugging.
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


@router.post("/test-parse")
async def test_parse_email(request: Request):
    """
    POST /api/orders/test-parse
    Test the Gemini email parser with FULL debug output.
    Calls Gemini REST API directly and shows every step.
    """
    import requests as http_requests
    from backend.config import GEMINI_API_KEY

    body = await request.json()
    email_text = body.get("email_text", "")
    platform = body.get("platform", "unknown")

    if not email_text:
        raise HTTPException(status_code=400, detail="email_text is required")

    debug = {}

    # Step 1: Check API key
    debug["gemini_key_set"] = bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 5)
    debug["gemini_key_prefix"] = GEMINI_API_KEY[:10] + "..." if GEMINI_API_KEY else "EMPTY"

    if not GEMINI_API_KEY:
        return {
            "success": False,
            "extracted": None,
            "message": "GEMINI_API_KEY is not set in deployment secrets!",
            "debug": debug,
        }

    # Step 2: Build prompt
    prompt = f"""You are an AI assistant for ReturnKart.in, an Indian e-commerce return tracker.
Extract structured order information from the email below.
Return ONLY valid JSON. No markdown, no explanation, no code fences.

Extract this JSON:
{{
  "order_id": "platform order ID or null",
  "brand": "brand name or null",
  "item_name": "product name or null",
  "total_amount": number or null,
  "currency": "INR",
  "order_date": "YYYY-MM-DD or null",
  "category": "Fashion & Apparel | Electronics | Home & Kitchen | Default or null",
  "courier_partner": "courier name or null",
  "delivery_pincode": "6-digit pincode or null",
  "confidence": 0.0 to 1.0
}}

Rules:
- order_date in YYYY-MM-DD format
- total_amount as number (no currency symbols)
- null for missing fields
- confidence: 1.0 = certain, 0.5 = guessing

Email:
{email_text}

JSON:"""

    debug["prompt_length"] = len(prompt)

    # Step 3: Call Gemini REST API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}
    }

    try:
        response = http_requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        debug["gemini_status"] = response.status_code
        debug["gemini_response_length"] = len(response.text)

        if response.status_code != 200:
            debug["gemini_error"] = response.text[:500]
            return {
                "success": False,
                "extracted": None,
                "message": f"Gemini API returned {response.status_code}",
                "debug": debug,
            }

        data = response.json()
        candidates = data.get("candidates", [])
        debug["candidates_count"] = len(candidates)

        if not candidates:
            debug["full_response"] = json.dumps(data)[:500]
            return {
                "success": False,
                "extracted": None,
                "message": "Gemini returned no candidates",
                "debug": debug,
            }

        raw = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        debug["raw_gemini_output"] = raw[:500]

        # Strip markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        debug["parsed_ok"] = True

        return {
            "success": True,
            "extracted": parsed,
            "platform_hint": platform,
            "debug": debug,
        }

    except json.JSONDecodeError as e:
        debug["json_error"] = str(e)
        debug["raw_text"] = raw[:300] if 'raw' in dir() else "N/A"
        return {"success": False, "extracted": None, "message": f"JSON parse failed: {e}", "debug": debug}
    except Exception as e:
        debug["exception"] = str(e)
        debug["traceback"] = traceback.format_exc()[:500]
        return {"success": False, "extracted": None, "message": f"Error: {e}", "debug": debug}
