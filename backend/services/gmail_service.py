"""
RETURNKART.IN — GMAIL SERVICE
Fetch invoice/shipping emails from Gmail and extract order data using Gemini AI.

Supports 40+ Indian ecommerce platforms with broad search queries.
Excludes quick commerce (Blinkit, Zepto, Swiggy Instamart, Dunzo, BigBasket) —
those orders deliver in minutes and don't need return tracking.
"""
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

from backend.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from backend.services.supabase_service import (
    get_gmail_token,
    save_gmail_token,
    upsert_order,
)
from backend.models.order import OrderCreate

IST = timezone(timedelta(hours=5, minutes=30))

# Common subject keywords for ecommerce emails
_SUBJ = '(subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed" OR subject:"dispatched" OR subject:"out for delivery" OR subject:"arriving" OR subject:"refund" OR subject:"invoice")'

# Platforms to EXCLUDE from catch-all detection (quick commerce / food delivery)
EXCLUDED_PLATFORMS = {"swiggy", "zomato", "blinkit", "zepto", "dunzo", "bigbasket", "grofers", "instamart"}

# ==============================
# PLATFORM QUERIES — 40+ Indian ecommerce brands
# Quick commerce excluded: Blinkit, Zepto, Swiggy, Dunzo, BigBasket
# ==============================
PLATFORM_QUERIES = {
    # --- Horizontal Marketplaces ---
    "amazon":    f'(from:amazon.in OR from:amazon.com) {_SUBJ}',
    "flipkart":  f'(from:flipkart.com OR from:ekartlogistics.com) {_SUBJ}',
    "meesho":    f'(from:meesho.com) {_SUBJ}',
    "snapdeal":  f'(from:snapdeal.com) {_SUBJ}',
    "shopclues": f'(from:shopclues.com) {_SUBJ}',
    "jiomart":   f'(from:jiomart.com OR from:reliancedigital.in) {_SUBJ}',
    "tatacliq":  f'(from:tatacliq.com OR from:tataneu.com OR from:tatadigital.com) {_SUBJ}',
    "paytmmall": f'(from:paytmmall.com OR from:paytm.com) {_SUBJ}',
    "indiamart": f'(from:indiamart.com) {_SUBJ}',

    # --- Fashion & Lifestyle ---
    "myntra":    f'(from:myntra.com) {_SUBJ}',
    "ajio":      f'(from:ajio.com) {_SUBJ}',
    "nykaa":     f'(from:nykaa.com OR from:nykaafashion.com OR from:nykaamann.com) {_SUBJ}',
    "zara":      f'(from:zara.com) {_SUBJ}',
    "hm":        f'(from:hm.com OR from:email.hm.com) {_SUBJ}',
    "bewakoof":  f'(from:bewakoof.com) {_SUBJ}',
    "souledstore": f'(from:thesouledstore.com) {_SUBJ}',
    "limeroad":  f'(from:limeroad.com) {_SUBJ}',
    "koovs":     f'(from:koovs.com) {_SUBJ}',
    "urbanic":   f'(from:urbanic.com) {_SUBJ}',
    "shein":     f'(from:shein.com OR from:shein.in) {_SUBJ}',
    "trendsin":  f'(from:trends.in OR from:reliancetrends) {_SUBJ}',
    "fabindia":  f'(from:fabindia.com) {_SUBJ}',
    "westside":  f'(from:westside.com OR from:trentlimited) {_SUBJ}',
    "mango":     f'(from:mango.com) {_SUBJ}',
    "uniqlo":    f'(from:uniqlo.com) {_SUBJ}',

    # --- Electronics & Tech ---
    "croma":     f'(from:croma.com) {_SUBJ}',
    "vijaysales":f'(from:vijaysales.com) {_SUBJ}',
    "boat":      f'(from:boat-lifestyle.com OR from:boatlifestyle.com) {_SUBJ}',
    "oneplus":   f'(from:oneplus.in OR from:oneplus.com) {_SUBJ}',
    "samsung":   f'(from:samsung.com OR from:shop.samsung.com) {_SUBJ}',
    "apple":     f'(from:apple.com) {_SUBJ}',
    "mi":        f'(from:xiaomi.com OR from:mi.com OR from:store.mi.com) {_SUBJ}',
    "noise":     f'(from:gonoise.com) {_SUBJ}',
    "realme":    f'(from:realme.com OR from:buy.realme.com) {_SUBJ}',

    # --- Beauty & Health ---
    "purplle":   f'(from:purplle.com) {_SUBJ}',
    "mamaearth": f'(from:mamaearth.in) {_SUBJ}',
    "tataone":   f'(from:tata1mg.com OR from:1mg.com) {_SUBJ}',
    "pharmeasy": f'(from:pharmeasy.in) {_SUBJ}',
    "netmeds":   f'(from:netmeds.com) {_SUBJ}',

    # --- Home & Furniture ---
    "pepperfry": f'(from:pepperfry.com) {_SUBJ}',
    "urbanladder":f'(from:urbanladder.com) {_SUBJ}',
    "wakefit":   f'(from:wakefit.co) {_SUBJ}',
    "ikea":      f'(from:ikea.in OR from:ikea.com) {_SUBJ}',
    "hometown":  f'(from:hometown.in) {_SUBJ}',
    "godrej":    f'(from:godrejinterio.com) {_SUBJ}',

    # --- Eyewear & Jewellery ---
    "lenskart":  f'(from:lenskart.com) {_SUBJ}',
    "caratlane": f'(from:caratlane.com) {_SUBJ}',
    "tanishq":   f'(from:tanishq.co.in OR from:titan.co.in) {_SUBJ}',
    "bluestone": f'(from:bluestone.com) {_SUBJ}',

    # --- Sports & Outdoor ---
    "decathlon": f'(from:decathlon.in OR from:decathlon.com) {_SUBJ}',

    # --- Kids & Baby ---
    "firstcry":  f'(from:firstcry.com) {_SUBJ}',
    "hopscotch": f'(from:hopscotch.in) {_SUBJ}',

    # --- Books & Stationery ---
    "bookswagon": f'(from:bookswagon.com) {_SUBJ}',
}

