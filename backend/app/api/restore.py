"""
POST /api/face-restore & POST /api/old-photo-restore Endpoints
"""

from fastapi import APIRouter, HTTPException
from ..schemas.models import FaceRestoreRequest, JobResponse, OldPhotoRestoreRequest
from ..services.enhancement_service import EnhancementService

router = APIRouter(tags=["Restoration"])
enhancer = EnhancementService()


@router.post("/face-restore", response_model=JobResponse)
async def restore_faces(request: FaceRestoreRequest):
    """
    Executes dedicated GFPGAN / CodeFormer facial reconstruction with controllable fidelity slider.
    """
    try:
        return enhancer.run_face_restore(request)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face restoration error: {str(e)}")


@router.post("/old-photo-restore", response_model=JobResponse)
async def restore_old_photos(request: OldPhotoRestoreRequest):
    """
    Restores vintage, damaged, scratched, or faded historical photographs.
    """
    try:
        return enhancer.run_old_photo_restore(request)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Old photo restoration error: {str(e)}")
