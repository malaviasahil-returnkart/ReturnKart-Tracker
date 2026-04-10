"""
RETURNKART.IN — BRAND SUBMISSION SECURITY LAYER
================================================
Validates user-submitted domains before they enter the community whitelist.

Drop this file into backend/services/brand_validator.py
"""
import re
from typing import Optional, Tuple
from backend.services.brand_config import BLOCKED_BRANDS, ALLOWED_BRANDS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1: INPUT SANITIZATION — prevents injection & XSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sanitize_domain(raw: str) -> Optional[str]:
    """
    Clean and validate a domain string.
    Returns sanitized domain or None if invalid.

    Valid: "virgio.com", "https://www.virgio.com/shop", "the-souled-store.com"
    Invalid: "javascript:alert(1)", "<script>", "file:///etc/passwd"
    """
    if not raw or not isinstance(raw, str):
        return None

    domain = raw.strip().lower()

    # Strip protocol
    domain = re.sub(r'^https?://', '', domain)
    # Strip www.
    domain = re.sub(r'^www\.', '', domain)
    # Strip trailing path, query params, fragments
    domain = domain.split('/')[0].split('?')[0].split('#')[0]
    # Strip port
    domain = domain.split(':')[0]

    # Must contain at least one dot (is a real domain)
    if '.' not in domain:
        return None

    # Only allow alphanumeric, hyphens, dots
    if not re.match(r'^[a-z0-9][a-z0-9.\-]*[a-z0-9]\.[a-z]{2,10}$', domain):
        return None

    # Block dangerous TLDs and patterns
    dangerous_tlds = {'.exe', '.bat', '.cmd', '.scr', '.js', '.vbs'}
    if any(domain.endswith(tld) for tld in dangerous_tlds):
        return None

    # Max length
    if len(domain) > 100:
        return None

    return domain


def sanitize_brand_name(raw: str) -> Optional[str]:
    """
    Clean and validate a brand name.
    Strips HTML/script tags, limits length, allows only safe characters.
    """
    if not raw or not isinstance(raw, str):
        return None

    name = raw.strip()

    # Strip any HTML tags
    name = re.sub(r'<[^>]+>', '', name)
    # Strip script-like content
    name = re.sub(r'javascript:', '', name, flags=re.IGNORECASE)
    name = re.sub(r'on\w+\s*=', '', name, flags=re.IGNORECASE)

    # Only allow letters, numbers, spaces, hyphens, ampersands, dots, apostrophes
    # This covers names like "H&M", "Marks & Spencer", "Levi's", "Dr. Martens"
    if not re.match(r"^[a-zA-Z0-9\s&.\-']{1,80}$", name):
        return None

    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    if len(name) < 2 or len(name) > 80:
        return None

    return name


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2: BLOCKED BRAND CHECK — catches variants of blocked brands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_blocked_submission(domain: str, brand_name: str) -> Optional[str]:
    """
    Check if the submitted domain/name is a variant of a blocked brand.
    Returns reason string if blocked, None if clean.
    """
    domain_lower = domain.lower()
    name_lower = brand_name.lower().replace(" ", "")
    slug = domain_lower.split('.')[0]

    # Direct match
    if slug in BLOCKED_BRANDS:
        return f"'{brand_name}' is a blocked service"

    # Substring match — catches "swiggy-food", "zomato-delivery", "uber-eats"
    for blocked in BLOCKED_BRANDS:
        if blocked in slug or blocked in name_lower:
            return f"'{brand_name}' appears related to blocked brand '{blocked}'"
        if slug in blocked:
            return f"'{brand_name}' appears related to blocked brand '{blocked}'"

    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 3: PHISHING / TYPOSQUAT DETECTION — catches fake lookalike domains
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Known brand domains to protect against lookalikes
PROTECTED_DOMAINS = {
    "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho",
    "zara", "nike", "adidas", "puma", "levis", "hm",
    "tommy", "calvinklein", "ralphlauren", "gucci", "louis",
    "tanishq", "titan", "samsung", "apple", "oneplus",
    "google", "facebook", "instagram", "whatsapp", "paypal",
    "paytm", "phonepe", "razorpay",
}

# Common character substitutions used in typosquatting
TYPO_SUBSTITUTIONS = {
    'a': ['@', '4', 'á', 'à', 'â'],
    'e': ['3', 'é', 'è', 'ê'],
    'i': ['1', '!', 'í', 'ì', 'î', 'l'],
    'o': ['0', 'ó', 'ò', 'ô'],
    's': ['$', '5'],
    'l': ['1', 'i'],
    'g': ['9'],
    't': ['7'],
}


def _normalize_for_comparison(text: str) -> str:
    """Remove common typosquat substitutions to get the 'real' word."""
    result = text.lower()
    for real_char, fakes in TYPO_SUBSTITUTIONS.items():
        for fake in fakes:
            result = result.replace(fake, real_char)
    # Remove hyphens, underscores, dots within the name part
    result = re.sub(r'[\-_.]', '', result)
    return result


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Simple Levenshtein distance for short strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def check_typosquat(domain: str) -> Optional[str]:
    """
    Detect if a domain is a typosquat/lookalike of a known brand.
    Returns warning string if suspicious, None if clean.

    Catches: amaz0n.com, niike.com, flipk4rt.com, g00gle.com
    """
    slug = domain.split('.')[0]
    normalized = _normalize_for_comparison(slug)

    for protected in PROTECTED_DOMAINS:
        # Skip if it's an exact match (legitimate)
        if slug == protected:
            return None

        # Check if normalized version matches a protected brand
        if normalized == protected:
            return f"Domain '{domain}' looks like a typosquat of '{protected}'"

        # Check Levenshtein distance (catches niike, amazn, flpkart)
        if len(protected) >= 4:
            distance = _levenshtein_distance(slug, protected)
            # Allow distance of 1 only for long names, 0 for short
            max_distance = 1 if len(protected) >= 6 else 0
            if 0 < distance <= max_distance and slug != protected:
                return f"Domain '{domain}' is suspiciously similar to '{protected}' (distance: {distance})"

    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 4: RATE LIMITING — prevents spam flooding
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from datetime import datetime, timezone, timedelta
from collections import defaultdict

