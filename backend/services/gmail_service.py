"""
RETURNKART.IN — GMAIL SERVICE
Fetch emails, extract orders via Gemini, calculate return deadlines.

RULES:
  - Only search last 30 days of emails
  - Return deadline = order_date + return_window_days
  - return_window_days comes from: knowledge base > Gemini AI research > default (10)
  - Skip orders where return window has already closed
  - Skip quick commerce (Blinkit, Zepto, Swiggy, etc.)
"""
import base64
import json
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

from backend.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from backend.services.supabase_service import (
    get_gmail_token, save_gmail_token, upsert_order,
)
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))
EMAIL_LOOKBACK_DAYS = 30

_SUBJ = '(subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed" OR subject:"dispatched" OR subject:"out for delivery" OR subject:"arriving" OR subject:"refund" OR subject:"invoice")'
_SUBJ_BROAD = '(subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed" OR subject:"dispatched" OR subject:"out for delivery" OR subject:"arriving" OR subject:"refund" OR subject:"invoice" OR subject:"receipt" OR subject:"purchase" OR subject:"thank you" OR subject:"your package" OR subject:"your parcel" OR subject:"on its way" OR subject:"delivery" OR subject:"tracking" OR subject:"shopping")'

EXCLUDED_PLATFORMS = {"swiggy", "zomato", "blinkit", "zepto", "dunzo", "bigbasket", "grofers", "instamart", "uber eats", "ubereats", "dominos", "pizzahut"}

# Knowledge base for return windows
_KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
_knowledge_base: Optional[dict] = None

def _load_kb() -> dict:
    global _knowledge_base
    if _knowledge_base is None:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            _knowledge_base = json.load(f)
    return _knowledge_base


def _get_return_window_days(brand_slug: str, category: str, ai_days: Optional[int] = None) -> int:
    """Get return window days. Priority: knowledge base > AI research > default."""
    kb = _load_kb()
    category_lower = (category or "default").lower()

    # 1. Try knowledge base (most accurate)
    for p in kb.get("platforms", []):
        if p["brand_slug"] == brand_slug:
            for cat in p.get("categories", []):
                if cat["category"].lower() == category_lower:
                    return cat["return_window_days"]
            for cat in p.get("categories", []):
                if cat["category"].lower() == "default":
                    return cat["return_window_days"]

    # 2. Use AI-researched return window (from Gemini's knowledge)
    if ai_days and 1 <= ai_days <= 60:
        return ai_days

    # 3. Fall back to defaults by category
    defaults = {"fashion": 15, "electronics": 7, "home": 10, "books": 10}
    for key, days in defaults.items():
        if key in category_lower:
            return days

    return kb.get("fallback_policy", {}).get("return_window_days", 10)


def _get_replacement_only(brand_slug: str, category: str, ai_replacement: Optional[bool] = None) -> bool:
    """Check replacement only. Priority: knowledge base > AI > default."""
    kb = _load_kb()
    category_lower = (category or "default").lower()
    for p in kb.get("platforms", []):
        if p["brand_slug"] == brand_slug:
            for cat in p.get("categories", []):
                if cat["category"].lower() == category_lower:
                    return cat.get("is_replacement_only", False)
    if ai_replacement is not None:
        return ai_replacement
    return False


# Gmail queries
UNIVERSAL_QUERIES = {
    "universal_orders": f'(subject:"order confirmed" OR subject:"order placed" OR subject:"your order" OR subject:"order shipped" OR subject:"order dispatched" OR subject:"order delivered" OR subject:"order summary" OR subject:"order receipt" OR subject:"order details") newer_than:{EMAIL_LOOKBACK_DAYS}d',
    "universal_shipping": f'(subject:"has been shipped" OR subject:"has been dispatched" OR subject:"out for delivery" OR subject:"has been delivered" OR subject:"is on its way" OR subject:"your package" OR subject:"your parcel" OR subject:"shipment update" OR subject:"delivery update" OR subject:"tracking number") newer_than:{EMAIL_LOOKBACK_DAYS}d',
    "universal_purchase": f'(subject:"thank you for your purchase" OR subject:"payment received" OR subject:"payment confirmed" OR subject:"invoice for your order" OR subject:"your receipt" OR subject:"purchase confirmation" OR subject:"thank you for shopping" OR subject:"thank you for ordering") newer_than:{EMAIL_LOOKBACK_DAYS}d',
}

