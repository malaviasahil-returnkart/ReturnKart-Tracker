"""
RETURNKART.IN — WHATSAPP API ROUTES

Two ingestion channels:

  CHANNEL 1 — Android Notification Listener
  POST /api/whatsapp/notification
  Called by the ReturnKart Android app's NotificationListenerService.
  Receives notification text captured from the device notification tray.
  Works automatically, zero user effort.

  CHANNEL 2 — Meta WhatsApp Business API
  GET  /api/whatsapp/webhook  → Meta verification handshake (run once on setup)
  POST /api/whatsapp/webhook  → Incoming messages from Meta Cloud API
  iOS users forward their ecommerce WhatsApp messages to ReturnKart's
  WhatsApp Business number. Meta sends those to this webhook.

Both channels call whatsapp_service.extract_order_from_whatsapp().
"""
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Optional

from backend.config import WHATSAPP_VERIFY_TOKEN, WHATSAPP_APP_SECRET
from backend.services.whatsapp_service import (
    extract_order_from_whatsapp,
    is_ecommerce_notification,
)

router = APIRouter()


# ─────────────────────────────────────────────
# CHANNEL 1: Android Notification Listener
# ─────────────────────────────────────────────

class NotificationPayload(BaseModel):
    user_id: str
    notification_text: str          # Full notification text from Android
    sender_name: str = "unknown"    # App/sender name (e.g. "Amazon", "+91 80690...")
    app_package: str = ""           # e.g. "com.whatsapp" or "com.whatsapp.w4b"
    timestamp_ms: Optional[int] = None


@router.post("/notification")
async def ingest_notification(
    payload: NotificationPayload,
    background_tasks: BackgroundTasks,
):
    """
    POST /api/whatsapp/notification

    Called by the Android NotificationListenerService every time
    a WhatsApp notification arrives on the user's device.

    Flow:
      1. Filter — is this actually an ecommerce message?
      2. Extract order data via Gemini (background task so response is instant)
      3. Upsert to Supabase
    """
    # Quick filter before doing any AI work
    if not is_ecommerce_notification(payload.sender_name, payload.notification_text):
        return {"status": "skipped", "reason": "not_ecommerce"}

    # Run extraction in background — Android app gets instant 202
    background_tasks.add_task(
        extract_order_from_whatsapp,
        message_text=payload.notification_text,
        user_id=payload.user_id,
        sender=payload.sender_name,
        source_channel="whatsapp_notification",
    )
    return {"status": "queued", "message": "Notification queued for extraction"}


# ─────────────────────────────────────────────
# CHANNEL 2: Meta WhatsApp Business API
# ─────────────────────────────────────────────

@router.get("/webhook")
async def meta_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    GET /api/whatsapp/webhook

    Meta calls this ONCE when you register the webhook URL in
    Meta Developer Console. It verifies you control the server.

    Setup step:
      1. Go to Meta for Developers → Your App → WhatsApp → Configuration
      2. Webhook URL: https://return-kart-tracker.replit.app/api/whatsapp/webhook
      3. Verify token: whatever you set as WHATSAPP_VERIFY_TOKEN in Replit Secrets
      4. Click Verify — this endpoint responds and you're done.
    """
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        print("[WhatsApp] Meta webhook verified successfully")
        return int(hub_challenge)  # Must return the challenge as plain int
    raise HTTPException(status_code=403, detail="Webhook verification failed — check WHATSAPP_VERIFY_TOKEN")


@router.post("/webhook")
async def meta_webhook_receive(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    POST /api/whatsapp/webhook

    Meta sends this every time a message arrives at ReturnKart's
    WhatsApp Business number.

    iOS user flow:
      User receives Amazon/Flipkart WhatsApp message
      → Taps message → Share/Forward → ReturnKart's WhatsApp number
      → Meta sends it here → Gemini parses → Supabase upsert

    Security: validates X-Hub-Signature-256 header using WHATSAPP_APP_SECRET.
    """
    body_bytes = await request.body()

    # Validate signature from Meta (prevents fake webhook calls)
    if WHATSAPP_APP_SECRET:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            WHATSAPP_APP_SECRET.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Meta wraps messages in a nested structure — dig in
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])

                # Map sender phone → display name
                contact_map = {
                    c["wa_id"]: c.get("profile", {}).get("name", c["wa_id"])
                    for c in contacts
                }

                for msg in messages:
                    msg_type = msg.get("type")
                    if msg_type != "text":
                        continue  # Skip image/audio/etc for now

                    text = msg.get("text", {}).get("body", "")
                    sender_phone = msg.get("from", "unknown")
                    sender_name = contact_map.get(sender_phone, sender_phone)

                    # We need to resolve user_id from their phone number
                    # For now tag with sender phone — later join against users table
                    user_id = f"wa_{sender_phone}"  # TODO: resolve to Supabase user_id

                    if text:
                        background_tasks.add_task(
                            extract_order_from_whatsapp,
                            message_text=text,
                            user_id=user_id,
                            sender=sender_name,
                            source_channel="whatsapp_business_api",
                        )
    except Exception as e:
        print(f"[WhatsApp webhook] Parse error: {e}")
        # Always return 200 to Meta — otherwise they retry forever

    # Meta requires 200 OK within 20 seconds or it retries
    return {"status": "ok"}
