"""
RETURNKART.IN — MULTI-PROVIDER EMAIL API ROUTES

Endpoints for connecting and syncing non-Gmail email providers.

  IMAP PROVIDERS (Yahoo, Rediffmail, iCloud, Zoho, AOL, generic):
    POST /api/email/imap/connect   — validate + store IMAP credentials
    POST /api/email/imap/sync      — trigger IMAP sync in background
    DELETE /api/email/imap/disconnect — remove stored IMAP credentials

  OUTLOOK / HOTMAIL (Microsoft Graph API):
    GET  /api/email/outlook/auth       — generate Microsoft OAuth URL
    GET  /api/email/outlook/callback   — handle OAuth callback from Microsoft
    POST /api/email/outlook/sync       — trigger Outlook sync in background
    DELETE /api/email/outlook/disconnect — revoke Outlook access

  PROVIDER STATUS:
    GET  /api/email/status/{user_id}   — list all connected email providers
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid

from backend.services.imap_service import (
    validate_imap_credentials,
    sync_imap_orders,
    IMAPCONFIG,
    _detect_provider,
)
from backend.services.outlook_service import (
    get_auth_url,
    exchange_code_for_tokens,
    sync_outlook_orders,
)
from backend.services.supabase_service import (
    save_email_token,
    get_email_token,
    get_all_email_tokens,
    delete_email_token,
)
from backend.config import FRONTEND_URL

router = APIRouter()


# ─────────────────────────────────────────────
# IMAP PROVIDERS
# ─────────────────────────────────────────────

class ImapConnectRequest(BaseModel):
    user_id: str
    email_address: str
    app_password: str
    imap_host: Optional[str] = None  # Auto-detected if not provided


@router.post("/imap/connect")
async def connect_imap(body: ImapConnectRequest):
    """
    POST /api/email/imap/connect
    Validates IMAP credentials and saves them to Supabase.
    """
    imap_host = body.imap_host
    if not imap_host:
        provider_slug = _detect_provider(body.email_address)
        config = IMAPCONFIG.get(provider_slug)
        if not config:
            raise HTTPException(
                status_code=400,
                detail="Unknown email provider. Please provide imap_host manually.",
            )
        imap_host = config["imap_host"]

    try:
        validate_imap_credentials(imap_host, body.email_address, body.app_password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    provider_slug = _detect_provider(body.email_address)
    provider_label = {
        "yahoo": "Yahoo Mail", "ymail": "Yahoo Mail",
        "rediff": "Rediffmail", "rediffmail": "Rediffmail",
        "icloud": "iCloud Mail", "me": "iCloud Mail",
        "zoho": "Zoho Mail",
        "aol": "AOL Mail",
        "hotmail": "Outlook", "live": "Outlook",
    }.get(provider_slug, provider_slug.title() + " Mail")

    await save_email_token(
        user_id=body.user_id,
        provider=provider_slug,
        access_token=body.app_password,
        refresh_token=None,
        token_expiry=None,
        email_address=body.email_address,
        imap_host=imap_host,
        provider_label=provider_label,
    )

    return {
        "status": "connected",
        "provider": provider_label,
        "email": body.email_address,
        "message": f"{provider_label} connected. Tap Sync to import your orders.",
    }


@router.post("/imap/sync")
async def sync_imap(request: Request, background_tasks: BackgroundTasks):
    """POST /api/email/imap/sync — triggers IMAP sync in background."""
    body = await request.json()
    user_id = body.get("user_id")
    provider = body.get("provider")

    if not user_id or not provider:
        raise HTTPException(status_code=400, detail="user_id and provider are required")

    token_row = await get_email_token(user_id, provider=provider)
    if not token_row:
        raise HTTPException(status_code=404, detail=f"{provider} not connected")

    background_tasks.add_task(
        sync_imap_orders,
        user_id=user_id,
        imap_host=token_row["imap_host"],
        email_address=token_row["email_address"],
        app_password=token_row["access_token"],
    )
    return {"status": "sync_started", "message": f"{provider} sync running in background"}


@router.delete("/imap/disconnect")
async def disconnect_imap(request: Request):
    """DELETE /api/email/imap/disconnect — removes IMAP credentials."""
    body = await request.json()
    user_id = body.get("user_id")
    provider = body.get("provider")
    if not user_id or not provider:
        raise HTTPException(status_code=400, detail="user_id and provider are required")
    await delete_email_token(user_id, provider)
    return {"status": "disconnected", "provider": provider}


# ─────────────────────────────────────────────
# OUTLOOK — Microsoft Graph API
# ─────────────────────────────────────────────

@router.get("/outlook/auth")
async def outlook_auth(user_id: str):
    """GET /api/email/outlook/auth?user_id=... — returns Microsoft OAuth URL."""
    state = f"{user_id}::{uuid.uuid4().hex}"
    auth_url = get_auth_url(state=state)
    return {"auth_url": auth_url}


@router.get("/outlook/callback")
async def outlook_callback(code: str, state: str):
    """GET /api/email/outlook/callback — Microsoft redirects here after approval."""
    try:
        user_id = state.split("::")[0]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        tokens = await exchange_code_for_tokens(code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from datetime import timedelta, timezone
    import datetime as dt

    expiry = dt.datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    id_token_claims = tokens.get("id_token_claims", {})
    email_address = id_token_claims.get("preferred_username", "")

    await save_email_token(
        user_id=user_id,
        provider="outlook",
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        token_expiry=expiry,
        email_address=email_address,
        provider_label="Outlook / Hotmail",
    )

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{FRONTEND_URL}?outlook_connected=true")


@router.post("/outlook/sync")
async def sync_outlook(request: Request, background_tasks: BackgroundTasks):
    """POST /api/email/outlook/sync — triggers Outlook sync in background."""
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    background_tasks.add_task(sync_outlook_orders, user_id=user_id)
    return {"status": "sync_started", "message": "Outlook sync running in background"}


@router.delete("/outlook/disconnect")
async def disconnect_outlook(request: Request):
    """DELETE /api/email/outlook/disconnect — removes Outlook token."""
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    await delete_email_token(user_id, "outlook")
    return {"status": "disconnected", "provider": "outlook"}


# ─────────────────────────────────────────────
# STATUS — list all connected providers
# ─────────────────────────────────────────────

@router.get("/status/{user_id}")
async def email_status(user_id: str):
    """
    GET /api/email/status/{user_id}
    Returns all connected email providers for this user.
    Used by the Settings Vault screen to show which accounts are linked.

    Returns empty list gracefully for:
    - Users with no connected providers
    - Invalid or non-UUID user_id values (e.g. during testing)
    """
    try:
        tokens = await get_all_email_tokens(user_id)
    except Exception as e:
        # Supabase throws if user_id is not a valid UUID format —
        # return empty provider list rather than a 500
        print(f"[email_status] Could not fetch tokens for user_id={user_id}: {e}")
        tokens = []

    providers = [
        {
            "provider": t["provider"],
            "label": t.get("provider_label", t["provider"].title()),
            "email": t.get("email_address", ""),
            "connected": True,
        }
        for t in tokens
    ]
    return {"providers": providers, "count": len(providers)}
