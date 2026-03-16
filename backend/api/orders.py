"""
RETURNKART.IN — ORDERS API ROUTES
Task #15: HTTP endpoints for order management.
All business logic lives in supabase_service. These are thin wrappers.
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
    """
    GET /api/orders
    Returns all orders for the authenticated user.
    Optional ?status=active|kept|returned|expired filter.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    orders = await get_orders_by_user(user_id, status=status)
    return {"orders": orders, "count": len(orders)}


@router.get("/urgent")
async def urgent_orders(request: Request, days: int = 3):
    """
    GET /api/orders/urgent
    Returns orders expiring within N days. Used for the dashboard carousel.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    orders = await get_expiring_soon(user_id, days=days)
    return {"orders": orders, "count": len(orders)}


@router.patch("/{order_id}")
async def patch_order(order_id: str, request: Request):
    """
    PATCH /api/orders/{order_id}
    Update order status. Body: { "user_id": "...", "status": "kept|returned" }
    """
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
    """
    POST /api/orders/sync
    Triggers Gmail sync in the background.
    Returns immediately so the UI doesn't block.
    """
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    background_tasks.add_task(sync_gmail_orders, user_id)
    return {"status": "sync_started", "message": "Gmail sync running in background"}
