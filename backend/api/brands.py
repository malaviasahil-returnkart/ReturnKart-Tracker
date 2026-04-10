from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.community_brands import (
    add_community_brand,
    get_all_community_brands,
    _slug_from_domain,
)

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
    if len(body.brand_name) > 100:
        raise HTTPException(400, "Brand name too long")
    slug = _slug_from_domain(body.domain)
    result = await add_community_brand(
        domain=body.domain,
        brand_name=body.brand_name,
        brand_slug=slug,
        user_id=body.user_id,
        return_days=body.return_days,
        category=body.category,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/community")
async def list_community_brands():
    brands = await get_all_community_brands()
    return {"brands": brands, "count": len(brands)}
