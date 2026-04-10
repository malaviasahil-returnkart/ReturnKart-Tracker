import re
from datetime import datetime, timezone
from typing import Optional, Dict
from backend.services.supabase_service import get_client

_cache = {}
_cache_keywords = {}
_last_refresh = None
CACHE_TTL_SECONDS = 300

def _slug_from_domain(domain):
    domain = domain.lower().strip()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www[.]", "", domain)
    domain = domain.split("/")[0].split(".")[0]
    domain = re.sub(r"[^a-z0-9-]", "", domain)
    return domain

async def refresh_cache():
    global _cache, _cache_keywords, _last_refresh
    try:
        result = get_client().table("community_brands").select("*").eq("status", "approved").execute()
        new_cache = {}
        new_keywords = {}
        for row in result.data:
            slug = row["brand_slug"]
            new_cache[slug] = {"domain": row["domain"], "brand_name": row["brand_name"], "return_days": row.get("return_days", 15)}
            new_keywords[slug] = slug
            new_keywords[row["domain"].replace("www.", "")] = slug
            new_keywords[row["brand_name"].lower().replace(" ", "")] = slug
        _cache = new_cache
        _cache_keywords = new_keywords
        _last_refresh = datetime.now(timezone.utc)
        print(f"[CommunityBrands] Refreshed: {len(new_cache)} brands")
    except Exception as e:
        print(f"[CommunityBrands] Cache refresh error: {e}")

async def _ensure_cache():
    global _last_refresh
    if _last_refresh is None:
        await refresh_cache()
    else:
        elapsed = (datetime.now(timezone.utc) - _last_refresh).total_seconds()
        if elapsed > CACHE_TTL_SECONDS:
            await refresh_cache()

def get_community_keywords():
    return _cache_keywords.copy()

def get_community_return_days(slug):
    entry = _cache.get(slug)
    return entry["return_days"] if entry else None

def is_in_community_whitelist(slug):
    return slug in _cache

async def add_community_brand(domain, brand_name, brand_slug, user_id, return_days=15, category="fashion", status="approved"):
    existing = get_client().table("community_brands").select("*").eq("brand_slug", brand_slug).execute()
    if existing.data:
        row = existing.data[0]
        get_client().table("community_brands").update({"submission_count": row["submission_count"] + 1, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", row["id"]).execute()
        await refresh_cache()
        return {"info": f"Brand already added. Upvoted!", "slug": brand_slug}
    clean_domain = re.sub(r"^https?://", "", domain.lower().strip())
    clean_domain = re.sub(r"^www[.]", "", clean_domain).split("/")[0]
    get_client().table("community_brands").insert({"domain": clean_domain, "brand_name": brand_name.strip(), "brand_slug": brand_slug, "submitted_by": user_id, "status": status, "return_days": return_days, "category": category, "submission_count": 1}).execute()
    await refresh_cache()
    print(f"[CommunityBrands] Added: {brand_name} ({brand_slug}) by {user_id}")
    return {"success": f"Brand added! Now tracked for all users.", "slug": brand_slug}

async def get_all_community_brands():
    await _ensure_cache()
    return [{"slug": s, "brand_name": i["brand_name"], "domain": i["domain"], "return_days": i["return_days"]} for s, i in _cache.items()]
