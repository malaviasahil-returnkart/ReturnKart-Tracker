"""
RETURNKART.IN — RETURN DEADLINE CALCULATOR
Task #14 (supporting): Pure function — no DB, no API calls.
Given order_date + brand + category → return_deadline date.

This is the heart of ReturnKart's value proposition.
Testable in complete isolation.
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

_KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
_kb_cache: Optional[dict] = None


def _load_kb() -> dict:
    global _kb_cache
    if _kb_cache is None:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            _kb_cache = json.load(f)
    return _kb_cache


def get_return_window(brand_slug: str, category: str = "Default") -> int:
    """
    Look up return window days from knowledge_base.json.
    Falls back to 'Default' category, then to fallback_policy.
    """
    kb = _load_kb()
    for platform in kb.get("platforms", []):
        if platform["brand_slug"].lower() == brand_slug.lower():
            # Try exact category match first
            for cat in platform.get("categories", []):
                if cat["category"].lower() == category.lower():
                    return cat["return_window_days"]
            # Fall back to Default category
            for cat in platform.get("categories", []):
                if cat["category"] == "Default":
                    return cat["return_window_days"]
    # Global fallback
    return kb.get("fallback_policy", {}).get("return_window_days", 7)


def calculate_return_deadline(order_date: date, brand_slug: str, category: str = "Default") -> date:
    """
    Core calculation: order_date + return_window_days = return_deadline.
    This is the date shown to the user as "last day to return".
    """
    window = get_return_window(brand_slug, category)
    return order_date + timedelta(days=window)


def days_remaining(return_deadline: date) -> int:
    """How many days left before the return window closes. Negative = expired."""
    return (return_deadline - date.today()).days


def is_urgent(return_deadline: date, threshold_days: int = 3) -> bool:
    """Is the return deadline within N days? Used to trigger urgent UI state."""
    remaining = days_remaining(return_deadline)
    return 0 <= remaining <= threshold_days


def is_expired(return_deadline: date) -> bool:
    """Has the return window already closed?"""
    return date.today() > return_deadline
