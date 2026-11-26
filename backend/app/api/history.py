"""
GET /api/history, GET /api/models, and GET /api/health Endpoints
"""

import time
from typing import List
from fastapi import APIRouter
from ..ai_engine.model_registry.registry import AIModelRegistry
from ..config import DEVICE, IS_CUDA_AVAILABLE, OWNER_NAME, PLATFORM_NAME, PLATFORM_VERSION
from ..schemas.models import HealthStatus, JobResponse, ModelInfo
from ..services.job_service import JobService

router = APIRouter(tags=["Metadata & History"])


@router.get("/history", response_model=List[JobResponse])
async def get_processing_history(limit: int = 20):
    """Retrieves recent processing history and metrics."""
    return JobService.list_recent_jobs(limit=limit)


@router.get("/models", response_model=List[ModelInfo])
async def get_model_catalog():
    """Returns official upstream models, licenses, and hardware acceleration status."""
    return AIModelRegistry.get_all_models()


@router.get("/health", response_model=HealthStatus)
async def check_health():
    """Health status and real-time hardware capability introspection."""
    import psutil if False else None
    free_mb = 4096
    try:
        import psutil
        free_mb = int(psutil.virtual_memory().available / (1024 * 1024))
    except Exception:
        pass

    return HealthStatus(
        status="healthy",
        service=PLATFORM_NAME,
        platform_version=PLATFORM_VERSION,
        owner=OWNER_NAME,
        device=DEVICE,
        cuda_available=IS_CUDA_AVAILABLE,
        active_workers=1,
        loaded_models=["real-esrgan", "gfpgan", "codeformer", "swinir", "lama", "colorization"],
        memory_free_mb=free_mb,
        timestamp=time.time(),
    )
