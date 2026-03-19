"""
RETURNKART.IN — DPDP CONSENT API
Task #26: Timestamped consent logging for DPDP Act 2023 compliance.

Every consent event (grant, revoke, delete) is immutably logged.
Records cannot be updated or deleted — append-only audit trail.

Endpoints:
  POST  /api/consent/log     → log a consent event
  GET   /api/consent/history  → get consent history for a user
"""
from fastapi import APIRouter, HTTPException, Request
from backend.services.supabase_service import log_consent, get_consent_history

router = APIRouter()

# Valid consent purpose IDs
VALID_PURPOSES = [
    'gmail_read_access',       # User consents to Gmail scanning
    'return_tracking',         # User consents to return window tracking
    'data_storage',            # User consents to data being stored
    'gmail_revoke',            # User revokes Gmail access
    'data_delete_request',     # User requests all data deletion
    'platform_add',            # User consents to adding a new platform
]


@router.post("/log")
async def log_consent_event(request: Request):
    """
    Log an immutable consent event.
    Body: { user_id, purpose_id, consented (bool), consent_text }
    """
    body = await request.json()
    user_id = body.get("user_id")
    purpose_id = body.get("purpose_id")
    consented = body.get("consented", True)
    consent_text = body.get("consent_text", "")

    if not user_id or not purpose_id:
        raise HTTPException(status_code=400, detail="user_id and purpose_id are required")

    if purpose_id not in VALID_PURPOSES:
        raise HTTPException(status_code=400, detail=f"Invalid purpose_id. Valid: {VALID_PURPOSES}")

    # Capture request metadata for audit
    ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent", "")

    result = await log_consent(
        user_id=user_id,
        purpose_id=purpose_id,
        consented=consented,
        consent_text=consent_text,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {"consent": result, "message": f"Consent event '{purpose_id}' logged successfully"}


@router.get("/history")
async def consent_history(request: Request):
    """
    Get full consent audit trail for a user.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    history = await get_consent_history(user_id)
    return {"history": history, "count": len(history)}
