"""
POST /api/upload - Multipart/form-data Image Ingestion Endpoint
"""

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from ..schemas.models import UploadResponse
from ..services.storage_service import StorageService

router = APIRouter(tags=["Upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    Accepts multipart image uploads, validates headers and dimensions,
    and returns temporary file_id and dimensions for editor initialization.
    """
    try:
        content = await file.read()
        file_id, file_path = StorageService.save_upload(content, file.filename or "upload.jpg")

        # Read dimensions
        with Image.open(file_path) as img:
            w, h = img.size

        return UploadResponse(
            file_id=file_id,
            filename=file.filename or f"{file_id}.jpg",
            width=w,
            height=h,
            file_size_bytes=len(content),
            mime_type=file.content_type or "image/jpeg",
            preview_url=f"/api/download/preview/{file_id}",
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")
