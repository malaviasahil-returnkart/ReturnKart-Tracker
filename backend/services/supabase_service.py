"""
RETURNKART.IN — SUPABASE SERVICE
Task #15: Central DB layer. All Supabase reads/writes go through here.
No other file should import supabase directly.

Rule: one function per DB operation. Never write raw queries outside this file.
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))


def get_client() -> Client:
    """Get a Supabase client using the service key (admin access)."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ─────────────────────────────────────────────
# GMAIL TOKENS
# ─────────────────────────────────────────────

async def save_gmail_token(
    user_id: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expiry: Optional[datetime],
    scope: str,
) -> dict:
    """Upsert Gmail OAuth tokens for a user."""
    client = get_client()
    data = {
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": token_expiry.isoformat() if token_expiry else None,
        "scope": scope,
        "updated_at": datetime.now(IST).isoformat(),
    }
    result = (
        client.table("gmail_tokens")
        .upsert(data, on_conflict="user_id")
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_gmail_token(user_id: str) -> Optional[dict]:
    """Retrieve Gmail token for a user. Returns None if not connected."""
    client = get_client()
    result = (
        client.table("gmail_tokens")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def delete_gmail_token(user_id: str) -> None:
    """Delete Gmail token — used when user revokes access."""
    client = get_client()
    client.table("gmail_tokens").delete().eq("user_id", user_id).execute()


# ─────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────

async def upsert_order(order: OrderCreate) -> dict:
    """
    Insert or update an order.
    UNIQUE(user_id, order_id) prevents duplicates automatically.
    """
    client = get_client()
    data = order.model_dump()
    # Convert date objects to ISO strings for Supabase
    for key, val in data.items():
        if isinstance(val, (date, datetime)):
            data[key] = val.isoformat()
    result = (
        client.table("orders")
        .upsert(data, on_conflict="user_id,order_id")
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_orders_by_user(user_id: str, status: Optional[str] = None) -> list:
    """Get all orders for a user, optionally filtered by status."""
    client = get_client()
    query = (
        client.table("orders")
        .select("*")
        .eq("user_id", user_id)
        .order("return_deadline", desc=False)
    )
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return result.data or []


async def update_order_status(order_id: str, user_id: str, status: str) -> dict:
    """Update order status (kept / returned / expired)."""
    client = get_client()
    result = (
        client.table("orders")
        .update({"status": status})
        .eq("id", order_id)
        .eq("user_id", user_id)  # RLS double-check
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_expiring_soon(user_id: str, days: int = 3) -> list:
    """Get orders whose return deadline is within N days. Used for urgent alerts."""
    client = get_client()
    today = date.today()
    cutoff = date.today().replace(day=today.day + days)
    result = (
        client.table("orders")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .lte("return_deadline", cutoff.isoformat())
        .gte("return_deadline", today.isoformat())
        .execute()
    )
    return result.data or []


# ─────────────────────────────────────────────
# CONSENT (DPDP ACT 2023)
# ─────────────────────────────────────────────

async def log_consent(
    user_id: str,
    purpose_id: str,
    consented: bool,
    consent_text: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> dict:
    """Write an immutable consent event to the audit log."""
    client = get_client()
    data = {
        "user_id": user_id,
        "purpose_id": purpose_id,
        "consented": consented,
        "consent_text": consent_text,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    result = client.table("user_consents").insert(data).execute()
    return result.data[0] if result.data else {}
