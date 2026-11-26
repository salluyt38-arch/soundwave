"""
POST /api/upscale - Real-ESRGAN & SwinIR Super-Resolution Endpoint
"""

from fastapi import APIRouter, HTTPException
from ..schemas.models import JobResponse, UpscaleRequest
from ..services.enhancement_service import EnhancementService

router = APIRouter(tags=["Upscaling"])
enhancer = EnhancementService()


@router.post("/upscale", response_model=JobResponse)
async def upscale_image(request: UpscaleRequest):
    """
    Upscales image by 2x, 4x, or 8x with guided edge-preserving micro-texture detail transfer.
    """
    try:
        return enhancer.run_upscale(request)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upscaling error: {str(e)}")
