"""
RETURNKART.IN — GMAIL OAUTH ROUTES
Task #10: Build Gmail OAuth authentication flow

Flow:
  1. GET /api/auth/google       → redirects user to Google consent screen
  2. GET /api/auth/callback     → exchanges code for tokens, saves to DB
  3. DELETE /api/auth/revoke    → revokes Gmail access (DPDP: right to withdraw)
  4. GET /api/auth/status       → checks if user has connected Gmail
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import json

from backend.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
)
from backend.services.supabase_service import save_gmail_token, delete_gmail_token, get_gmail_token

router = APIRouter()

# Gmail scopes — read-only, no send/delete permissions
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
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
    """Create a Google OAuth flow instance."""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    return flow


@router.get("/google")
async def google_auth_start(request: Request):
    """
    Step 1: Redirect user to Google consent screen.
    Frontend calls this to start the Gmail connection.
    Requires: user_id passed as query param (from Supabase auth session).
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    flow = build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",       # get refresh_token so we can sync later
        include_granted_scopes="true",
        prompt="consent",            # force consent screen so refresh_token is always returned
        state=user_id,               # pass user_id through state param
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_auth_callback(request: Request):
    """
    Step 2: Google redirects back here after user grants permission.
    Exchanges the auth code for access + refresh tokens.
    Saves tokens to gmail_tokens table.
    Redirects user back to frontend dashboard.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # this is the user_id we passed
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

        # Save tokens to Supabase
        await save_gmail_token(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=credentials.expiry,
            scope=" ".join(credentials.scopes) if credentials.scopes else "",
        )

        return RedirectResponse(url=f"{FRONTEND_URL}?gmail=connected")

    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}?error=oauth_failed")


@router.delete("/revoke")
async def revoke_gmail(request: Request):
    """
    DPDP Act 2023 — Right to Withdraw Consent.
    Deletes the Gmail token from DB so we can no longer read their inbox.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        # Try to revoke token at Google as well
        token_row = await get_gmail_token(user_id)
        if token_row and token_row.get("access_token"):
            creds = Credentials(token=token_row["access_token"])
            try:
                import requests as req
                req.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": token_row["access_token"]},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    timeout=5,
                )
            except Exception:
                pass  # best-effort revoke at Google

        await delete_gmail_token(user_id)
        return {"status": "revoked", "message": "Gmail access successfully removed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revoke failed: {str(e)}")


@router.get("/status")
async def gmail_status(request: Request):
    """
    Check if a user has connected their Gmail.
    Frontend uses this on load to decide which screen to show.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    token_row = await get_gmail_token(user_id)
    return {
        "connected": token_row is not None,
        "email": token_row.get("scope", "") if token_row else None,
    }
