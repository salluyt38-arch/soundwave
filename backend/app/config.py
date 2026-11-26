"""
APEX AI Photo Enhancer Pro - Global Application Configuration
"""

import os
from pathlib import Path
from typing import List

# Root project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
APP_DIR = BACKEND_DIR / "app"
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Create directories if they do not exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Hardware and Environment Detection
IS_CUDA_AVAILABLE = False
try:
    import torch
    IS_CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    IS_CUDA_AVAILABLE = False

DEVICE = "cuda" if IS_CUDA_AVAILABLE else "cpu"

# Security & Constraints
MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
ALLOWED_MIME_TYPES: List[str] = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
]
ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"]

# Image Dimension Thresholds
MAX_INPUT_DIMENSION: int = 4096
MIN_INPUT_DIMENSION: int = 16
DEFAULT_UPSCALE_MAX_DIM: int = 5120  # 5K True Ultra-HD

# Ephemeral Artifact Retention (10 Minutes)
ARTIFACT_EXPIRY_SECONDS: int = 600

# Server Config
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", 5000))
CORS_ORIGINS: List[str] = ["*"]
API_PREFIX: str = "/api"

# Platform Metadata
PLATFORM_NAME = "APEX AI Photo Enhancer Pro"
PLATFORM_VERSION = "2.4.0"
OWNER_NAME = "Sallu"
BRANDING_ACCENT = "#06b6d4"  # Cyan
