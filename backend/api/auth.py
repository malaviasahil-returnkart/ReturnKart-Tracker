"""
RETURNKART.IN — GMAIL OAUTH ROUTES (MULTI-ACCOUNT)

Flow:
  1. GET /api/auth/google       → redirects to Google consent screen
  2. GET /api/auth/callback     → exchanges code, saves token + profile
  3. DELETE /api/auth/revoke    → revokes one or all Gmail accounts
  4. GET /api/auth/status       → checks if user has ANY Gmail connected
  5. GET /api/auth/accounts     → returns list of all connected accounts
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import json
import urllib.parse

from backend.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
)
from backend.services.supabase_service import (
    save_gmail_token, delete_gmail_token, get_gmail_token,
    get_all_gmail_tokens, get_gmail_token_by_email,
)

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def build_flow() -> Flow:
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    return flow


def _fetch_google_userinfo(access_token: str) -> dict:
    try:
        import requests as req
        resp = req.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Failed to fetch Google userinfo: {e}")
    return {}


@router.get("/google")
async def google_auth_start(request: Request):
    """
    Redirect to Google consent. Works for first account AND adding more.
    prompt=consent forces the account picker every time.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    flow = build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",    # always show account picker + consent
        state=user_id,
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_auth_callback(request: Request):
    """
    Exchange code for tokens. Fetch Google profile. Save with email as key.
    Supports adding multiple accounts — each email gets its own row.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}?error=gmail_denied")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    user_id = state

    try:
        flow = build_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Fetch Google profile to get email (used as unique key)
        profile = _fetch_google_userinfo(credentials.token)
        user_email = profile.get("email", "")
        user_name = profile.get("name", "")
        user_picture = profile.get("picture", "")

        # Save token — upserts on (user_id, user_email)
        await save_gmail_token(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=credentials.expiry,
            scope=" ".join(credentials.scopes) if credentials.scopes else "",
            user_email=user_email,
            user_name=user_name,
            user_picture=user_picture,
        )

        # Pass profile back to frontend via URL params
        profile_params = ""
        if user_email:
            params = {
                "user_name": user_name,
                "user_email": user_email,
                "user_picture": user_picture,
            }
            profile_params = "&" + urllib.parse.urlencode(params)

        return RedirectResponse(url=f"{FRONTEND_URL}?gmail=connected{profile_params}")

    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}?error=oauth_failed")


@router.delete("/revoke")
async def revoke_gmail(request: Request):
    """
    Revoke one Gmail account (if email provided) or ALL accounts.
    DPDP Act 2023 — Right to Withdraw Consent.
    """
    user_id = request.query_params.get("user_id")
    email = request.query_params.get("email")  # optional: revoke specific account
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        if email:
            # Revoke specific account
            token_row = await get_gmail_token_by_email(user_id, email)
            if token_row and token_row.get("access_token"):
                try:
                    import requests as req
                    req.post(
                        "https://oauth2.googleapis.com/revoke",
                        params={"token": token_row["access_token"]},
                        headers={"content-type": "application/x-www-form-urlencoded"},
                        timeout=5,
                    )
                except Exception:
                    pass
            await delete_gmail_token(user_id, user_email=email)
        else:
            # Revoke ALL accounts
            tokens = await get_all_gmail_tokens(user_id)
            for t in tokens:
                try:
                    import requests as req
                    req.post(
                        "https://oauth2.googleapis.com/revoke",
                        params={"token": t.get("access_token", "")},
                        headers={"content-type": "application/x-www-form-urlencoded"},
                        timeout=5,
                    )
                except Exception:
                    pass
            await delete_gmail_token(user_id)

        return {"status": "revoked", "message": "Gmail access removed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revoke failed: {str(e)}")


@router.get("/status")
async def gmail_status(request: Request):
    """
    Check if user has ANY connected Gmail account.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    tokens = await get_all_gmail_tokens(user_id)
    return {
        "connected": len(tokens) > 0,
        "count": len(tokens),
    }


@router.get("/accounts")
async def list_accounts(request: Request):
    """
    Return all connected Gmail accounts for a user.
    Frontend uses this to show the account list.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    tokens = await get_all_gmail_tokens(user_id)
    accounts = []
    for t in tokens:
        accounts.append({
            "email": t.get("user_email", ""),
            "name": t.get("user_name", ""),
            "picture": t.get("user_picture", ""),
            "connected_at": t.get("created_at", ""),
        })
    return {"accounts": accounts, "count": len(accounts)}
