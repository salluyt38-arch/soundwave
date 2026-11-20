"""
Primary Self-Hosted Worker Adapter.
Represents your dedicated host hardware (Physical NVIDIA GPU or Host CPU Tensor Engine).
Trust Level: TRUSTED_SELF_HOSTED (Authorized for Personal and Confidential images).
Zero Fictional Data: Queries genuine live hardware capabilities.
"""

import logging
import time
from typing import Optional

from .base_adapter import BaseGPUWorkerAdapter
from ..contracts import EnhanceJob, WorkerCapabilities, WorkerTrustLevel
from ..hardware import detect_live_hardware
from ..inference.pipeline_runner import ImageInferencePipeline

logger = logging.getLogger("gpu_infrastructure.adapters.self_hosted")


class SelfHostedGPUAdapter(BaseGPUWorkerAdapter):
    """
    Primary worker for processing production workloads.
    Uses real hardware capability detection.
    """

    def __init__(
        self,
        worker_id: str = "primary-trusted-worker-01",
        gpu_model: Optional[str] = None,
        vram_total_mb: Optional[int] = None,
        cuda_version: Optional[str] = None,
    ):
        super().__init__(
            worker_id=worker_id,
            provider_name="self_hosted",
            trust_level=WorkerTrustLevel.TRUSTED_SELF_HOSTED,
        )
        # Query real hardware
        hw = detect_live_hardware()
        self.gpu_model = gpu_model or hw["hardware_model"]
        self.vram_total_mb = vram_total_mb or hw["vram_total_mb"]
        self.cuda_available = hw["cuda_available"]
        self.cuda_version = cuda_version or hw["cuda_version"]
        self.is_physical_gpu = hw["is_physical_gpu"]
        self.pipeline = ImageInferencePipeline(use_cuda=self.cuda_available)
        self.active_jobs = 0

    def detect_capabilities(self) -> WorkerCapabilities:
        hw = detect_live_hardware()
        # Compute free memory accounting for active jobs
        free_mb = max(0, hw["vram_free_mb"] - (self.active_jobs * 512))

        return WorkerCapabilities(
            worker_id=self.worker_id,
            provider=self.provider_name,
            trust_level=self.trust_level,
            gpu_model=hw["hardware_model"],
            vram_total_mb=hw["vram_total_mb"],
            vram_free_mb=free_mb,
            cuda_available=hw["cuda_available"],
            cuda_version=hw["cuda_version"],
            supported_models=["realesrgan_x4plus", "realesrgan_x2plus", "gfpgan_v1.4"],
            worker_health="healthy",
            active_workload=self.active_jobs,
            max_concurrency=1,
            last_heartbeat=time.time(),
        )

    def is_healthy(self) -> bool:
        return True

    def execute_inference(self, job: EnhanceJob) -> bytes:
        self.active_jobs += 1
        job.progress_percent = 25
        try:
            run_gfp = "gfpgan" in [m.lower() for m in job.model_pipeline]
            job.progress_percent = 50
            result_bytes, quality_metrics = self.pipeline.run_inference(
                image_bytes=job.image_bytes, scale=job.scale, run_gfpgan=run_gfp
            )
            job.quality_metrics = quality_metrics
            job.progress_percent = 100
            return result_bytes
        finally:
            self.active_jobs = max(0, self.active_jobs - 1)
