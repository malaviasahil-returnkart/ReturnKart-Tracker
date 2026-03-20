"""
RETURNKART.IN — ORDERS API ROUTES
Task #15: HTTP endpoints for order management.
Includes test-parse endpoint for testing email parsing without Gmail.
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Optional

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
    Test the Gemini email parser WITHOUT Gmail.
    Send raw email text and see what Gemini extracts.

    Body: { "email_text": "Subject: ...\nFrom: ...\n\n<email body>", "platform": "amazon" }
    
    Returns: raw Gemini extraction result (order_id, brand, item_name, price, etc.)
    """
    from backend.services.gemini_service import extract_order_from_email

    body = await request.json()
    email_text = body.get("email_text", "")
    platform = body.get("platform", "unknown")

    if not email_text:
        raise HTTPException(status_code=400, detail="email_text is required")

    extracted = await extract_order_from_email(email_text, platform)

    if extracted:
        return {
            "success": True,
            "extracted": {
                "order_id": extracted.order_id,
                "brand": extracted.brand,
                "item_name": extracted.item_name,
                "total_amount": extracted.total_amount,
                "currency": extracted.currency,
                "order_date": extracted.order_date,
                "category": extracted.category,
                "courier_partner": extracted.courier_partner,
                "delivery_pincode": extracted.delivery_pincode,
                "confidence": extracted.confidence,
            },
            "platform_hint": platform,
        }
    else:
        return {
            "success": False,
            "extracted": None,
            "message": "Gemini could not extract order data from this email.",
            "platform_hint": platform,
        }
