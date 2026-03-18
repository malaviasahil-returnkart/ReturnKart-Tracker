"""
RETURNKART.IN — EVIDENCE LOCKER API
Task #22: Upload, list, and delete evidence photos/videos for return disputes.

Endpoints:
  POST   /api/evidence/upload    → upload a file (base64) for an order
  GET    /api/evidence/{order_id} → list all evidence for an order
  DELETE /api/evidence/{id}       → delete a single evidence file
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import base64
import uuid

from backend.services.supabase_service import (
    save_evidence,
    get_evidence_by_order,
    delete_evidence,
    get_client,
)

router = APIRouter()

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
async def upload_evidence(request: Request):
    """
    Upload evidence for a return dispute.
    Body: { user_id, order_id, file_data (base64), file_type (mime), file_name }
    """
    body = await request.json()
    user_id = body.get("user_id")
    order_id = body.get("order_id")
    file_data = body.get("file_data")  # base64 encoded
    file_type = body.get("file_type", "image/jpeg")
    file_name = body.get("file_name", "evidence")

    if not user_id or not order_id or not file_data:
        raise HTTPException(status_code=400, detail="user_id, order_id, and file_data are required")

    if file_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file_type} not allowed")

    try:
        # Decode base64
        file_bytes = base64.b64decode(file_data)

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        file_size = len(file_bytes)

        # Generate unique path for Supabase Storage
        ext = file_type.split("/")[-1].replace("quicktime", "mov")
        storage_path = f"{user_id}/{order_id}/{uuid.uuid4().hex[:8]}.{ext}"

        # Upload to Supabase Storage
        client = get_client()
        try:
            client.storage.from_("evidence").upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": file_type}
            )
            file_url = client.storage.from_("evidence").get_public_url(storage_path)
        except Exception as storage_err:
            # Fallback: store as base64 data URI if storage bucket doesn't exist
            print(f"Storage upload failed ({storage_err}), using data URI fallback")
            file_url = f"data:{file_type};base64,{file_data[:100]}..."  # truncated for DB
            # Store full base64 as the URL (works for small files)
            file_url = f"data:{file_type};base64,{file_data}"

        # Save metadata to evidence_locker table
        result = await save_evidence(
            order_id=order_id,
            user_id=user_id,
            file_url=file_url,
            file_type=file_type,
            file_size_bytes=file_size,
        )

        return {"evidence": result, "message": "Evidence uploaded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Evidence upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{order_id}")
async def list_evidence(order_id: str, request: Request):
    """
    Get all evidence files for a specific order.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    evidence = await get_evidence_by_order(order_id, user_id)
    return {"evidence": evidence, "count": len(evidence)}


@router.delete("/{evidence_id}")
async def remove_evidence(evidence_id: str, request: Request):
    """
    Delete a single evidence file.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    await delete_evidence(evidence_id, user_id)
    return {"status": "deleted", "message": "Evidence removed"}
