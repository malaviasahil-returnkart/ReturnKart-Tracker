"""
RETURNKART.IN — SUPABASE SERVICE
Central DB layer. All Supabase reads/writes go through here.
No other file should import supabase directly.
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ───── GMAIL TOKENS ─────

async def save_gmail_token(user_id, access_token, refresh_token, token_expiry, scope) -> dict:
    client = get_client()
    data = {
        "user_id": user_id, "access_token": access_token, "refresh_token": refresh_token,
        "token_expiry": token_expiry.isoformat() if token_expiry else None,
        "scope": scope, "updated_at": datetime.now(IST).isoformat(),
    }
    result = client.table("gmail_tokens").upsert(data, on_conflict="user_id").execute()
    return result.data[0] if result.data else {}

async def get_gmail_token(user_id) -> Optional[dict]:
    client = get_client()
    result = client.table("gmail_tokens").select("*").eq("user_id", user_id).limit(1).execute()
    return result.data[0] if result.data else None

async def delete_gmail_token(user_id) -> None:
    client = get_client()
    client.table("gmail_tokens").delete().eq("user_id", user_id).execute()


# ───── ORDERS ─────

async def upsert_order(order: OrderCreate) -> dict:
    client = get_client()
    data = order.model_dump()
    for key, val in data.items():
        if isinstance(val, (date, datetime)):
            data[key] = val.isoformat()
    result = client.table("orders").upsert(data, on_conflict="user_id,order_id").execute()
    return result.data[0] if result.data else {}

async def get_orders_by_user(user_id, status=None) -> list:
    client = get_client()
    query = client.table("orders").select("*").eq("user_id", user_id).order("return_deadline", desc=False)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return result.data or []

async def update_order_status(order_id, user_id, status) -> dict:
    client = get_client()
    result = client.table("orders").update({"status": status}).eq("id", order_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else {}

async def get_expiring_soon(user_id, days=3) -> list:
    client = get_client()
    today = date.today()
    cutoff = today + timedelta(days=days)
    result = (
        client.table("orders").select("*")
        .eq("user_id", user_id).eq("status", "active")
        .lte("return_deadline", cutoff.isoformat()).gte("return_deadline", today.isoformat())
        .execute()
    )
    return result.data or []


# ───── EVIDENCE LOCKER ─────

async def save_evidence(order_id, user_id, file_url, file_type, file_size_bytes) -> dict:
    client = get_client()
    data = {"order_id": order_id, "user_id": user_id, "file_url": file_url, "file_type": file_type, "file_size_bytes": file_size_bytes}
    result = client.table("evidence_locker").insert(data).execute()
    return result.data[0] if result.data else {}

async def get_evidence_by_order(order_id, user_id) -> list:
    client = get_client()
    result = client.table("evidence_locker").select("*").eq("order_id", order_id).eq("user_id", user_id).order("uploaded_at", desc=True).execute()
    return result.data or []

async def delete_evidence(evidence_id, user_id) -> None:
    client = get_client()
    client.table("evidence_locker").delete().eq("id", evidence_id).eq("user_id", user_id).execute()


# ───── PLATFORMS ─────

async def save_platform(user_id, platform_name, platform_slug, website_url, email_domains, email_sender_patterns, return_policy, communication_channels) -> dict:
    client = get_client()
    data = {
        "user_id": user_id,
        "platform_name": platform_name,
        "platform_slug": platform_slug,
        "website_url": website_url,
        "email_domains": email_domains,
        "email_sender_patterns": email_sender_patterns,
        "return_policy": return_policy,
        "communication_channels": communication_channels,
        "ai_generated": True,
        "updated_at": datetime.now(IST).isoformat(),
    }
    result = client.table("platforms").upsert(data, on_conflict="platform_slug,user_id").execute()
    return result.data[0] if result.data else {}

async def get_platforms_for_user(user_id) -> list:
    client = get_client()
    # Get user-specific + global platforms
    result = client.table("platforms").select("*").or_(f"user_id.eq.{user_id},is_global.eq.true").order("platform_name").execute()
    return result.data or []

async def delete_platform(platform_id, user_id) -> None:
    client = get_client()
    client.table("platforms").delete().eq("id", platform_id).eq("user_id", user_id).execute()


# ───── CONSENT (DPDP ACT 2023) ─────

async def log_consent(user_id, purpose_id, consented, consent_text, ip_address=None, user_agent=None) -> dict:
    client = get_client()
    data = {
        "user_id": user_id, "purpose_id": purpose_id, "consented": consented,
        "consent_text": consent_text, "ip_address": ip_address, "user_agent": user_agent,
    }
    result = client.table("user_consents").insert(data).execute()
    return result.data[0] if result.data else {}