# Catch-all: any ecommerce-sounding email from the last 60 days
CATCH_ALL_QUERY = '(subject:"order confirmed" OR subject:"order placed" OR subject:"your order" OR subject:"order shipped" OR subject:"has been shipped" OR subject:"has been dispatched" OR subject:"out for delivery" OR subject:"has been delivered" OR subject:"order summary" OR subject:"order receipt" OR subject:"payment received" OR subject:"invoice for your order") newer_than:60d'


def _build_credentials(token_row: dict) -> Credentials:
    return Credentials(
        token=token_row["access_token"],
        refresh_token=token_row.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_row.get("scope", "").split(),
    )


async def _refresh_if_needed(user_id: str, token_row: dict) -> Credentials:
    creds = _build_credentials(token_row)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await save_gmail_token(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry,
            scope=" ".join(creds.scopes) if creds.scopes else "",
        )
    return creds


def _decode_email_body(payload: dict) -> str:
    """Extract text body from Gmail payload. Tries plain text first, then HTML. Recursive."""
    body = ""
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        if body.strip():
            return body[:12000]

    parts = payload.get("parts", [])
    plain_text = ""
    html_text = ""
    for part in parts:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data", "")
        if mime == "text/plain" and data:
            plain_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime == "text/html" and data:
            html_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime.startswith("multipart/") and part.get("parts"):
            nested = _decode_email_body(part)
            if nested:
                plain_text = plain_text or nested

    body = plain_text or html_text
    return body[:12000]


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _detect_platform(sender: str, subject: str) -> str:
    """Auto-detect platform from sender/subject for catch-all matches.
    Returns 'skip' for quick commerce platforms that should be ignored."""
    text = (sender + " " + subject).lower()

    # Check for excluded quick commerce / food delivery first
    for excluded in EXCLUDED_PLATFORMS:
        if excluded in text:
            return "skip"

    hints = {
        "amazon": ["amazon"], "flipkart": ["flipkart", "ekart"], "myntra": ["myntra"],
        "meesho": ["meesho"], "ajio": ["ajio"], "nykaa": ["nykaa", "nykaafashion"],
        "tatacliq": ["tatacliq", "tataneu", "tata cliq"], "jiomart": ["jiomart"],
        "snapdeal": ["snapdeal"], "croma": ["croma"],
        "lenskart": ["lenskart"], "boat": ["boat-lifestyle", "boatlifestyle"],
        "pepperfry": ["pepperfry"], "urbanladder": ["urbanladder"], "bewakoof": ["bewakoof"],
        "souledstore": ["souledstore", "thesouledstore"], "purplle": ["purplle"],
        "mamaearth": ["mamaearth"], "decathlon": ["decathlon"], "ikea": ["ikea"],
        "oneplus": ["oneplus"], "samsung": ["samsung"], "apple": ["apple"],
        "xiaomi": ["xiaomi", "mi.com"], "zara": ["zara"], "hm": ["hm.com", "h&m"],
        "pharmeasy": ["pharmeasy"], "tataone": ["1mg", "tata1mg"], "netmeds": ["netmeds"],
        "caratlane": ["caratlane"], "tanishq": ["tanishq", "titan"], "bluestone": ["bluestone"],
        "wakefit": ["wakefit"], "vijaysales": ["vijaysales"], "noise": ["gonoise"],
        "shein": ["shein"], "limeroad": ["limeroad"], "realme": ["realme"],
        "paytmmall": ["paytmmall", "paytm"], "shopclues": ["shopclues"],
        "fabindia": ["fabindia"], "firstcry": ["firstcry"], "hopscotch": ["hopscotch"],
        "uniqlo": ["uniqlo"], "mango": ["mango.com"], "godrej": ["godrejinterio"],
    }
    for platform, keywords in hints.items():
        for kw in keywords:
            if kw in text:
                return platform
    return "unknown"


