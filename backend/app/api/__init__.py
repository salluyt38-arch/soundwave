from fastapi import APIRouter
from .colorize import router as colorize_router
from .download import router as download_router
from .enhance import router as enhance_router
from .history import router as history_router
from .restore import router as restore_router
from .upload import router as upload_router
from .upscale import router as upscale_router

api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(enhance_router)
api_router.include_router(restore_router)
api_router.include_router(upscale_router)
api_router.include_router(colorize_router)
api_router.include_router(download_router)
api_router.include_router(history_router)

__all__ = ["api_router"]
