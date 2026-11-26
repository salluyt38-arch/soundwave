"""
APEX AI Photo Enhancer Pro - FastAPI Application Master Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import api_router
from .config import (
    API_PREFIX,
    BASE_DIR,
    CORS_ORIGINS,
    PLATFORM_NAME,
    PLATFORM_VERSION,
)
from .services.storage_service import StorageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Cleanup any stale expired artifacts
    StorageService.cleanup_expired_artifacts()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=PLATFORM_NAME,
    version=PLATFORM_VERSION,
    description="Professional Remini-Inspired AI Photo Restoration & Enhancement Platform",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include All REST API Routes
app.include_router(api_router, prefix=API_PREFIX)

# Mount Static Frontend
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    from .config import HOST, PORT
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=True)
