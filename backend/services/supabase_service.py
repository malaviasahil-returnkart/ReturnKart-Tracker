"""
RETURNKART.IN — SUPABASE SERVICE
Central DB layer. All Supabase reads/writes go through here.

MULTI-GMAIL: gmail_tokens supports multiple rows per user.
Unique constraint is on (user_id, user_email).
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))

_client: Optional[Client] = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


# ─────────────────────────────────────────────
# GMAIL TOKENS (multi-account)
# ─────────────────────────────────────────────

async def save_gmail_token(
    user_id: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expiry: Optional[datetime],
    scope: str,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    user_picture: Optional[str] = None,
) -> dict:
    client = get_client()
    # Ensure user_email is never NULL — use 'unknown' as fallback
    email = user_email or "unknown"
    data = {
        "user_id": user_id,
        "user_email": email,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": token_expiry.isoformat() if token_expiry else None,
        "scope": scope,
        "updated_at": datetime.now(IST).isoformat(),
    }
    if user_name is not None:
        data["user_name"] = user_name
    if user_picture is not None:
        data["user_picture"] = user_picture

    # Always upsert on (user_id, user_email)
    try:
        result = client.table("gmail_tokens").upsert(data, on_conflict="user_id,user_email").execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"[Supabase] save_gmail_token error: {e}")
        # Fallback: try without on_conflict for legacy rows
        try:
            result = client.table("gmail_tokens").upsert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e2:
            print(f"[Supabase] save_gmail_token fallback error: {e2}")
            return {}


async def get_gmail_token(user_id: str) -> Optional[dict]:
    """Get the first connected Gmail token (backward compat)."""
    client = get_client()
    result = (
        client.table("gmail_tokens")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_all_gmail_tokens(user_id: str) -> list:
    """Get ALL connected Gmail accounts for a user."""
    client = get_client()
    result = (
        client.table("gmail_tokens")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


async def get_gmail_token_by_email(user_id: str, user_email: str) -> Optional[dict]:
    """Get a specific Gmail token by email address."""
    client = get_client()
    result = (
        client.table("gmail_tokens")
        .select("*")
        .eq("user_id", user_id)
        .eq("user_email", user_email)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def delete_gmail_token(user_id: str, user_email: Optional[str] = None) -> None:
    """Delete one Gmail token (by email) or ALL tokens for a user."""
    q = get_client().table("gmail_tokens").delete().eq("user_id", user_id)
    if user_email:
        q = q.eq("user_email", user_email)
    q.execute()


# ─────────────────────────────────────────────
# EMAIL TOKENS (Yahoo, Outlook, Rediff, iCloud…)
# ─────────────────────────────────────────────

async def save_email_token(
    user_id: str,
    provider: str,
    access_token: str,
    refresh_token: Optional[str],
    token_expiry: Optional[datetime],
    email_address: str,
    imap_host: Optional[str] = None,
    provider_label: Optional[str] = None,
) -> dict:
    client = get_client()
    data = {
        "user_id": user_id,
        "provider": provider,
        "provider_label": provider_label or provider.title(),
        "email_address": email_address,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": token_expiry.isoformat() if token_expiry else None,
        "imap_host": imap_host,
        "updated_at": datetime.now(IST).isoformat(),
    }
    result = (
        client.table("email_tokens")
        .upsert(data, on_conflict="user_id,provider")
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_email_token(user_id: str, provider: str) -> Optional[dict]:
    result = (
        get_client().table("email_tokens")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", provider)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_all_email_tokens(user_id: str) -> list:
    result = (
        get_client().table("email_tokens")
        .select("provider, provider_label, email_address, last_synced_at")
        .eq("user_id", user_id)
        .execute()
    )
    return result.data or []


async def delete_email_token(user_id: str, provider: str) -> None:
    get_client().table("email_tokens").delete().eq("user_id", user_id).eq("provider", provider).execute()


# ─────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────

def _order_to_dict(order: OrderCreate) -> dict:
    data = order.model_dump()
    for key, val in data.items():
        if isinstance(val, (date, datetime)):
            data[key] = val.isoformat()
    return data


async def upsert_order(order: OrderCreate) -> dict:
    client = get_client()
    result = (
        client.table("orders")
        .upsert(_order_to_dict(order), on_conflict="user_id,order_id")
        .execute()
    )
    return result.data[0] if result.data else {}


async def bulk_upsert_orders(orders: list[OrderCreate]) -> int:
    if not orders:
        return 0
    client = get_client()
    # Deduplicate by order_id — keep last occurrence (most recent email)
    seen = {}
    for o in orders:
        seen[o.order_id] = o
    unique_orders = list(seen.values())
    rows = [_order_to_dict(o) for o in unique_orders]
    result = (
        client.table("orders")
        .upsert(rows, on_conflict="user_id,order_id")
        .execute()
    )
    return len(result.data) if result.data else 0


async def get_existing_order_ids(user_id: str) -> set[str]:
    result = (
        get_client().table("orders")
        .select("order_id")
        .eq("user_id", user_id)
        .execute()
    )
    return {row["order_id"] for row in (result.data or [])}


async def get_orders_by_user(user_id: str, status: Optional[str] = None) -> list:
    client = get_client()
    query = (
        client.table("orders")
        .select("*")
        .eq("user_id", user_id)
        .order("return_deadline", desc=False)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data or []


async def update_order_status(order_id: str, user_id: str, status: str) -> dict:
    result = (
        get_client().table("orders")
        .update({"status": status})
        .eq("id", order_id)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_expiring_soon(user_id: str, days: int = 3) -> list:
    today  = date.today()
    cutoff = date.today().replace(day=today.day + days)
    result = (
        get_client().table("orders")
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
    data = {
        "user_id": user_id,
        "purpose_id": purpose_id,
        "consented": consented,
        "consent_text": consent_text,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    result = get_client().table("user_consents").insert(data).execute()
    return result.data[0] if result.data else {}


# ───── DATA DELETION (DPDP ACT 2023 — RIGHT TO ERASURE) ─────

async def delete_all_user_data(user_id) -> dict:
    """
    DPDP Act 2023 — Right to Erasure.
    Deletes ALL user data from: orders, evidence_locker, gmail_tokens, platforms.
    IMPORTANT: user_consents are NEVER deleted — they are the legally-required
    audit trail proving we had consent and that deletion was requested.
    """
    client = get_client()
    deleted = {}
    tables = ["evidence_locker", "orders", "gmail_tokens", "platforms"]
    for table in tables:
        try:
            result = client.table(table).delete().eq("user_id", user_id).execute()
            deleted[table] = len(result.data) if result.data else 0
        except Exception as e:
            deleted[table] = f"error: {str(e)}"
    return deleted