PLATFORM_QUERIES = {
    "amazon":    f'(from:amazon.in OR from:amazon.com) {_SUBJ}',
    "flipkart":  f'(from:flipkart.com OR from:ekartlogistics.com) {_SUBJ}',
    "meesho":    f'(from:meesho.com) {_SUBJ}',
    "snapdeal":  f'(from:snapdeal.com) {_SUBJ}',
    "jiomart":   f'(from:jiomart.com OR from:reliancedigital.in) {_SUBJ}',
    "tatacliq":  f'(from:tatacliq.com OR from:tataneu.com) {_SUBJ}',
    "myntra":       f'(from:myntra.com) {_SUBJ_BROAD}',
    "ajio":         f'(from:ajio.com) {_SUBJ_BROAD}',
    "nykaa":        f'(from:nykaa.com OR from:nykaafashion.com) {_SUBJ_BROAD}',
    "shoppersstop": f'(from:shoppersstop.com) {_SUBJ_BROAD}',
    "zara":         f'(from:zara.com OR from:inditex.com) {_SUBJ_BROAD}',
    "hm":           f'(from:hm.com OR from:delivery.hm.com) {_SUBJ_BROAD}',
    "nike":         f'(from:nike.com OR from:nike.in) {_SUBJ_BROAD}',
    "adidas":       f'(from:adidas.co.in OR from:adidas.com) {_SUBJ_BROAD}',
    "levis":        f'(from:levi.in OR from:levi.com OR from:levis.com) {_SUBJ_BROAD}',
    "tommyhilfiger":f'(from:tommy.com OR from:tommyhilfiger.com OR from:pvhcorp.com) {_SUBJ_BROAD}',
    "puma":         f'(from:puma.com OR from:puma.in) {_SUBJ_BROAD}',
}


def _build_credentials(token_row: dict) -> Credentials:
    return Credentials(
        token=token_row["access_token"], refresh_token=token_row.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID, client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_row.get("scope", "").split(),
    )

async def _refresh_if_needed(user_id: str, token_row: dict) -> Credentials:
    creds = _build_credentials(token_row)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await save_gmail_token(user_id=user_id, access_token=creds.token, refresh_token=creds.refresh_token,
            token_expiry=creds.expiry, scope=" ".join(creds.scopes) if creds.scopes else "")
    return creds

def _decode_email_body(payload: dict) -> str:
    body = ""
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        if body.strip(): return body[:12000]
    parts = payload.get("parts", [])
    plain, html = "", ""
    for part in parts:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data", "")
        if mime == "text/plain" and data: plain = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime == "text/html" and data: html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime.startswith("multipart/") and part.get("parts"):
            nested = _decode_email_body(part)
            if nested: plain = plain or nested
    return (plain or html)[:12000]

def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower(): return h["value"]
    return ""

def _detect_platform(sender: str, subject: str) -> str:
    text = (sender + " " + subject).lower()
    for excluded in EXCLUDED_PLATFORMS:
        if excluded in text: return "skip"
    hints = {
        "amazon": ["amazon"], "flipkart": ["flipkart", "ekart"], "meesho": ["meesho"],
        "snapdeal": ["snapdeal"], "jiomart": ["jiomart"], "paytmmall": ["paytmmall", "paytm"],
        "tatacliq": ["tatacliq", "tataneu"], "shopclues": ["shopclues"],
        "myntra": ["myntra"], "ajio": ["ajio"], "nykaa": ["nykaa", "nykaafashion"],
        "shoppersstop": ["shoppersstop"], "lifestylestores": ["lifestylestores"],
        "maxfashion": ["maxfashion"], "pantaloons": ["pantaloons"],
        "trendsin": ["trends.in", "reliancetrends"], "westside": ["westside"], "fabindia": ["fabindia"],
        "zara": ["zara"], "hm": ["hm.com", "h&m", "delivery.hm"], "uniqlo": ["uniqlo"],
        "mango": ["mango.com"], "gap": ["gap.com", "oldnavy"],
        "forever21": ["forever21"], "tommyhilfiger": ["tommy.com", "tommyhilfiger", "pvhcorp"],
        "calvinklein": ["calvinklein"], "levis": ["levi.in", "levi.com", "levis"],
        "nike": ["nike.com", "nike.in"], "adidas": ["adidas"], "puma": ["puma.com", "puma.in"],
        "reebok": ["reebok"], "superdry": ["superdry"],
        "bewakoof": ["bewakoof"], "souledstore": ["souledstore", "thesouledstore"],
        "urbanic": ["urbanic"], "shein": ["shein"], "limeroad": ["limeroad"],
        "croma": ["croma"], "boat": ["boat-lifestyle", "boatlifestyle"],
        "oneplus": ["oneplus"], "samsung": ["samsung"], "apple": ["apple.com"],
        "xiaomi": ["xiaomi", "mi.com"], "noise": ["gonoise"], "realme": ["realme"],
        "vijaysales": ["vijaysales"],
        "purplle": ["purplle"], "mamaearth": ["mamaearth"],
        "pepperfry": ["pepperfry"], "urbanladder": ["urbanladder"],
        "ikea": ["ikea"], "lenskart": ["lenskart"], "caratlane": ["caratlane"],
        "tanishq": ["tanishq"], "decathlon": ["decathlon"], "firstcry": ["firstcry"],
    }
    for platform, keywords in hints.items():
        for kw in keywords:
            if kw in text: return platform
    return "unknown"


