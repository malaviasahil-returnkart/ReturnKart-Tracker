"""
RETURNKART.IN — COMMUNITY BRANDS FEATURE
=========================================
Allows users to submit shopping domains not in the static whitelist.
Once submitted, the brand is auto-approved and immediately available
to ALL users' AI parsing logic.

FILES TO CREATE/MODIFY:
1. Run the SQL migration in Supabase Dashboard → SQL Editor
2. Add backend/services/community_brands.py (new)
3. Add backend/api/brands.py (new API route)
4. Modify backend/services/gmail_service.py (integrate dynamic whitelist)
5. Modify backend/main.py (register new route)
6. Add frontend component (Settings page)
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE 1: SUPABASE MIGRATION
# Run this in Supabase Dashboard → SQL Editor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPABASE_MIGRATION = """
-- Community-submitted brands whitelist
CREATE TABLE IF NOT EXISTS community_brands (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain TEXT NOT NULL,                    -- e.g. "virgio.com"
  brand_name TEXT NOT NULL,                -- e.g. "Virgio"
  brand_slug TEXT NOT NULL UNIQUE,         -- e.g. "virgio"
  submitted_by UUID,                       -- user who first added it
  status TEXT DEFAULT 'approved'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  submission_count INT DEFAULT 1,          -- how many users requested this
  return_days INT DEFAULT 15,              -- default return window
  category TEXT DEFAULT 'fashion',         -- fashion, electronics, home, etc.
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for fast lookups during email processing
CREATE INDEX idx_community_brands_slug ON community_brands(brand_slug);
CREATE INDEX idx_community_brands_domain ON community_brands(domain);
CREATE INDEX idx_community_brands_status ON community_brands(status);

-- Enable RLS
ALTER TABLE community_brands ENABLE ROW LEVEL SECURITY;

-- Anyone authenticated can read approved brands
CREATE POLICY "read_approved_brands"
  ON community_brands FOR SELECT
  USING (status = 'approved');

-- Authenticated users can insert new brands
CREATE POLICY "insert_brands"
  ON community_brands FOR INSERT
  WITH CHECK (true);
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE 2: backend/services/community_brands.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMMUNITY_BRANDS_SERVICE = '''
"""
Community Brands Service — dynamic whitelist from Supabase.
Caches approved brands in memory, refreshes every 5 minutes.
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import Optional, Set, Dict
from backend.services.supabase_service import supabase
from backend.services.brand_config import ALLOWED_BRANDS, BLOCKED_BRANDS

# ── In-memory cache ───────────────────────────────────────────────────────────
_cache: Dict[str, dict] = {}          # slug → {domain, brand_name, return_days}
_cache_keywords: Dict[str, str] = {}  # keyword → slug
_last_refresh: Optional[datetime] = None
CACHE_TTL_SECONDS = 300               # 5 minutes


def _slug_from_domain(domain: str) -> str:
    """Convert domain to a brand slug: 'www.virgio.com' → 'virgio'"""
    domain = domain.lower().strip()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\\.', '', domain)
    domain = domain.split('/')[0]        # remove path
    domain = domain.split('.')[0]        # take first part: virgio.com → virgio
    domain = re.sub(r'[^a-z0-9-]', '', domain)
    return domain


async def refresh_cache():
    """Load all approved community brands from Supabase into memory."""
    global _cache, _cache_keywords, _last_refresh
    try:
        result = supabase.table("community_brands") \\
            .select("*") \\
            .eq("status", "approved") \\
            .execute()

        new_cache = {}
        new_keywords = {}
        for row in result.data:
            slug = row["brand_slug"]
            # Skip if it's in the blocked list
            if slug in BLOCKED_BRANDS:
                continue
            new_cache[slug] = {
                "domain": row["domain"],
                "brand_name": row["brand_name"],
                "return_days": row.get("return_days", 15),
            }
            # Add keyword mappings for _guess_brand
            new_keywords[slug] = slug
            new_keywords[row["domain"].replace("www.", "")] = slug
            # Also map brand name keywords
            name_lower = row["brand_name"].lower().replace(" ", "")
            new_keywords[name_lower] = slug

        _cache = new_cache
        _cache_keywords = new_keywords
        _last_refresh = datetime.now(timezone.utc)
        print(f"[CommunityBrands] Refreshed cache: {len(new_cache)} brands")
    except Exception as e:
        print(f"[CommunityBrands] Cache refresh error: {e}")


async def _ensure_cache():
    """Refresh cache if stale or empty."""
    global _last_refresh
    if _last_refresh is None:
        await refresh_cache()
    else:
        elapsed = (datetime.now(timezone.utc) - _last_refresh).total_seconds()
        if elapsed > CACHE_TTL_SECONDS:
            await refresh_cache()


def get_community_brands() -> Set[str]:
    """Return set of all approved community brand slugs."""
    return set(_cache.keys())


def get_community_keywords() -> Dict[str, str]:
    """Return keyword→slug mapping for community brands."""
    return _cache_keywords.copy()


def get_community_return_days(slug: str) -> Optional[int]:
    """Return the return window for a community brand, or None."""
    entry = _cache.get(slug)
    return entry["return_days"] if entry else None


def is_allowed_brand(slug: str) -> bool:
    """Check if a slug is in EITHER the static whitelist or community whitelist."""
    return slug in ALLOWED_BRANDS or slug in _cache


async def add_community_brand(
    domain: str,
    brand_name: str,
    user_id: str,
    return_days: int = 15,
    category: str = "fashion",
) -> dict:
    """
    Add a new brand to the community whitelist.
    If the domain already exists, increment submission_count.
    Returns the brand record.
    """
    slug = _slug_from_domain(domain)

    # Reject if it's a known blocked brand
    if slug in BLOCKED_BRANDS:
        return {"error": f"'{brand_name}' is a blocked service (not physical products)"}

    # Check if already in static whitelist
    if slug in ALLOWED_BRANDS:
        return {"info": f"'{brand_name}' is already supported!", "slug": slug}

    # Check if already submitted by someone
    existing = supabase.table("community_brands") \\
        .select("*") \\
        .eq("brand_slug", slug) \\
        .execute()

    if existing.data:
        # Increment submission count (more users = higher trust)
        row = existing.data[0]
        supabase.table("community_brands") \\
            .update({
                "submission_count": row["submission_count"] + 1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }) \\
            .eq("id", row["id"]) \\
            .execute()
        # Refresh cache immediately
        await refresh_cache()
        return {"info": f"'{brand_name}' was already added. Upvoted!", "slug": slug}

    # Insert new brand — auto-approved
    clean_domain = re.sub(r'^https?://', '', domain.lower().strip())
    clean_domain = re.sub(r'^www\\.', '', clean_domain).split('/')[0]

    result = supabase.table("community_brands").insert({
        "domain": clean_domain,
        "brand_name": brand_name.strip(),
        "brand_slug": slug,
        "submitted_by": user_id,
        "status": "approved",
        "return_days": return_days,
        "category": category,
        "submission_count": 1,
    }).execute()

    # Refresh cache immediately so it's available for parsing
    await refresh_cache()

    print(f"[CommunityBrands] New brand added: {brand_name} ({slug}) by {user_id}")
    return {"success": f"'{brand_name}' added! It will now be tracked for all users.", "slug": slug}


async def get_all_community_brands() -> list:
    """Return all approved community brands for the frontend."""
    await _ensure_cache()
    return [
        {
            "slug": slug,
            "brand_name": info["brand_name"],
            "domain": info["domain"],
            "return_days": info["return_days"],
        }
        for slug, info in _cache.items()
    ]
'''


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE 3: backend/api/brands.py (NEW API ROUTE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API_ROUTE = '''
"""
API routes for community brand management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.community_brands import (
    add_community_brand,
    get_all_community_brands,
)

router = APIRouter(prefix="/api/brands", tags=["brands"])


class BrandSubmission(BaseModel):
    domain: str              # e.g. "virgio.com" or "https://www.virgio.com"
    brand_name: str          # e.g. "Virgio"
    user_id: str             # from auth
    return_days: int = 15
    category: str = "fashion"


@router.post("/add")
async def submit_brand(body: BrandSubmission):
    """Submit a new shopping domain to the community whitelist."""
    if not body.domain or not body.brand_name:
        raise HTTPException(status_code=400, detail="Domain and brand name are required")

    if len(body.brand_name) > 100:
        raise HTTPException(status_code=400, detail="Brand name too long")

    result = await add_community_brand(
        domain=body.domain,
        brand_name=body.brand_name,
        user_id=body.user_id,
        return_days=body.return_days,
        category=body.category,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/community")
async def list_community_brands():
    """List all approved community-submitted brands."""
    brands = await get_all_community_brands()
    return {"brands": brands, "count": len(brands)}
'''


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE 4: INTEGRATION — Changes to gmail_service.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GMAIL_SERVICE_CHANGES = '''
# Add these imports at the top of gmail_service.py:
from backend.services.community_brands import (
    _ensure_cache,
    get_community_keywords,
    is_allowed_brand,
    get_community_return_days,
)

# ── MODIFY _guess_brand() ─────────────────────────────────────────────────────
# After the static brands dict lookup, add community brand lookup:

def _guess_brand(sender: str, subject: str) -> str:
    text = (sender + " " + subject).lower()

    # 1. Check static brand keywords first (fast, in-memory)
    for keyword, slug in BRAND_KEYWORDS.items():
        if keyword in text:
            return slug

    # 2. Check community-submitted brands (cached from Supabase)
    community_kw = get_community_keywords()
    for keyword, slug in community_kw.items():
        if keyword in text:
            return slug

    return "unknown"


# ── MODIFY _process_one_email() ───────────────────────────────────────────────
# Replace the BLOCKED_BRANDS check with the whitelist approach:

async def _process_one_email(...):
    ...
    # Ensure community brands cache is fresh
    await _ensure_cache()

    brand_slug = _guess_brand(sender, subject)

    # Block known bad brands
    if brand_slug in BLOCKED_BRANDS:
        print(f"[Gmail] Blocked non-ecommerce brand: {brand_slug}")
        return None

    # ... (send to Gemini for extraction) ...

    # After Gemini extraction, check if brand is allowed
    extracted_slug = (extracted.brand or "").lower().replace(" ", "")
    if not is_allowed_brand(brand_slug) and not is_allowed_brand(extracted_slug):
        # Neither the guessed slug nor Gemini's brand is in any whitelist
        if brand_slug != "unknown":
            print(f"[Gmail] Skipped non-whitelisted brand: {brand_slug}")
            return None

    # For return deadline, check community brands too
    return_days = get_community_return_days(brand_slug)
    if return_days:
        return_deadline = order_date + timedelta(days=return_days)
    else:
        return_deadline = calculate_return_deadline(order_date, calc_slug)
    ...
'''


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE 5: MAIN.PY — Register the new route
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAIN_PY_CHANGES = '''
# Add this import in main.py:
from backend.api.brands import router as brands_router

# Register the router:
app.include_router(brands_router)
'''


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE 6: FRONTEND COMPONENT — AddBrandForm.jsx
# Add to Settings page or as a modal in the Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FRONTEND_COMPONENT = '''
import { useState } from "react";

export default function AddBrandForm({ userId }) {
  const [domain, setDomain] = useState("");
  const [brandName, setBrandName] = useState("");
  const [returnDays, setReturnDays] = useState(15);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!domain || !brandName) return;

    setLoading(true);
    setStatus(null);

    try {
      const res = await fetch("/api/brands/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain,
          brand_name: brandName,
          user_id: userId,
          return_days: returnDays,
          category: "fashion",
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setStatus({ type: "success", msg: data.success || data.info });
        setDomain("");
        setBrandName("");
      } else {
        setStatus({ type: "error", msg: data.detail || "Something went wrong" });
      }
    } catch (err) {
      setStatus({ type: "error", msg: "Network error. Please try again." });
    }
    setLoading(false);
  };

  return (
    <div style={{
      background: "#1A1A1A",
      borderRadius: "12px",
      padding: "24px",
      border: "1px solid #2A2A2A",
      maxWidth: "480px",
    }}>
      <h3 style={{
        color: "#D4AF37",
        fontSize: "16px",
        fontWeight: 600,
        marginBottom: "4px",
      }}>
        Add a Shopping Brand
      </h3>
      <p style={{
        color: "#888",
        fontSize: "13px",
        marginBottom: "20px",
      }}>
        Shop from a brand we don't track yet? Add it here and it'll work for everyone.
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "14px" }}>
          <label style={{ color: "#aaa", fontSize: "12px", display: "block", marginBottom: "4px" }}>
            Store Website
          </label>
          <input
            type="text"
            placeholder="e.g. virgio.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={{
              width: "100%",
              background: "#0A0A0A",
              border: "1px solid #333",
              borderRadius: "8px",
              padding: "10px 14px",
              color: "#fff",
              fontSize: "14px",
              outline: "none",
            }}
          />
        </div>

        <div style={{ marginBottom: "14px" }}>
          <label style={{ color: "#aaa", fontSize: "12px", display: "block", marginBottom: "4px" }}>
            Brand Name
          </label>
          <input
            type="text"
            placeholder="e.g. Virgio"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            style={{
              width: "100%",
              background: "#0A0A0A",
              border: "1px solid #333",
              borderRadius: "8px",
              padding: "10px 14px",
              color: "#fff",
              fontSize: "14px",
              outline: "none",
            }}
          />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <label style={{ color: "#aaa", fontSize: "12px", display: "block", marginBottom: "4px" }}>
            Return Window (days)
          </label>
          <input
            type="number"
            min={1}
            max={365}
            value={returnDays}
            onChange={(e) => setReturnDays(parseInt(e.target.value) || 15)}
            style={{
              width: "100px",
              background: "#0A0A0A",
              border: "1px solid #333",
              borderRadius: "8px",
              padding: "10px 14px",
              color: "#fff",
              fontSize: "14px",
              outline: "none",
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !domain || !brandName}
          style={{
            width: "100%",
            padding: "12px",
            background: loading ? "#333" : "#D4AF37",
            color: loading ? "#888" : "#0A0A0A",
            border: "none",
            borderRadius: "8px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "Adding..." : "Add Brand"}
        </button>
      </form>

      {status && (
        <div style={{
          marginTop: "14px",
          padding: "10px 14px",
          borderRadius: "8px",
          fontSize: "13px",
          background: status.type === "success" ? "#22C55E22" : "#EF444422",
          color: status.type === "success" ? "#22C55E" : "#EF4444",
          border: `1px solid ${status.type === "success" ? "#22C55E44" : "#EF444444"}`,
        }}>
          {status.msg}
        </div>
      )}
    </div>
  );
}
'''