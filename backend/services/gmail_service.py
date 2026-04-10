"""
RETURNKART.IN — GMAIL SERVICE (v2)

Universal query, sequential fetch, Python deadline calc.
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
from backend.services.return_calculator import calculate_return_deadline
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))

def _build_gmail_query(days: int = 30) -> str:
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    return (
        f'after:{cutoff} ('
        'category:purchases OR category:updates OR '
        'subject:"order confirmation" OR subject:"order confirmed" OR '
        'subject:"has been delivered" OR subject:"out for delivery" OR '
        'subject:"payment successful" OR subject:"shipped"'
        ')'
    )

GMAIL_QUERY = _build_gmail_query(30)

# Backward compat for orders.py import
PLATFORM_QUERIES = {"universal": GMAIL_QUERY}

GEMINI_CONCURRENCY = 3


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
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: creds.refresh(GoogleRequest()))
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
            mime = part.get("mimeType", "")
            data = part.get("body", {}).get("data")
            if not data:
                for subpart in part.get("parts", []):
                    sub_data = subpart.get("body", {}).get("data")
                    if sub_data and subpart.get("mimeType") in ("text/plain", "text/html"):
                        body = base64.urlsafe_b64decode(sub_data).decode("utf-8", errors="ignore")
                        if subpart["mimeType"] == "text/plain":
                            return body[:8000]
                continue
            if mime == "text/plain":
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")[:8000]
            elif mime == "text/html":
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return body[:8000]


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _guess_brand(sender: str, subject: str) -> str:
    text = (sender + " " + subject).lower()
    brands = {
        "amazon": "amazon", "flipkart": "flipkart", "myntra": "myntra",
        "meesho": "meesho", "ajio": "ajio", "nykaa": "nykaa",
        "jiomart": "jiomart", "tatacliq": "tatacliq", "snapdeal": "snapdeal",
        "croma": "croma", "temu": "temu", "swiggy": "swiggy",
        "zomato": "zomato", "blinkit": "blinkit", "bigbasket": "bigbasket",
        "h&m": "hm", "hm.com": "hm", "zara": "zara", "uniqlo": "uniqlo",
        "levi": "levis", "nike": "nike", "adidas": "adidas", "puma": "puma",
        "zepto": "zepto", "dunzo": "dunzo", "uber": "uber", "ola": "ola",
        "rapido": "rapido", "eventbrite": "eventbrite", "bookmyshow": "bookmyshow",
    }
    for keyword, slug in brands.items():
        if keyword in text:
            return slug
    return "unknown"


async def _process_one_email(
    service,
    msg_id: str,
    user_id: str,
) -> Optional[OrderCreate]:
    from backend.services.gemini_service import extract_order_from_email

    try:
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(
            None,
            lambda mid=msg_id: service.users().messages().get(
                userId="me", id=mid, format="full"
            ).execute()
        )
        if not msg:
            return None

        headers = msg.get("payload", {}).get("headers", [])
        subject = _get_header(headers, "subject")
        sender = _get_header(headers, "from")
        date_str = _get_header(headers, "date")
        body = _decode_email_body(msg.get("payload", {}))

        email_received_date = parse_email_header_date(date_str)
        brand_slug = _guess_brand(sender, subject)

        email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"

        # Block non-ecommerce brands at Python level
        BLOCKED_BRANDS = {
            "swiggy", "zomato", "blinkit", "zepto", "bigbasket", "dunzo",
            "uber", "ola", "rapido", "eventbrite", "bookmyshow", "paytm",
            "gpay", "phonepe", "netflix", "spotify", "hotstar", "youtube",
            "airtel", "jio", "vi", "bsnl",
        }
        if brand_slug in BLOCKED_BRANDS:
            print(f"[Gmail] Blocked non-ecommerce brand: {brand_slug}")
            return None

        BLOCKED_BRANDS = {
            "swiggy", "zomato", "blinkit", "zepto", "bigbasket", "dunzo",
            "uber", "ola", "rapido", "eventbrite", "bookmyshow", "paytm",
            "gpay", "phonepe", "netflix", "spotify", "hotstar", "youtube",
            "airtel", "jio", "vi", "bsnl",
        }
        if brand_slug in BLOCKED_BRANDS:
            print(f"[Gmail] Blocked non-ecommerce brand: {brand_slug}")
            return None

        extracted = await extract_order_from_email(email_text, brand_slug)

        if extracted and extracted.order_id:
            extracted_brand_lower = (extracted.brand or "").lower()
            if any(b in extracted_brand_lower for b in BLOCKED_BRANDS):
                print(f"[Gmail] Blocked non-ecommerce brand from Gemini: {extracted.brand}")
                return None
            # Also block if Gemini returned a blocked brand
            extracted_brand_lower = (extracted.brand or "").lower()
            if any(b in extracted_brand_lower for b in BLOCKED_BRANDS):
                print(f"[Gmail] Blocked non-ecommerce brand from Gemini: {extracted.brand}")
                return None
            order_date = resolve_order_date(
                gemini_date=extracted.order_date,
                fallback_date=email_received_date,
                context=f"{brand_slug} {extracted.order_id}",
            )

            brand_for_calc = (extracted.brand or brand_slug).lower().replace(" ", "")
            brand_map = {
                "amazonindia": "amazon", "amazon.in": "amazon",
                "amazon": "amazon", "flipkart": "flipkart",
                "myntra": "myntra", "meesho": "meesho",
                "ajio": "ajio", "nykaa": "nykaa", "temu": "temu",
            }
            calc_slug = brand_map.get(brand_for_calc, brand_slug)
            return_deadline = calculate_return_deadline(order_date, calc_slug)

            return OrderCreate(
                user_id=user_id,
                order_id=extracted.order_id,
                brand=extracted.brand or brand_slug.title(),
                item_name=extracted.item_name or "Unknown item",
                price=extracted.total_amount or 0.0,
                order_date=order_date,
                return_deadline=return_deadline,
                category=extracted.category,
                courier_partner=extracted.courier_partner,
                delivery_pincode=extracted.delivery_pincode,
                purpose_id="return_tracking",
                consent_timestamp=datetime.now(IST),
                source="gmail",
            )
    except Exception as e:
        print(f"[Gmail] Error processing email {msg_id}: {e}")
    return None


async def _sync_single_account(
    user_id: str,
    token_row: dict,
    max_emails: int = 500,
) -> dict:
    account_email = token_row.get("user_email", "unknown")

    try:
        creds = await _refresh_if_needed(user_id, token_row)
        loop = asyncio.get_event_loop()
        service = await loop.run_in_executor(
            None, lambda: build("gmail", "v1", credentials=creds)
        )

        try:
            results = await loop.run_in_executor(
                None,
                lambda: service.users().messages().list(
                    userId="me", q=GMAIL_QUERY, maxResults=max_emails
                ).execute()
            )
            msg_ids = [m["id"] for m in results.get("messages", [])]
        except Exception as e:
            print(f"[Gmail:{account_email}] Query error: {e}")
            return {"account": account_email, "synced": 0, "new_orders": 0, "errors": 1, "error_detail": str(e)}

        if not msg_ids:
            return {"account": account_email, "synced": 0, "new_orders": 0, "errors": 0, "detail": "No emails matched"}

        print(f"[Gmail:{account_email}] Found {len(msg_ids)} emails to process")

        # Sequential processing
        results_list = []
        for msg_id in msg_ids:
            result = await _process_one_email(service, msg_id, user_id)
            results_list.append(result)

        orders = [r for r in results_list if r is not None]
        errors = sum(1 for r in results_list if r is None)

        new_orders = 0
        if orders:
            new_orders = await bulk_upsert_orders(orders)

        return {
            "account": account_email,
            "synced": len(msg_ids),
            "extracted": len(orders),
            "new_orders": new_orders,
            "errors": errors,
        }

    except Exception as e:
        print(f"[Gmail:{account_email}] Sync failed: {e}")
        return {"account": account_email, "synced": 0, "new_orders": 0, "errors": 1, "error_detail": str(e)}


async def sync_gmail_orders(user_id: str, max_emails: int = 500) -> dict:
    all_tokens = await get_all_gmail_tokens(user_id)
    if not all_tokens:
        return {"error": "No Gmail accounts connected", "synced": 0, "new_orders": 0}

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
        "per_account": account_results,
    }
