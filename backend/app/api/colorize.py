"""
POST /api/colorize - B&W Photo Colorization Endpoint
"""

from fastapi import APIRouter, HTTPException
from ..schemas.models import ColorizeRequest, JobResponse
from ..services.enhancement_service import EnhancementService

router = APIRouter(tags=["Colorization"])
enhancer = EnhancementService()


@router.post("/colorize", response_model=JobResponse)
async def colorize_image(request: ColorizeRequest):
    """
    Colorizes monochrome photographs using luminance mapping and natural organic color priors.
    """
    try:
        return enhancer.run_colorize(request)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Colorization error: {str(e)}")
