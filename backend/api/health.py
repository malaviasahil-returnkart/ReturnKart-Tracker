"""Health check endpoint — GET /api/health"""
from fastapi import APIRouter
from backend.config import ENV

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "env": ENV}