async def _process_email(service, msg_ref, platform, user_id, extract_fn, confidence_threshold=0.5):
    """Process a single email: fetch, extract via Gemini (incl. return policy), save if valid."""
    msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
    headers = msg.get("payload", {}).get("headers", [])
    subject = _get_header(headers, "subject")
    sender = _get_header(headers, "from")
    date_str = _get_header(headers, "date")
    body = _decode_email_body(msg.get("payload", {}))

    if not body or len(body) < 50:
        return False, "empty body"

    email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"
    extracted = await extract_fn(email_text, platform)

    if not extracted or not extracted.order_id:
        return False, "no order_id"
    if not extracted.confidence or extracted.confidence < confidence_threshold:
        return False, f"low confidence ({extracted.confidence})"

    today = date.today()
    order_date = today
    if extracted.order_date:
        try: order_date = datetime.strptime(extracted.order_date, "%Y-%m-%d").date()
        except ValueError: order_date = today

    if (today - order_date).days > EMAIL_LOOKBACK_DAYS:
        return False, f"order too old ({order_date})"

    # Calculate return deadline: knowledge base > AI research > default
    category = extracted.category or "Default"
    return_window = _get_return_window_days(
        platform, category,
        ai_days=extracted.return_window_days  # Gemini's researched return policy
    )
    return_deadline = order_date + timedelta(days=return_window)

    if return_deadline < today:
        return False, f"return window closed ({return_deadline})"

    is_replacement = _get_replacement_only(
        platform, category,
        ai_replacement=extracted.is_replacement_only
    )

    order = OrderCreate(
        user_id=user_id, order_id=extracted.order_id,
        brand=extracted.brand or platform.title(),
        item_name=extracted.item_name or "Unknown item",
        price=extracted.total_amount or 0.0,
        order_date=order_date, return_deadline=return_deadline,
        category=category, courier_partner=extracted.courier_partner,
        delivery_pincode=extracted.delivery_pincode,
        is_replacement_only=is_replacement,
        purpose_id="return_tracking", consent_timestamp=datetime.now(IST),
    )
    await upsert_order(order)
    return True, f"{extracted.brand}: {extracted.item_name} (deadline: {return_deadline}, window: {return_window}d)"


async def sync_gmail_orders(user_id: str, max_emails: int = 200) -> dict:
    """Main sync: 30-day lookback, auto return deadlines, skip expired."""
    from backend.services.gemini_service import extract_order_from_email

    token_row = await get_gmail_token(user_id)
    if not token_row:
        return {"error": "Gmail not connected", "synced": 0, "new_orders": 0}

    creds = await _refresh_if_needed(user_id, token_row)
    service = build("gmail", "v1", credentials=creds)

    synced, new_orders, errors, skipped = 0, 0, 0, 0
    details = []
    seen_ids = set()

    # Pass 1: Brand-specific
    for platform, query in PLATFORM_QUERIES.items():
        try:
            results = service.users().messages().list(userId="me", q=f"({query}) newer_than:{EMAIL_LOOKBACK_DAYS}d", maxResults=10).execute()
            messages = results.get("messages", [])
            if messages: details.append(f"{platform}: {len(messages)} emails")
            for msg_ref in messages:
                if msg_ref["id"] in seen_ids: continue
                seen_ids.add(msg_ref["id"])
                try:
                    saved, detail = await _process_email(service, msg_ref, platform, user_id, extract_order_from_email, 0.5)
                    if saved: new_orders += 1; details.append(f"  \u2713 {detail}")
                    else: skipped += 1
                    synced += 1
                except Exception as e: print(f"Error: {e}"); errors += 1
        except Exception as e: print(f"Error fetching {platform}: {e}"); errors += 1

    # Pass 2: Universal catch-all
    for query_name, query in UNIVERSAL_QUERIES.items():
        try:
            results = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
            messages = results.get("messages", [])
            if messages: details.append(f"{query_name}: {len(messages)} emails")
            for msg_ref in messages:
                if msg_ref["id"] in seen_ids: continue
                seen_ids.add(msg_ref["id"])
                try:
                    msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="metadata", metadataHeaders=["Subject", "From"]).execute()
                    headers = msg.get("payload", {}).get("headers", [])
                    detected = _detect_platform(_get_header(headers, "from"), _get_header(headers, "subject"))
                    if detected == "skip": skipped += 1; continue
                    saved, detail = await _process_email(service, msg_ref, detected, user_id, extract_order_from_email, 0.6)
                    if saved: new_orders += 1; details.append(f"  \u2713 [catch-all] {detail}")
                    else: skipped += 1
                    synced += 1
                except Exception as e: print(f"Error: {e}"); errors += 1
        except Exception as e: print(f"Error in {query_name}: {e}"); errors += 1

    return {"synced": synced, "new_orders": new_orders, "skipped": skipped, "errors": errors, "details": details}
