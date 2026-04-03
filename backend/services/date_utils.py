"""
RETURNKART.IN — DATE PARSING UTILITIES

Central date parsing used by all ingestion services.
Gemini sometimes returns null or unexpected formats for order_date.
Email/SMS always have a timestamp we can use as a reliable fallback.

Priority order for every order:
  1. Gemini-extracted order_date (most accurate — date printed on the order)
  2. Email/SMS received date (the Date: header or Android timestamp)
  3. Today's date (last resort, logged as a warning)

NEVER silently default to today without trying the fallback first.
"""
import re
from datetime import date, datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

IST = timezone(timedelta(hours=5, minutes=30))

# All date formats Gemini might produce despite being told YYYY-MM-DD
GEMINI_DATE_FORMATS = [
    "%Y-%m-%d",       # Correct: 2024-11-15
    "%d-%m-%Y",       # Indian format: 15-11-2024
    "%d/%m/%Y",       # 15/11/2024
    "%m/%d/%Y",       # US format: 11/15/2024
    "%d %b %Y",       # 15 Nov 2024
    "%d %B %Y",       # 15 November 2024
    "%B %d, %Y",      # November 15, 2024
    "%b %d, %Y",      # Nov 15, 2024
    "%Y/%m/%d",       # 2024/11/15
    "%d-%b-%Y",       # 15-Nov-2024
]


def parse_gemini_date(raw: Optional[str]) -> Optional[date]:
    """
    Try to parse whatever date string Gemini returned.
    Returns a date object or None if unparseable.
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    for fmt in GEMINI_DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    # Last attempt: let Python's dateutil-style regex find YYYY-MM-DD anywhere in the string
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    print(f"[date_utils] Could not parse Gemini date: '{raw}'")
    return None


def parse_email_header_date(date_header: str) -> Optional[date]:
    """
    Parse the RFC 2822 Date: header from an email.
    e.g. 'Mon, 15 Nov 2024 10:30:00 +0530'
    Returns a date object in IST or None on failure.
    """
    if not date_header:
        return None
    try:
        dt = parsedate_to_datetime(date_header)
        return dt.astimezone(IST).date()
    except Exception:
        pass
    # Fallback: try to extract a 4-digit year and build from that
    match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", date_header)
    if match:
        try:
            return datetime.strptime(
                f"{match.group(1)} {match.group(2)} {match.group(3)}", "%d %b %Y"
            ).date()
        except ValueError:
            pass
    print(f"[date_utils] Could not parse email Date header: '{date_header}'")
    return None


def parse_epoch_ms(epoch_ms: Optional[int]) -> Optional[date]:
    """
    Convert Android epoch milliseconds timestamp to a date in IST.
    Used for SMS and WhatsApp notification timestamps.
    """
    if not epoch_ms:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000, tz=IST).date()
    except Exception:
        return None


def resolve_order_date(
    gemini_date: Optional[str],
    fallback_date: Optional[date],
    context: str = "",
) -> date:
    """
    Master resolver. Call this everywhere instead of inline fallbacks.

    Args:
        gemini_date:   The raw string Gemini returned for order_date (may be None)
        fallback_date: Reliable date from email header / SMS timestamp
        context:       Short label for logging e.g. 'amazon email 12345'

    Returns:
        A date object. Priority: Gemini date > fallback > today (with warning)
    """
    # 1. Try Gemini's extracted date
    parsed = parse_gemini_date(gemini_date)
    if parsed:
        return parsed

    # 2. Use the email/SMS received date
    if fallback_date:
        print(f"[date_utils] Using fallback date {fallback_date} for: {context}")
        return fallback_date

    # 3. Absolute last resort — today, with a warning
    today = datetime.now(IST).date()
    print(f"[date_utils] WARNING: No date found, using today {today} for: {context}")
    return today
