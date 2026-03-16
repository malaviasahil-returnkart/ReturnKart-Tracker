"""
RETURNKART.IN — GMAIL SERVICE
Task #13: Fetch invoice emails from Gmail and extract order data.

Flow:
  1. Load user's Gmail token from Supabase
  2. Refresh token if expired
  3. Search Gmail for invoice emails from known platforms
  4. For each email: call Gemini to extract order data
  5. Save extracted orders to Supabase (upsert — no duplicates)

This is the ORCHESTRATOR — it calls gemini_service and supabase_service.
"""
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

from backend.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from backend.services.supabase_service import (
    get_gmail_token,
    save_gmail_token,
    upsert_order,
)
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))

# Gmail search queries per platform
PLATFORM_QUERIES = {
    "amazon":   "from:(auto-confirm@amazon.in OR shipment-tracking@amazon.in) subject:(order)",
    "myntra":   "from:(noreply@myntra.com) subject:(order)",
    "flipkart": "from:(noreply@flipkart.com) subject:(order)",
    "meesho":   "from:(noreply@meesho.com) subject:(order)",
    "ajio":     "from:(noreply@ajio.com) subject:(order)",
}


def _build_credentials(token_row: dict) -> Credentials:
    """Build a Google Credentials object from a DB token row."""
    return Credentials(
        token=token_row["access_token"],
        refresh_token=token_row.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_row.get("scope", "").split(),
    )


async def _refresh_if_needed(user_id: str, token_row: dict) -> Credentials:
    """Refresh expired credentials and save updated token back to DB."""
    creds = _build_credentials(token_row)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await save_gmail_token(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry,
            scope=" ".join(creds.scopes) if creds.scopes else "",
        )
    return creds


def _decode_email_body(payload: dict) -> str:
    """Extract plain text body from a Gmail message payload."""
    body = ""
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
            elif part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                # Fallback to HTML if no plain text
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
    return body[:8000]  # Trim to avoid Gemini token limits


def _get_header(headers: list, name: str) -> str:
    """Extract a specific header value from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


async def sync_gmail_orders(user_id: str, max_emails: int = 50) -> dict:
    """
    Main sync function. Called when user triggers 'Sync Gmail' in the app.
    Returns a summary: { synced: N, new_orders: N, errors: N }
    """
    # Lazy import to avoid circular dependency
    from backend.services.gemini_service import extract_order_from_email

    token_row = await get_gmail_token(user_id)
    if not token_row:
        return {"error": "Gmail not connected", "synced": 0, "new_orders": 0}

    creds = await _refresh_if_needed(user_id, token_row)
    service = build("gmail", "v1", credentials=creds)

    synced = 0
    new_orders = 0
    errors = 0

    for platform, query in PLATFORM_QUERIES.items():
        try:
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_emails // len(PLATFORM_QUERIES))
                .execute()
            )
            messages = results.get("messages", [])

            for msg_ref in messages:
                try:
                    msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_ref["id"], format="full")
                        .execute()
                    )

                    headers = msg.get("payload", {}).get("headers", [])
                    subject = _get_header(headers, "subject")
                    sender  = _get_header(headers, "from")
                    date_str = _get_header(headers, "date")
                    body = _decode_email_body(msg.get("payload", {}))

                    email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"

                    # Ask Gemini to extract order data
                    extracted = await extract_order_from_email(email_text, platform)

                    if extracted and extracted.order_id:
                        order = OrderCreate(
                            user_id=user_id,
                            order_id=extracted.order_id,
                            brand=extracted.brand or platform.title(),
                            item_name=extracted.item_name or "Unknown item",
                            price=extracted.total_amount or 0.0,
                            order_date=datetime.strptime(extracted.order_date, "%Y-%m-%d").date()
                                if extracted.order_date else datetime.now(IST).date(),
                            category=extracted.category,
                            courier_partner=extracted.courier_partner,
                            delivery_pincode=extracted.delivery_pincode,
                            purpose_id="return_tracking",
                            consent_timestamp=datetime.now(IST),
                        )
                        await upsert_order(order)
                        new_orders += 1

                    synced += 1

                except Exception as e:
                    print(f"Error processing email {msg_ref['id']}: {e}")
                    errors += 1

        except Exception as e:
            print(f"Error fetching {platform} emails: {e}")
            errors += 1

    return {"synced": synced, "new_orders": new_orders, "errors": errors}
