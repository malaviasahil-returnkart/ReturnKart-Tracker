"""
RETURNKART.IN — GMAIL SERVICE (MULTI-ACCOUNT)

Sync now iterates over ALL connected Gmail accounts for a user.
Each account is synced independently with its own credentials.
"""
import asyncio
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

from backend.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from backend.services.supabase_service import (
    get_all_gmail_tokens,
    save_gmail_token,
    bulk_upsert_orders,
)
from backend.services.date_utils import parse_email_header_date, resolve_order_date
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))

_ORDER_SUBJECTS = (
    "subject:(order OR ordered OR dispatch OR dispatched OR shipped OR "
    "delivery OR delivered OR return OR refund OR exchange OR replacement OR confirm)"
)

PLATFORM_QUERIES = {
    "amazon": (
        "from:(amazon.in OR @amazon.in OR auto-confirm@amazon.in OR "
        "shipment-tracking@amazon.in OR order-update@amazon.in OR "
        "returns@amazon.in OR refund@amazon.in OR "
        "no-reply@amazon.in OR donotreply@amazon.in) "
        + _ORDER_SUBJECTS
    ),
    "flipkart": (
        "from:(flipkart.com OR @flipkart.com OR noreply@flipkart.com OR "
        "no-reply@flipkart.com OR order@flipkart.com OR "
        "returns@flipkart.com OR track@flipkart.com) "
        + _ORDER_SUBJECTS
    ),
    "myntra": (
        "from:(myntra.com OR @myntra.com OR noreply@myntra.com OR "
        "no-reply@myntra.com OR returns@myntra.com) "
        + _ORDER_SUBJECTS
    ),
    "meesho": (
        "from:(meesho.com OR @meesho.com OR noreply@meesho.com OR "
        "no-reply@meesho.com OR support@meesho.com) "
        + _ORDER_SUBJECTS
    ),
    "ajio": (
        "from:(ajio.com OR @ajio.com OR noreply@ajio.com OR "
        "no-reply@ajio.com OR care@ajio.com) "
        + _ORDER_SUBJECTS
    ),
    "nykaa": (
        "from:(nykaa.com OR @nykaa.com OR noreply@nykaa.com OR "
        "no-reply@nykaa.com OR care@nykaa.com OR orders@nykaa.com) "
        + _ORDER_SUBJECTS
    ),
    "jiomart": (
        "from:(jiomart.com OR @jiomart.com OR noreply@jiomart.com OR "
        "care@jiomart.com) "
        + _ORDER_SUBJECTS
    ),
    "tatacliq": (
        "from:(tatacliq.com OR @tatacliq.com OR noreply@tatacliq.com OR "
        "care@tatacliq.com) "
        + _ORDER_SUBJECTS
    ),
    "snapdeal": (
        "from:(snapdeal.com OR @snapdeal.com OR noreply@snapdeal.com OR "
        "cs@snapdeal.com) "
        + _ORDER_SUBJECTS
    ),
    "croma": (
        "from:(croma.com OR @croma.com OR noreply@croma.com OR "
        "care@croma.com) "
        + _ORDER_SUBJECTS
    ),
}

GEMINI_CONCURRENCY = 5


def _build_credentials(token_row: dict) -> Credentials:
    return Credentials(
        token=token_row["access_token"],
        refresh_token=token_row.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_row.get("scope", "").split(),
    )


async def _refresh_if_needed(user_id: str, token_row: dict) -> Credentials:
    creds = _build_credentials(token_row)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await save_gmail_token(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry,
            scope=" ".join(creds.scopes) if creds.scopes else "",
            user_email=token_row.get("user_email"),
        )
    return creds


def _decode_email_body(payload: dict) -> str:
    body = ""
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
            elif part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
    return body[:8000]


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _fetch_email_sync(service, msg_id: str) -> dict:
    return (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )


async def _fetch_email_async(service, msg_id: str) -> Optional[dict]:
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _fetch_email_sync, service, msg_id)
    except Exception as e:
        print(f"[Gmail] Failed to fetch email {msg_id}: {e}")
        return None


