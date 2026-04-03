"""
RETURNKART.IN — ORDERS API ROUTES

Includes sync-debug and gmail-diagnose endpoints for troubleshooting.
"""
import asyncio
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Optional

from backend.services.supabase_service import (
    get_orders_by_user,
    update_order_status,
    get_expiring_soon,
    get_all_gmail_tokens,
    save_gmail_token,
)
from backend.services.gmail_service import sync_gmail_orders, PLATFORM_QUERIES
from backend.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

router = APIRouter()

VALID_STATUSES = ("kept", "returned", "active", "expired", "want_to_return")


@router.get("")
async def list_orders(request: Request, status: Optional[str] = None):
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    orders = await get_orders_by_user(user_id, status=status)
    return {"orders": orders, "count": len(orders)}


@router.get("/urgent")
async def urgent_orders(request: Request, days: int = 3):
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    orders = await get_expiring_soon(user_id, days=days)
    return {"orders": orders, "count": len(orders)}


@router.patch("/{order_id}")
async def patch_order(order_id: str, request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    status = body.get("status")
    if not user_id or not status:
        raise HTTPException(status_code=400, detail="user_id and status are required")
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
    updated = await update_order_status(order_id, user_id, status)
    return {"order": updated}


@router.post("/sync")
async def trigger_sync(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    background_tasks.add_task(sync_gmail_orders, user_id)
    return {"status": "sync_started", "message": "Gmail sync running in background"}


@router.post("/sync-debug")
async def sync_debug(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        result = await sync_gmail_orders(user_id)
        return {"status": "complete", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e), "type": type(e).__name__}


@router.post("/gmail-diagnose")
async def gmail_diagnose(request: Request):
    """
    POST /api/orders/gmail-diagnose
    Tests Gmail connection with progressively broader queries.
    Returns count of emails found per query level.
    Use this to figure out why sync finds 0 emails.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build
    import base64

    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    tokens = await get_all_gmail_tokens(user_id)
    if not tokens:
        return {"error": "No Gmail accounts connected"}

    results = []

    for token_row in tokens:
        account_email = token_row.get("user_email", "unknown")
        account_result = {"account": account_email, "tests": []}

        try:
            # Build credentials and refresh if needed
            creds = Credentials(
                token=token_row["access_token"],
                refresh_token=token_row.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=token_row.get("scope", "").split(),
            )

            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(GoogleRequest())
                    await save_gmail_token(
                        user_id=user_id,
                        access_token=creds.token,
                        refresh_token=creds.refresh_token,
                        token_expiry=creds.expiry,
                        scope=" ".join(creds.scopes) if creds.scopes else "",
                        user_email=account_email,
                    )
                    account_result["token_refreshed"] = True
                except Exception as e:
                    account_result["token_refresh_error"] = str(e)
                    results.append(account_result)
                    continue

            loop = asyncio.get_event_loop()
            service = await loop.run_in_executor(
                None, lambda: build("gmail", "v1", credentials=creds)
            )

            # Test 1: Can we access Gmail at all? Get profile.
            try:
                profile = await loop.run_in_executor(
                    None, lambda: service.users().getProfile(userId="me").execute()
                )
                account_result["gmail_profile"] = {
                    "email": profile.get("emailAddress"),
                    "total_messages": profile.get("messagesTotal"),
                    "total_threads": profile.get("threadsTotal"),
                }
            except Exception as e:
                account_result["gmail_profile_error"] = str(e)
                results.append(account_result)
                continue

            # Test 2: Broadest possible query — just "from:amazon"
            test_queries = [
                ("broadest: from:amazon.in", "from:amazon.in"),
                ("broad: from:amazon.in order", "from:amazon.in order"),
                ("our_query: amazon platform query", PLATFORM_QUERIES.get("amazon", "")),
                ("broadest: from:flipkart.com", "from:flipkart.com"),
                ("broad: from:flipkart.com order", "from:flipkart.com order"),
                ("our_query: flipkart platform query", PLATFORM_QUERIES.get("flipkart", "")),
                ("broadest: from:myntra.com", "from:myntra.com"),
                ("any_shopping: order confirmed OR shipped OR delivered", "subject:(order confirmed OR shipped OR delivered)"),
            ]

            for label, query in test_queries:
                try:
                    res = await loop.run_in_executor(
                        None,
                        lambda q=query: service.users().messages().list(
                            userId="me", q=q, maxResults=5
                        ).execute()
                    )
                    msgs = res.get("messages", [])
                    count = len(msgs)
                    est_total = res.get("resultSizeEstimate", 0)

                    # Get subject of first email if found
                    first_subject = None
                    if msgs:
                        try:
                            full_msg = await loop.run_in_executor(
                                None,
                                lambda mid=msgs[0]["id"]: service.users().messages().get(
                                    userId="me", id=mid, format="metadata",
                                    metadataHeaders=["Subject", "From"]
                                ).execute()
                            )
                            headers = full_msg.get("payload", {}).get("headers", [])
                            for h in headers:
                                if h["name"].lower() == "subject":
                                    first_subject = h["value"][:100]
                                elif h["name"].lower() == "from":
                                    first_from = h["value"][:100]
                        except:
                            pass

                    account_result["tests"].append({
                        "label": label,
                        "found": count,
                        "estimated_total": est_total,
                        "first_subject": first_subject,
                    })
                except Exception as e:
                    account_result["tests"].append({
                        "label": label,
                        "error": str(e),
                    })

        except Exception as e:
            account_result["error"] = str(e)

        results.append(account_result)

    return {"diagnose": results}