# In-memory rate limiter (resets on server restart — fine for MVP)
_user_submissions: dict = defaultdict(list)  # user_id → [timestamp, ...]

MAX_SUBMISSIONS_PER_HOUR = 5
MAX_SUBMISSIONS_PER_DAY = 15


def check_rate_limit(user_id: str) -> Optional[str]:
    """
    Check if a user has exceeded submission limits.
    Returns error string if rate-limited, None if allowed.
    """
    now = datetime.now(timezone.utc)
    timestamps = _user_submissions[user_id]

    # Clean old entries
    _user_submissions[user_id] = [
        ts for ts in timestamps if (now - ts).total_seconds() < 86400
    ]
    timestamps = _user_submissions[user_id]

    # Check hourly limit
    hour_ago = now - timedelta(hours=1)
    recent_hour = [ts for ts in timestamps if ts > hour_ago]
    if len(recent_hour) >= MAX_SUBMISSIONS_PER_HOUR:
        return f"Rate limit: max {MAX_SUBMISSIONS_PER_HOUR} submissions per hour"

    # Check daily limit
    if len(timestamps) >= MAX_SUBMISSIONS_PER_DAY:
        return f"Rate limit: max {MAX_SUBMISSIONS_PER_DAY} submissions per day"

    return None


def record_submission(user_id: str):
    """Record a successful submission for rate limiting."""
    _user_submissions[user_id].append(datetime.now(timezone.utc))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 5: TRUST SCORING — new users get moderated, trusted users auto-approve
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Users who have X+ successful orders tracked are "trusted"
TRUST_THRESHOLD_ORDERS = 3

async def get_user_trust_level(user_id: str, supabase) -> str:
    """
    Determine if a user is trusted based on their order history.
    Returns 'trusted' or 'new'.

    trusted = has 3+ legitimate orders → auto-approve submissions
    new = fewer orders → submissions go to 'pending' for review
    """
    try:
        result = supabase.table("orders") \
            .select("id", count="exact") \
            .eq("user_id", user_id) \
            .execute()
        order_count = result.count or 0
        return "trusted" if order_count >= TRUST_THRESHOLD_ORDERS else "new"
    except Exception:
        return "new"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 6: CONTENT FILTER — blocks offensive/inappropriate brand names
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Basic profanity/offensive terms filter (expand as needed)
_OFFENSIVE_TERMS = {
    "fuck", "shit", "ass", "dick", "porn", "xxx", "sex",
    "hack", "crack", "warez", "torrent", "pirate",
    "scam", "fraud", "phish", "malware", "virus",
    "terror", "bomb", "kill", "drug",
}

def check_content(brand_name: str, domain: str) -> Optional[str]:
    """Check for offensive or dangerous content in brand name/domain."""
    combined = (brand_name + " " + domain).lower()
    for term in _OFFENSIVE_TERMS:
        if term in combined:
            return f"Submission contains inappropriate content"
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER VALIDATION FUNCTION — runs all layers in sequence
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def validate_brand_submission(
    raw_domain: str,
    raw_brand_name: str,
    user_id: str,
    supabase,
) -> Tuple[bool, str, Optional[str], Optional[str], str]:
    """
    Run all 6 security layers on a brand submission.

    Returns: (
        is_valid: bool,
        message: str,           # error message or "ok"
        clean_domain: str,      # sanitized domain (or None)
        clean_name: str,        # sanitized brand name (or None)
        approval_status: str,   # "approved" or "pending"
    )
    """

    # Layer 1: Sanitize inputs
    clean_domain = sanitize_domain(raw_domain)
    if not clean_domain:
        return (False, "Invalid domain format. Enter a valid website like 'virgio.com'", None, None, "rejected")

    clean_name = sanitize_brand_name(raw_brand_name)
    if not clean_name:
        return (False, "Invalid brand name. Use only letters, numbers, and basic punctuation.", None, None, "rejected")

    # Layer 2: Blocked brand check
    blocked_reason = is_blocked_submission(clean_domain, clean_name)
    if blocked_reason:
        return (False, blocked_reason, None, None, "rejected")

    # Layer 3: Typosquat / phishing detection
    typo_warning = check_typosquat(clean_domain)
    if typo_warning:
        return (False, f"Rejected: {typo_warning}. If this is a legitimate brand, contact support.", None, None, "rejected")

    # Layer 4: Rate limiting
    rate_error = check_rate_limit(user_id)
    if rate_error:
        return (False, rate_error, None, None, "rejected")

    # Layer 5: Content filter
    content_error = check_content(clean_name, clean_domain)
    if content_error:
        return (False, content_error, None, None, "rejected")

    # Layer 6: Trust-based approval
    trust_level = await get_user_trust_level(user_id, supabase)
    if trust_level == "trusted":
        approval = "approved"
    else:
        approval = "pending"  # new users need manual review

    # Record the submission for rate limiting
    record_submission(user_id)

    return (True, "ok", clean_domain, clean_name, approval)
