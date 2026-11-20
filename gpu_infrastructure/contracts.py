"""
Core Data Contracts, Types, and Enums for SoundWave GPU Infrastructure.
Governs Provider-Independent GPU Workers, Security Trust Boundaries, and Job Lifecycle.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class WorkerTrustLevel(str, Enum):
    """
    Security Trust Boundaries for GPU Workers.
    Enforces that personal/private images never reach unverified community nodes.
    """
    TRUSTED_SELF_HOSTED = "trusted_self_hosted"      # Primary: Self-hosted private GPU (100% trusted)
    TRUSTED_EXTERNAL = "trusted_external"            # Secondary: Authorized external cloud GPU with mTLS
    COMMUNITY = "community"                          # Community/P2P workers (Kalavai, public test nodes)
    DEV_FALLBACK = "dev_fallback"                    # Development sandbox (ZeroGPU / CPU test)


class JobPriority(int, Enum):
    """Job queue priorities (lower integer = higher priority)."""
    HIGH = 1
    NORMAL = 2
    BATCH = 3


class JobPrivacy(str, Enum):
    """
    Data Privacy Classification.
    PERSONAL: Strictly confidential personal photos. Routed ONLY to trusted workers.
    PUBLIC_TEST: Non-sensitive benchmark / demo photos. Community workers allowed with explicit consent.
    """
    PERSONAL = "personal"
    PUBLIC_TEST = "public_test"


class JobStatus(str, Enum):
    """Lifecycle states of an image enhancement job."""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    GPU_UNAVAILABLE = "gpu_unavailable"              # Returned gracefully when no capable GPU is online


@dataclass
class WorkerCapabilities:
    """
    Real-time capability and telemetry matrix of a GPU worker.
    """
    worker_id: str
    provider: str                                    # 'self_hosted', 'gpustack', 'kalavai', 'zerogpu', 'local_sim'
    trust_level: WorkerTrustLevel
    gpu_model: str                                   # e.g., 'NVIDIA GeForce RTX 4090', 'Tesla T4', 'A100'
    vram_total_mb: int                               # Total VRAM in MB
    vram_free_mb: int                                # Free VRAM available
    cuda_available: bool                             # True if CUDA is active
    cuda_version: str                                # e.g., '12.4' or 'N/A'
    supported_models: List[str]                      # ['realesrgan_x4plus', 'gfpgan_v1.4']
    worker_health: str                               # 'healthy', 'busy', 'degraded', 'offline'
    active_workload: int = 0                         # Number of currently running jobs
    max_concurrency: int = 1                         # Horizontal scaling: normally 1 job per worker
    last_heartbeat: float = field(default_factory=time.time)

    def is_available(self, required_vram_mb: int = 2048) -> bool:
        """Determines if the worker can accept a new job."""
        return (
            self.worker_health == "healthy"
            and self.active_workload < self.max_concurrency
            and self.vram_free_mb >= required_vram_mb
            and (time.time() - self.last_heartbeat) < 60.0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "provider": self.provider,
            "trust_level": self.trust_level.value,
            "gpu_model": self.gpu_model,
            "vram_total_mb": self.vram_total_mb,
            "vram_free_mb": self.vram_free_mb,
            "cuda_available": self.cuda_available,
            "cuda_version": self.cuda_version,
            "supported_models": self.supported_models,
            "worker_health": self.worker_health,
            "active_workload": self.active_workload,
            "max_concurrency": self.max_concurrency,
            "is_available": self.is_available(),
            "heartbeat_age_sec": round(time.time() - self.last_heartbeat, 1)
        }


@dataclass
class EnhanceJob:
    """
    Complete state specification for an image enhancement task.
    """
    job_id: str
    image_bytes: bytes                               # Raw image buffer (never stored on public URLs)
    privacy: JobPrivacy = JobPrivacy.PERSONAL
    priority: JobPriority = JobPriority.NORMAL
    model_pipeline: List[str] = field(default_factory=lambda: ["realesrgan", "gfpgan"])
    scale: int = 4                                   # 2x or 4x super-resolution
    has_contributor_consent: bool = False            # Required before community workers can touch any image
    status: JobStatus = JobStatus.QUEUED
    assigned_worker_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout_seconds: float = 45.0                    # Hard timeout to prevent stuck jobs
    retry_count: int = 0
    max_retries: int = 2
    result_bytes: Optional[bytes] = None             # Enhanced image result in-memory
    error_message: Optional[str] = None
    attempts_log: List[Dict[str, Any]] = field(default_factory=list)

    def log_attempt(self, worker_id: str, status: str, detail: str = "") -> None:
        self.attempts_log.append({
            "worker_id": worker_id,
            "status": status,
            "timestamp": time.time(),
            "detail": detail
        })

    def to_summary_dict(self) -> Dict[str, Any]:
        """User-safe summary without leaking raw image bytes or internal secrets."""
        duration = None
        if self.completed_at and self.started_at:
            duration = round(self.completed_at - self.started_at, 2)

        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "privacy": self.privacy.value,
            "priority": self.priority.name,
            "models": self.model_pipeline,
            "scale": f"{self.scale}x",
            "assigned_worker": self.assigned_worker_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "duration_sec": duration,
            "has_result": self.result_bytes is not None,
            "error": self.error_message,
            "attempts": len(self.attempts_log)
        }
