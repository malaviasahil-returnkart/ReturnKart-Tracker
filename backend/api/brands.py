"""
API routes for community brand management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.brand_validator import (
    validate_brand_submission,
    sanitize_domain,
    _slug_from_domain,
)
from backend.services.community_brands import (
    add_community_brand,
    get_all_community_brands,
)
from backend.services.supabase_service import supabase

router = APIRouter(prefix="/api/brands", tags=["brands"])


class BrandSubmission(BaseModel):
    domain: str
    brand_name: str
    user_id: str
    return_days: int = 15
    category: str = "fashion"


@router.post("/add")
async def submit_brand(body: BrandSubmission):
    if not body.domain or not body.brand_name:
        raise HTTPException(400, "Domain and brand name required")

    # Run all 6 security layers
    is_valid, message, clean_domain, clean_name, approval = \
        await validate_brand_submission(
            body.domain, body.brand_name, body.user_id, supabase
        )

    if not is_valid:
        raise HTTPException(400, message)

    # Generate slug from clean domain
    from backend.services.brand_validator import _slug_from_domain
    slug = _slug_from_domain(clean_domain)

    # Add to community whitelist
    result = await add_community_brand(
        domain=clean_domain,
        brand_name=clean_name,
        brand_slug=slug,
        user_id=body.user_id,
        return_days=body.return_days,
        category=body.category,
        status=approval,
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    # Tell user if pending moderation
    if approval == "pending":
        result["note"] = "Your submission is pending review (new accounts are moderated)"

    return result


@router.get("/community")
async def list_community_brands():
    brands = await get_all_community_brands()
    return {"brands": brands, "count": len(brands)}
```

---