async def sync_gmail_orders(user_id: str, max_emails: int = 200) -> dict:
    """
    Main sync function. Searches all known platforms + catch-all.
    Excludes quick commerce platforms.
    Returns: { synced, new_orders, errors, details }
    """
    from backend.services.gemini_service import extract_order_from_email

    token_row = await get_gmail_token(user_id)
    if not token_row:
        return {"error": "Gmail not connected", "synced": 0, "new_orders": 0}

    creds = await _refresh_if_needed(user_id, token_row)
    service = build("gmail", "v1", credentials=creds)

    synced = 0
    new_orders = 0
    errors = 0
    details = []
    seen_ids = set()

    # Combine all platform queries + catch-all
    all_queries = {**PLATFORM_QUERIES, "catch_all": CATCH_ALL_QUERY}

    for platform, query in all_queries.items():
        try:
            time_query = f"({query}) newer_than:90d"
            results = (
                service.users().messages()
                .list(userId="me", q=time_query, maxResults=10)
                .execute()
            )
            messages = results.get("messages", [])
            if messages:
                details.append(f"{platform}: {len(messages)} emails")

            for msg_ref in messages:
                if msg_ref["id"] in seen_ids:
                    continue
                seen_ids.add(msg_ref["id"])

                try:
                    msg = (
                        service.users().messages()
                        .get(userId="me", id=msg_ref["id"], format="full")
                        .execute()
                    )
                    headers = msg.get("payload", {}).get("headers", [])
                    subject = _get_header(headers, "subject")
                    sender = _get_header(headers, "from")
                    date_str = _get_header(headers, "date")
                    body = _decode_email_body(msg.get("payload", {}))

                    if not body or len(body) < 50:
                        continue

                    actual_platform = platform if platform != "catch_all" else _detect_platform(sender, subject)

                    # Skip quick commerce / food delivery platforms
                    if actual_platform == "skip":
                        continue

                    email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"

                    extracted = await extract_order_from_email(email_text, actual_platform)

                    if extracted and extracted.order_id and extracted.confidence and extracted.confidence >= 0.5:
                        order = OrderCreate(
                            user_id=user_id,
                            order_id=extracted.order_id,
                            brand=extracted.brand or actual_platform.title(),
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
                        details.append(f"  \u2713 {extracted.brand}: {extracted.item_name}")

                    synced += 1

                except Exception as e:
                    print(f"Error processing email {msg_ref['id']}: {e}")
                    errors += 1

        except Exception as e:
            print(f"Error fetching {platform} emails: {e}")
            errors += 1

    return {"synced": synced, "new_orders": new_orders, "errors": errors, "details": details}
