"""
APEX AI Photo Enhancer Pro - Pydantic Request & Response Schemas
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EnhancementType(str, Enum):
    AUTO = "auto"
    UPSCALE = "upscale"
    FACE_RESTORE = "face_restore"
    OLD_PHOTO = "old_photo"
    COLORIZE = "colorize"
    DENOISE = "denoise"
    INPAINT = "inpaint"


# --- Request Schemas ---

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    width: int
    height: int
    file_size_bytes: int
    mime_type: str
    preview_url: str


class BaseEnhanceRequest(BaseModel):
    image: Optional[str] = Field(None, description="Base64 encoded image or file_id")
    file_id: Optional[str] = Field(None, description="ID of previously uploaded image")
    scale: int = Field(4, ge=1, le=8, description="Upscale multiplier (2, 4, 8)")
    face_restore: bool = Field(True, description="Enable GFPGAN/CodeFormer facial restoration")
    face_strength: float = Field(0.85, ge=0.0, le=1.0, description="Facial restoration fidelity weight")
    denoise_strength: float = Field(0.5, ge=0.0, le=1.0, description="Denoise strength")
    color_correct: bool = Field(True, description="Optimize contrast and natural color balance")
    is_async: bool = Field(False, description="Process in background thread")


class FaceRestoreRequest(BaseModel):
    image: Optional[str] = None
    file_id: Optional[str] = None
    model_name: str = Field("codeformer", description="codeformer | gfpgan | restoreformer")
    fidelity: float = Field(0.85, ge=0.0, le=1.0, description="Fidelity control (0=highest quality, 1=highest fidelity)")
    eye_enhancement: bool = True
    skin_polish: bool = True
    lip_enhancement: bool = True


class UpscaleRequest(BaseModel):
    image: Optional[str] = None
    file_id: Optional[str] = None
    scale: int = Field(4, ge=2, le=8)
    model_name: str = Field("real-esrgan", description="real-esrgan | swinir")
    sharpen: bool = True


class OldPhotoRestoreRequest(BaseModel):
    image: Optional[str] = None
    file_id: Optional[str] = None
    remove_scratches: bool = True
    colorize: bool = False
    face_restore: bool = True
    contrast_recovery: bool = True


class ColorizeRequest(BaseModel):
    image: Optional[str] = None
    file_id: Optional[str] = None
    saturation: float = Field(1.15, ge=0.5, le=2.0)
    warmth: float = Field(1.05, ge=0.8, le=1.4)


class InpaintRequest(BaseModel):
    image: Optional[str] = None
    file_id: Optional[str] = None
    mask: str = Field(..., description="Base64 mask where white=255 indicates regions to remove/fill")
    algorithm: str = Field("lama_guided", description="lama_guided | telea | ns")


class DenoiseRequest(BaseModel):
    image: Optional[str] = None
    file_id: Optional[str] = None
    strength: float = Field(0.6, ge=0.1, le=1.0)
    preserve_texture: bool = True


# --- Response Schemas ---

class QualityMetrics(BaseModel):
    psnr_db: float
    ssim: float
    blur_score: float
    white_clipping_ratio: float
    black_clipping_ratio: float
    exposure_safe: bool
    quality_grade: str
    inference_duration_sec: float
    input_resolution: str
    output_resolution: str
    scale: str


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress_percent: int
    task_type: str
    models_used: List[str]
    input_resolution: Optional[str] = None
    output_resolution: Optional[str] = None
    created_at: float
    completed_at: Optional[float] = None
    duration_sec: Optional[float] = None
    quality_metrics: Optional[QualityMetrics] = None
    error: Optional[str] = None
    result_url: Optional[str] = None
    image: Optional[str] = None  # Base64 data URL for instant display


class ModelInfo(BaseModel):
    model_id: str
    display_name: str
    category: str
    upstream_repository: str
    license_type: str
    commercial_friendly: bool
    hardware_accelerated: bool
    supported_devices: List[str]
    description: str


class HealthStatus(BaseModel):
    status: str
    service: str
    platform_version: str
    owner: str
    device: str
    cuda_available: bool
    active_workers: int
    loaded_models: List[str]
    memory_free_mb: int
    timestamp: float
