"""
RETURNKART.IN — GMAIL SERVICE
Task #13: Fetch invoice emails from Gmail and extract order data.

Flow:
  1. Load user's Gmail token from Supabase
  2. Refresh token if expired
  3. Search Gmail for invoice/shipping emails from known platforms
  4. For each email: call Gemini to extract order data
  5. Save extracted orders to Supabase (upsert — no duplicates)
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

# Gmail search queries per platform — BROAD queries to catch all order-related emails
# Each query searches multiple sender addresses and subjects
PLATFORM_QUERIES = {
    "amazon": '(from:amazon.in OR from:amazon.com) (subject:"your order" OR subject:"shipped" OR subject:"delivered" OR subject:"order confirmation" OR subject:"out for delivery" OR subject:"arriving" OR subject:"refund")',
    "flipkart": '(from:flipkart.com) (subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"arriving" OR subject:"refund" OR subject:"placed")',
    "myntra": '(from:myntra.com) (subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed" OR subject:"refund")',
    "meesho": '(from:meesho.com) (subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed")',
    "ajio": '(from:ajio.com) (subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed")',
    "nykaa": '(from:nykaa.com) (subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed")',
    "tatacliq": '(from:tatacliq.com OR from:tataneu.com) (subject:"order" OR subject:"shipped" OR subject:"delivered")',
    "jiomart": '(from:jiomart.com OR from:reliance) (subject:"order" OR subject:"shipped" OR subject:"delivered")',
    "snapdeal": '(from:snapdeal.com) (subject:"order" OR subject:"shipped" OR subject:"delivered")',
    "croma": '(from:croma.com) (subject:"order" OR subject:"shipped" OR subject:"delivered")',
}

# Catch-all query for any ecommerce order email not from known platforms
CATCH_ALL_QUERY = '(subject:"order confirmed" OR subject:"order placed" OR subject:"your order" OR subject:"order shipped" OR subject:"has been shipped" OR subject:"out for delivery" OR subject:"has been delivered") newer_than:30d'


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
    """Extract text body from a Gmail message payload. Tries plain text first, then HTML."""
    body = ""

    # Direct body
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        if body.strip():
            return body[:10000]

    # Multipart — search recursively
    parts = payload.get("parts", [])
    plain_text = ""
    html_text = ""

    for part in parts:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data", "")

        if mime == "text/plain" and data:
            plain_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime == "text/html" and data:
            html_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime.startswith("multipart/") and part.get("parts"):
            # Recurse into nested multipart
            nested = _decode_email_body(part)
            if nested:
                plain_text = plain_text or nested

    body = plain_text or html_text
    return body[:10000]  # Increase limit for more context


def _get_header(headers: list, name: str) -> str:
    """Extract a specific header value from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _detect_platform(sender: str, subject: str) -> str:
    """Auto-detect platform from sender/subject when using catch-all query."""
    sender_lower = sender.lower()
    subject_lower = subject.lower()

    platform_hints = {
        "amazon": ["amazon"],
        "flipkart": ["flipkart", "ekart"],
        "myntra": ["myntra"],
        "meesho": ["meesho"],
        "ajio": ["ajio"],
        "nykaa": ["nykaa"],
        "tatacliq": ["tatacliq", "tataneu", "tata cliq"],
        "jiomart": ["jiomart", "reliance"],
        "snapdeal": ["snapdeal"],
        "croma": ["croma"],
        "swiggy": ["swiggy"],
        "zomato": ["zomato"],
        "bigbasket": ["bigbasket"],
        "lenskart": ["lenskart"],
        "boat": ["boat-lifestyle", "boatlifestyle"],
        "pepperfry": ["pepperfry"],
        "urbanladder": ["urbanladder"],
    }

    for platform, hints in platform_hints.items():
        for hint in hints:
            if hint in sender_lower or hint in subject_lower:
                return platform

    return "unknown"


async def sync_gmail_orders(user_id: str, max_emails: int = 100) -> dict:
    """
    Main sync function. Called when user triggers 'Sync Gmail' in the app.
    Returns a summary: { synced: N, new_orders: N, errors: N, details: [] }
    """
    from backend.services.gemini_service import extract_order_from_email

    token_row = await get_gmail_token(user_id)
    if not token_row:
        return {"error": "Gmail not connected", "synced": 0, "new_orders": 0}

    creds = await _refresh_if_needed(user_id, token_row)
    service = build("gmail", "v1", credentials=creds)

    synced = 0
    new_orders = 0
    errors = 0
    details = []
    seen_message_ids = set()

    # Search known platforms + catch-all
    all_queries = {**PLATFORM_QUERIES, "catch_all": CATCH_ALL_QUERY}

    for platform, query in all_queries.items():
        try:
            # Add time filter — only look at last 90 days
            time_query = f"({query}) newer_than:90d"

            results = (
                service.users()
                .messages()
                .list(userId="me", q=time_query, maxResults=15)
                .execute()
            )
            messages = results.get("messages", [])
            details.append(f"{platform}: {len(messages)} emails found")

            for msg_ref in messages:
                if msg_ref["id"] in seen_message_ids:
                    continue
                seen_message_ids.add(msg_ref["id"])

                try:
                    msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_ref["id"], format="full")
                        .execute()
                    )

                    headers = msg.get("payload", {}).get("headers", [])
                    subject = _get_header(headers, "subject")
                    sender = _get_header(headers, "from")
                    date_str = _get_header(headers, "date")
                    body = _decode_email_body(msg.get("payload", {}))

                    if not body or len(body) < 50:
                        continue  # Skip empty or too-short emails

                    # Detect platform for catch-all query
                    actual_platform = platform if platform != "catch_all" else _detect_platform(sender, subject)

                    email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"

                    # Ask Gemini to extract order data
                    extracted = await extract_order_from_email(email_text, actual_platform)

                    if extracted and extracted.order_id and extracted.confidence and extracted.confidence >= 0.5:
                        order = OrderCreate(
                            user_id=user_id,
                            order_id=extracted.order_id,
                            brand=extracted.brand or actual_platform.title(),
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
                        details.append(f"  ✓ {extracted.brand}: {extracted.item_name} ({extracted.order_id})")

                    synced += 1

                except Exception as e:
                    print(f"Error processing email {msg_ref['id']}: {e}")
                    errors += 1

        except Exception as e:
            print(f"Error fetching {platform} emails: {e}")
            errors += 1

    return {"synced": synced, "new_orders": new_orders, "errors": errors, "details": details}
