"""
RETURNKART.IN — SMS API ROUTES

Called exclusively by the ReturnKart Android app.
iOS cannot access SMS — iOS users should use the WhatsApp
Business API channel to forward order messages instead.

Endpoints:

  POST /api/sms/ingest
    Main endpoint. Android app sends a batch of SMS messages.
    Supports both:
      - BULK scan: first-time connect, sends last 90 days of inbox
      - LIVE scan: single new SMS as it arrives via BroadcastReceiver

  GET /api/sms/status/{user_id}
    Returns whether SMS is connected + last sync timestamp.
    Used by the Settings Vault screen.

Android app integration notes:
  1. Request READ_SMS permission on first launch
  2. On grant: call POST /api/sms/ingest with last 90 days of SMS
  3. Optionally: register SMS_RECEIVED BroadcastReceiver for live ingestion
  4. Each message object: { sender, text, received_at (epoch ms) }
  5. Max batch size: 500 messages per call (split larger batches)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.services.sms_service import process_sms_batch, is_ecommerce_sms
from backend.services.supabase_service import get_client

router = APIRouter()

IST = timezone(timedelta(hours=5, minutes=30))


# ─────────────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────────────

class SmsMessage(BaseModel):
    sender: str                        # Sender ID e.g. "FLPKRT", "AZ-AMAZON"
    text: str                          # Full SMS body
    received_at: Optional[int] = None  # Unix epoch milliseconds from Android


class SmsIngestRequest(BaseModel):
    user_id: str
    messages: list[SmsMessage]
    scan_type: str = "bulk"            # "bulk" (first time) or "live" (new SMS)


# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post("/ingest")
async def ingest_sms(
    payload: SmsIngestRequest,
    background_tasks: BackgroundTasks,
):
    """
    POST /api/sms/ingest

    Android app sends SMS messages here after READ_SMS scan.

    For BULK scans (first connect): runs in background so the
    app gets an instant response and doesn't time out.

    For LIVE scans (new SMS arrival): also background, returns
    immediately so the Android BroadcastReceiver isn't blocked.

    The app should:
      1. Filter to only WhatsApp/SMS messages (not already done here
         in case the app pre-filters)
      2. Send in batches of max 500 messages
      3. Include received_at so we can deduplicate across syncs
    """
    if not payload.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not payload.messages:
        return {"status": "ok", "message": "No messages to process"}
    if len(payload.messages) > 500:
        raise HTTPException(
            status_code=400,
            detail="Max 500 messages per request. Split into smaller batches."
        )

    # Convert Pydantic models to plain dicts for the service
    messages_dicts = [
        {
            "sender": m.sender,
            "text": m.text,
            "received_at": (
                datetime.fromtimestamp(m.received_at / 1000, tz=IST).isoformat()
                if m.received_at else None
            ),
        }
        for m in payload.messages
    ]

    # Always run in background — instant response to Android app
    background_tasks.add_task(
        process_sms_batch,
        messages=messages_dicts,
        user_id=payload.user_id,
    )

    return {
        "status": "queued",
        "scan_type": payload.scan_type,
        "queued_count": len(payload.messages),
        "message": f"{len(payload.messages)} SMS queued for processing.",
    }


@router.get("/status/{user_id}")
async def sms_status(user_id: str):
    """
    GET /api/sms/status/{user_id}

    Returns SMS connection status for the Settings Vault screen.
    We infer "connected" if the user has any SMS-sourced orders.
    """
    client = get_client()
    result = (
        client.table("orders")
        .select("id, created_at")
        .eq("user_id", user_id)
        .eq("source", "sms")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if result.data:
        last_sync = result.data[0]["created_at"]
        sms_order_count = (
            client.table("orders")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("source", "sms")
            .execute()
            .count
        )
        return {
            "connected": True,
            "last_synced_at": last_sync,
            "sms_orders_found": sms_order_count,
        }

    return {
        "connected": False,
        "last_synced_at": None,
        "sms_orders_found": 0,
        "message": "No SMS orders found. Open the Android app and grant READ_SMS permission to scan.",
    }
