"""
RETURNKART.IN — OUTLOOK / HOTMAIL SERVICE (Microsoft Graph API)

OAuth2 flow identical in structure to Gmail but uses Microsoft Identity Platform.
Covers: outlook.com, hotmail.com, live.com, and any Microsoft 365 account.

iOS and Android users can connect their Outlook account the same way they connect Gmail.

Setup (one-time, in Azure Portal):
  1. portal.azure.com → App Registrations → New registration
  2. Name: ReturnKart, Supported accounts: Personal Microsoft accounts
  3. Redirect URI: https://return-kart-tracker.replit.app/api/email/outlook/callback
  4. API Permissions: Microsoft Graph → Mail.Read, offline_access
  5. Certificates & secrets → New client secret → copy value
  6. Add to Replit Secrets: MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

import msal
import httpx

from backend.config import (
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    MICROSOFT_REDIRECT_URI,
)
from backend.services.supabase_service import save_email_token, get_email_token, upsert_order
from backend.models.order import OrderCreate
from backend.services.brand_validator import BLOCKED_BRANDS

IST = timezone(timedelta(hours=5, minutes=30))

SCOPES = ["Mail.Read", "offline_access"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# Ecommerce sender search queries for Microsoft Graph
# Graph API uses OData $filter — we search sender address contains known domains
PLATFORM_SENDERS = [
    "amazon.in",
    "flipkart.com",
    "myntra.com",
    "meesho.com",
    "ajio.com",
    "nykaa.com",
    "jiomart.com",
    "tatacliq.com",
]


def _get_msal_app() -> msal.ConfidentialClientApplication:
    """Build a new MSAL app instance (stateless — no token cache)."""
    return msal.ConfidentialClientApplication(
        client_id=MICROSOFT_CLIENT_ID,
        client_credential=MICROSOFT_CLIENT_SECRET,
        authority="https://login.microsoftonline.com/consumers",
    )


def get_auth_url(state: str) -> str:
    """
    Step 1: Build the Microsoft OAuth2 authorization URL.
    Frontend redirects user here to approve Mail.Read permission.
    """
    app = _get_msal_app()
    url = app.get_authorization_request_url(
        scopes=SCOPES,
        state=state,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )
    return url


async def exchange_code_for_tokens(code: str) -> dict:
    """
    Step 2: Exchange the auth code for access + refresh tokens.
    Called from the OAuth callback endpoint.
    """
    app = _get_msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )
    if "error" in result:
        raise ValueError(f"Microsoft OAuth error: {result.get('error_description', result['error'])}")
    return result


async def _get_valid_token(user_id: str) -> str:
    """
    Retrieve a valid access token for the user, refreshing if expired.
    Returns the access token string.
    """
    token_row = await get_email_token(user_id, provider="outlook")
    if not token_row:
        raise ValueError("Outlook not connected for this user")

    # Check expiry
    expiry_str = token_row.get("token_expiry")
    if expiry_str:
        expiry = datetime.fromisoformat(expiry_str)
        now = datetime.now(timezone.utc)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if now >= expiry:  # Token expired — refresh
            app = _get_msal_app()
            result = app.acquire_token_by_refresh_token(
                refresh_token=token_row["refresh_token"],
                scopes=SCOPES,
            )
            if "error" in result:
                raise ValueError(f"Token refresh failed: {result.get('error_description')}")
            await save_email_token(
                user_id=user_id,
                provider="outlook",
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token", token_row["refresh_token"]),
                token_expiry=datetime.now(timezone.utc) + timedelta(seconds=result.get("expires_in", 3600)),
                email_address=token_row.get("email_address", ""),
            )
            return result["access_token"]

    return token_row["access_token"]


async def sync_outlook_orders(user_id: str, max_emails: int = 50) -> dict:
    """
    Main Outlook sync function.
    Searches inbox for ecommerce order emails via Graph API,
    extracts order data via Gemini, saves to Supabase.
    """
    from backend.services.gemini_service import extract_order_from_email

    access_token = await _get_valid_token(user_id)
    headers = {"Authorization": f"Bearer {access_token}"}

    synced = 0
    new_orders = 0
    errors = 0

    async with httpx.AsyncClient() as client:
        for sender_domain in PLATFORM_SENDERS:
            platform = sender_domain.split(".")[0]  # e.g. 'amazon'

            # Graph API OData filter: find emails from this sender domain
            filter_query = (
                f"contains(from/emailAddress/address, '{sender_domain}') "
                f"and contains(subject, 'order')"
            )
            url = (
                f"{GRAPH_BASE}/me/messages"
                f"?$filter={filter_query}"
                f"&$top={max_emails // len(PLATFORM_SENDERS)}"
                f"&$select=id,subject,from,receivedDateTime,body"
            )

            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    print(f"[Outlook] Graph API error for {sender_domain}: {resp.status_code}")
                    continue

                messages = resp.json().get("value", [])

                for msg in messages:
                    try:
                        subject   = msg.get("subject", "")
                        sender    = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                        date_str  = msg.get("receivedDateTime", "")
                        body      = msg.get("body", {}).get("content", "")[:8000]

                        email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"
                        # Skip blocked brands (quick commerce, SaaS, etc.)
            sender_lower = (sender or "").lower()
            subject_lower = (subject or "").lower()
            combined = sender_lower + " " + subject_lower
            skip = False
            for blocked in BLOCKED_BRANDS:
                if blocked in combined:
                    print(f"[Outlook] Skipped blocked brand: {blocked}")
                    skip = True
                    break
            if skip:
                skipped += 1
                continue
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
                        print(f"[Outlook] Error processing message: {e}")
                        errors += 1

            except Exception as e:
                print(f"[Outlook] Error fetching from {sender_domain}: {e}")
                errors += 1

    return {"synced": synced, "new_orders": new_orders, "errors": errors}
