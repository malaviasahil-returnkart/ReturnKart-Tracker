"""
RETURNKART.IN — GMAIL SERVICE
Fetch invoice/shipping emails from Gmail and extract order data using Gemini AI.

STRATEGY:
  1. Brand-specific queries for top 80+ known platforms (fast, accurate)
  2. UNIVERSAL catch-all that searches ANY email by ecommerce keywords
     regardless of sender domain — catches every platform including
     ones we haven't listed, subdomains, and third-party email services
  3. Gemini AI + confidence score (>=0.5) filters out non-ecommerce junk

Excludes quick commerce (Blinkit, Zepto, Swiggy, Dunzo, BigBasket, Zomato).
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

# Subject filter for marketplaces
_SUBJ = '(subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed" OR subject:"dispatched" OR subject:"out for delivery" OR subject:"arriving" OR subject:"refund" OR subject:"invoice")'

# Broader subject filter for fashion brands
_SUBJ_BROAD = '(subject:"order" OR subject:"shipped" OR subject:"delivered" OR subject:"confirmed" OR subject:"placed" OR subject:"dispatched" OR subject:"out for delivery" OR subject:"arriving" OR subject:"refund" OR subject:"invoice" OR subject:"receipt" OR subject:"purchase" OR subject:"thank you" OR subject:"your package" OR subject:"your parcel" OR subject:"on its way" OR subject:"delivery" OR subject:"tracking" OR subject:"shopping")'

# Platforms to EXCLUDE (quick commerce / food delivery)
EXCLUDED_PLATFORMS = {"swiggy", "zomato", "blinkit", "zepto", "dunzo", "bigbasket", "grofers", "instamart", "uber eats", "ubereats", "dominos", "pizzahut"}

# ═══════════════════════════════════════════════════
# UNIVERSAL CATCH-ALL QUERIES
# These search ANY email regardless of sender domain
# ═══════════════════════════════════════════════════
UNIVERSAL_QUERIES = {
    # Catch-all 1: Order lifecycle keywords (strongest signal)
    "universal_orders": '(subject:"order confirmed" OR subject:"order placed" OR subject:"your order" OR subject:"order shipped" OR subject:"order dispatched" OR subject:"order delivered" OR subject:"order summary" OR subject:"order receipt" OR subject:"order details") newer_than:90d',

    # Catch-all 2: Shipping/delivery keywords (catches non-standard subjects)
    "universal_shipping": '(subject:"has been shipped" OR subject:"has been dispatched" OR subject:"out for delivery" OR subject:"has been delivered" OR subject:"is on its way" OR subject:"your package" OR subject:"your parcel" OR subject:"shipment update" OR subject:"delivery update" OR subject:"tracking number") newer_than:90d',

    # Catch-all 3: Purchase/payment keywords (catches receipts)
    "universal_purchase": '(subject:"thank you for your purchase" OR subject:"payment received" OR subject:"payment confirmed" OR subject:"invoice for your order" OR subject:"your receipt" OR subject:"purchase confirmation" OR subject:"thank you for shopping" OR subject:"thank you for ordering") newer_than:90d',
}

# ═══════════════════════════════════════════════════
# BRAND-SPECIFIC QUERIES — Fast first pass for known brands
# These run first for speed and accuracy
# ═══════════════════════════════════════════════════
PLATFORM_QUERIES = {
    # Horizontal Marketplaces
    "amazon":    f'(from:amazon.in OR from:amazon.com) {_SUBJ}',
    "flipkart":  f'(from:flipkart.com OR from:ekartlogistics.com) {_SUBJ}',
    "meesho":    f'(from:meesho.com) {_SUBJ}',
    "snapdeal":  f'(from:snapdeal.com) {_SUBJ}',
    "jiomart":   f'(from:jiomart.com OR from:reliancedigital.in) {_SUBJ}',
    "tatacliq":  f'(from:tatacliq.com OR from:tataneu.com) {_SUBJ}',

    # Fashion — Tier 1 Indian
    "myntra":       f'(from:myntra.com) {_SUBJ_BROAD}',
    "ajio":         f'(from:ajio.com) {_SUBJ_BROAD}',
    "nykaa":        f'(from:nykaa.com OR from:nykaafashion.com) {_SUBJ_BROAD}',
    "shoppersstop": f'(from:shoppersstop.com) {_SUBJ_BROAD}',

    # Fashion — International (with known subdomains)
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
    """Extract text body from Gmail payload. Recursive multipart support."""
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
    """Auto-detect platform from sender/subject.
    Returns 'skip' for excluded platforms (quick commerce, food delivery)."""
    text = (sender + " " + subject).lower()

    # Check exclusions first
    for excluded in EXCLUDED_PLATFORMS:
        if excluded in text:
            return "skip"

    # Comprehensive brand detection
    hints = {
        # Marketplaces
        "amazon": ["amazon"], "flipkart": ["flipkart", "ekart"], "meesho": ["meesho"],
        "snapdeal": ["snapdeal"], "jiomart": ["jiomart"], "paytmmall": ["paytmmall", "paytm"],
        "tatacliq": ["tatacliq", "tataneu", "tata cliq"], "shopclues": ["shopclues"],
        # Fashion — Indian
        "myntra": ["myntra"], "ajio": ["ajio"], "nykaa": ["nykaa", "nykaafashion"],
        "shoppersstop": ["shoppersstop"], "lifestylestores": ["lifestylestores"],
        "maxfashion": ["maxfashion"], "pantaloons": ["pantaloons"],
        "trendsin": ["trends.in", "reliancetrends"], "westside": ["westside"],
        "fabindia": ["fabindia"],
        # Fashion — International
        "zara": ["zara"], "hm": ["hm.com", "h&m", "delivery.hm"], "uniqlo": ["uniqlo"],
        "mango": ["mango.com"], "gap": ["gap.com", "oldnavy"],
        "forever21": ["forever21"], "tommyhilfiger": ["tommy.com", "tommyhilfiger", "tommy.in", "pvhcorp"],
        "calvinklein": ["calvinklein", "pvhcorp"], "levis": ["levi.in", "levi.com", "levis", "levistrauss"],
        "nike": ["nike.com", "nike.in"], "adidas": ["adidas"], "puma": ["puma.com", "puma.in"],
        "reebok": ["reebok"], "superdry": ["superdry"],
        "marksandspencer": ["marksandspencer", "m-s.com"], "uspa": ["uspoloassn"],
        "benetton": ["benetton"], "guess": ["guess.in", "guess.com"],
        "hugoboss": ["hugoboss", "boss.com"], "ralphlauren": ["ralphlauren"],
        "coach": ["coach.com"], "michaelkors": ["michaelkors"],
        "charlesandkeith": ["charleskeith"], "aldo": ["aldoshoes"],
        "stevemadden": ["stevemadden"], "skechers": ["skechers"],
        "crocs": ["crocs"], "clarks": ["clarks"], "asics": ["asics"],
        "newbalance": ["newbalance"], "underarmour": ["underarmour"],
        "lacoste": ["lacoste"], "armani": ["armani"], "versace": ["versace"],
        "burberry": ["burberry"], "gucci": ["gucci"],
        # Fashion — D2C
        "bewakoof": ["bewakoof"], "souledstore": ["souledstore", "thesouledstore"],
        "urbanic": ["urbanic"], "shein": ["shein"], "limeroad": ["limeroad"],
        "snitch": ["snitch.co"], "rare_rabbit": ["houseofrare", "rarerabbit"],
        "libas": ["libas.in"], "biba": ["biba.in"], "clovia": ["clovia"],
        "zivame": ["zivame"], "fablestreet": ["fablestreet"],
        "allen_solly": ["allensolly"], "van_heusen": ["vanheusen"],
        "peter_england": ["peterengland"], "raymond": ["raymond"],
        "mufti": ["muftijeans"], "jack_jones": ["jackjones"],
        "woodland": ["woodland"], "bata": ["bata"], "metro_shoes": ["metroshoes"],
        # Luxury
        "aza": ["azafashions"], "pernia": ["perniaspopupshop"],
        # Electronics
        "croma": ["croma"], "boat": ["boat-lifestyle", "boatlifestyle"],
        "oneplus": ["oneplus"], "samsung": ["samsung"], "apple": ["apple.com"],
        "xiaomi": ["xiaomi", "mi.com"], "noise": ["gonoise"], "realme": ["realme"],
        "vijaysales": ["vijaysales"],
        # Beauty
        "purplle": ["purplle"], "mamaearth": ["mamaearth"],
        "pharmeasy": ["pharmeasy"], "tataone": ["1mg", "tata1mg"], "netmeds": ["netmeds"],
        # Home
        "pepperfry": ["pepperfry"], "urbanladder": ["urbanladder"],
        "ikea": ["ikea"], "wakefit": ["wakefit"], "godrej": ["godrejinterio"],
        # Jewellery & Eyewear
        "lenskart": ["lenskart"], "caratlane": ["caratlane"],
        "tanishq": ["tanishq"], "titan": ["titan.co"], "bluestone": ["bluestone"],
        # Others
        "decathlon": ["decathlon"], "firstcry": ["firstcry"], "hopscotch": ["hopscotch"],
        "fossil": ["fossil"], "fastrack": ["fastrack"],
    }
    for platform, keywords in hints.items():
        for kw in keywords:
            if kw in text:
                return platform
    return "unknown"


async def sync_gmail_orders(user_id: str, max_emails: int = 200) -> dict:
    """
    Main sync function. Two-pass strategy:
      Pass 1: Brand-specific queries for known platforms (fast, targeted)
      Pass 2: Universal catch-all queries by subject keywords only (catches everything else)
    
    Gemini AI extracts order data. Confidence >= 0.5 required to save.
    Excluded platforms (quick commerce) are skipped.
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

    # Pass 1: Brand-specific queries (fast, targeted — known domains)
    for platform, query in PLATFORM_QUERIES.items():
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
                    msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
                    headers = msg.get("payload", {}).get("headers", [])
                    subject = _get_header(headers, "subject")
                    sender = _get_header(headers, "from")
                    date_str = _get_header(headers, "date")
                    body = _decode_email_body(msg.get("payload", {}))

                    if not body or len(body) < 50:
                        continue

                    email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"
                    extracted = await extract_order_from_email(email_text, platform)

                    if extracted and extracted.order_id and extracted.confidence and extracted.confidence >= 0.5:
                        order = OrderCreate(
                            user_id=user_id,
                            order_id=extracted.order_id,
                            brand=extracted.brand or platform.title(),
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

    # Pass 2: Universal catch-all queries (no domain filter — catches EVERYTHING)
    for query_name, query in UNIVERSAL_QUERIES.items():
        try:
            results = (
                service.users().messages()
                .list(userId="me", q=query, maxResults=20)
                .execute()
            )
            messages = results.get("messages", [])
            if messages:
                details.append(f"{query_name}: {len(messages)} emails")

            for msg_ref in messages:
                if msg_ref["id"] in seen_ids:
                    continue
                seen_ids.add(msg_ref["id"])

                try:
                    msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
                    headers = msg.get("payload", {}).get("headers", [])
                    subject = _get_header(headers, "subject")
                    sender = _get_header(headers, "from")
                    date_str = _get_header(headers, "date")
                    body = _decode_email_body(msg.get("payload", {}))

                    if not body or len(body) < 50:
                        continue

                    # Auto-detect platform from sender/subject
                    detected_platform = _detect_platform(sender, subject)

                    # Skip excluded platforms (quick commerce, food delivery)
                    if detected_platform == "skip":
                        continue

                    email_text = f"Subject: {subject}\nFrom: {sender}\nDate: {date_str}\n\n{body}"
                    extracted = await extract_order_from_email(email_text, detected_platform)

                    # Higher confidence threshold for universal catch-all (0.6 vs 0.5)
                    # to reduce false positives from non-ecommerce emails
                    if extracted and extracted.order_id and extracted.confidence and extracted.confidence >= 0.6:
                        order = OrderCreate(
                            user_id=user_id,
                            order_id=extracted.order_id,
                            brand=extracted.brand or detected_platform.title(),
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
                        details.append(f"  \u2713 [catch-all] {extracted.brand}: {extracted.item_name}")

                    synced += 1
                except Exception as e:
                    print(f"Error processing catch-all email {msg_ref['id']}: {e}")
                    errors += 1
        except Exception as e:
            print(f"Error in {query_name}: {e}")
            errors += 1

    return {"synced": synced, "new_orders": new_orders, "errors": errors, "details": details}