async def _process_one_email(
    msg: dict,
    platform: str,
    user_id: str,
    semaphore: asyncio.Semaphore,
) -> Optional[OrderCreate]:
    from backend.services.gemini_service import extract_order_from_email

    async with semaphore:
        try:
            headers  = msg.get("payload", {}).get("headers", [])
            subject  = _get_header(headers, "subject")
            sender   = _get_header(headers, "from")
            date_str = _get_header(headers, "date")
            body     = _decode_email_body(msg.get("payload", {}))

            email_received_date = parse_email_header_date(date_str)
            email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"

            extracted = await extract_order_from_email(email_text, platform)

            if extracted and extracted.order_id:
                return OrderCreate(
                    user_id=user_id,
                    order_id=extracted.order_id,
                    brand=extracted.brand or platform.title(),
                    item_name=extracted.item_name or "Unknown item",
                    price=extracted.total_amount or 0.0,
                    order_date=resolve_order_date(
                        gemini_date=extracted.order_date,
                        fallback_date=email_received_date,
                        context=f"{platform} {extracted.order_id}",
                    ),
                    category=extracted.category,
                    courier_partner=extracted.courier_partner,
                    delivery_pincode=extracted.delivery_pincode,
                    purpose_id="return_tracking",
                    consent_timestamp=datetime.now(IST),
                    source="gmail",
                )
        except Exception as e:
            print(f"[Gmail] Error processing email for {platform}: {e}")
        return None


async def _sync_single_account(
    user_id: str,
    token_row: dict,
    max_emails: int = 100,
) -> dict:
    """Sync orders from ONE Gmail account."""
    account_email = token_row.get("user_email", "unknown")

    try:
        creds = await _refresh_if_needed(user_id, token_row)
        loop = asyncio.get_event_loop()
        service = await loop.run_in_executor(
            None, lambda: build("gmail", "v1", credentials=creds)
        )

        all_refs: list[tuple[str, str]] = []
        per_platform = max(1, max_emails // len(PLATFORM_QUERIES))

        for platform, query in PLATFORM_QUERIES.items():
            try:
                results = await loop.run_in_executor(
                    None,
                    lambda q=query: service.users().messages().list(
                        userId="me", q=q, maxResults=per_platform
                    ).execute()
                )
                for m in results.get("messages", []):
                    all_refs.append((m["id"], platform))
            except Exception as e:
                print(f"[Gmail:{account_email}] List error for {platform}: {e}")

        if not all_refs:
            return {"account": account_email, "synced": 0, "new_orders": 0, "errors": 0}

        seen_ids: set[str] = set()
        unique_refs = []
        for msg_id, platform in all_refs:
            if msg_id not in seen_ids:
                seen_ids.add(msg_id)
                unique_refs.append((msg_id, platform))

        # Fetch emails sequentially — Gmail API client is NOT thread-safe
        fetched_msgs = []
        for msg_id, _ in unique_refs:
            msg = await _fetch_email_async(service, msg_id)
            fetched_msgs.append(msg)

        msg_platform_pairs = [
            (msg, platform)
            for (msg, (_, platform)) in zip(fetched_msgs, unique_refs)
            if msg is not None
        ]

        semaphore = asyncio.Semaphore(GEMINI_CONCURRENCY)
        gemini_tasks = [
            _process_one_email(msg, platform, user_id, semaphore)
            for msg, platform in msg_platform_pairs
        ]
        results = await asyncio.gather(*gemini_tasks)

        orders = [r for r in results if r is not None]
        errors = len([r for r in results if r is None and r != 0])

        new_orders = 0
        if orders:
            new_orders = await bulk_upsert_orders(orders)

        return {
            "account": account_email,
            "synced": len(msg_platform_pairs),
            "new_orders": new_orders,
            "errors": max(0, errors),
        }

    except Exception as e:
        print(f"[Gmail:{account_email}] Sync failed: {e}")
        return {"account": account_email, "synced": 0, "new_orders": 0, "errors": 1, "error_detail": str(e)}


async def sync_gmail_orders(user_id: str, max_emails: int = 100) -> dict:
    """
    Sync orders from ALL connected Gmail accounts.
    """
    all_tokens = await get_all_gmail_tokens(user_id)
    if not all_tokens:
        return {"error": "No Gmail accounts connected", "synced": 0, "new_orders": 0}

    # Sync each account
    account_results = []
    total_synced = 0
    total_new = 0
    total_errors = 0

    for token_row in all_tokens:
        result = await _sync_single_account(user_id, token_row, max_emails)
        account_results.append(result)
        total_synced += result.get("synced", 0)
        total_new += result.get("new_orders", 0)
        total_errors += result.get("errors", 0)

    return {
        "synced": total_synced,
        "new_orders": total_new,
        "errors": total_errors,
        "accounts_synced": len(all_tokens),
        "platforms_searched": len(PLATFORM_QUERIES),
        "per_account": account_results,
    }
