"""
POST /api/enhance - Core Master AI Photo Enhancement Endpoint
"""

from fastapi import APIRouter, HTTPException
from ..schemas.models import BaseEnhanceRequest, JobResponse
from ..services.enhancement_service import EnhancementService

router = APIRouter(tags=["Enhancement"])
enhancer = EnhancementService()


@router.post("/enhance", response_model=JobResponse)
async def auto_enhance(request: BaseEnhanceRequest):
    """
    Executes one-click master deep AI restoration:
      - Multi-scale super-resolution (2x/4x)
      - GFPGAN / CodeFormer facial landmark restoration
      - Guided edge-preserving noise reduction (Zero halos)
      - Authentic micro-pore and organic texture preservation
    """
    try:
        return enhancer.run_auto_enhance(request)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement error: {str(e)}")
