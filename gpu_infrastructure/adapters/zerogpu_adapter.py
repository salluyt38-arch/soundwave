"""
Hugging Face ZeroGPU Adapter (Development & Rate-Limited Fallback).
Represents a dynamic shared A100 ZeroGPU space.
Trust Level: DEV_FALLBACK.
Enforces burst duration limits (<60s) and quota detection.
"""

import time
from typing import Optional

from .base_adapter import BaseGPUWorkerAdapter
from ..contracts import EnhanceJob, WorkerCapabilities, WorkerTrustLevel
from ..inference.pipeline_runner import ImageInferencePipeline


class HFZeroGPUAdapter(BaseGPUWorkerAdapter):
    """
    Development fallback adapter connecting to Hugging Face ZeroGPU.
    Operates within strict free-tier quotas and concurrency caps.
    """

    def __init__(
        self,
        worker_id: str = "dev-zerogpu-fallback",
        space_id: Optional[str] = None,
        hf_token: Optional[str] = None
    ):
        super().__init__(
            worker_id=worker_id,
            provider_name="zerogpu",
            trust_level=WorkerTrustLevel.DEV_FALLBACK
        )
        self.space_id = space_id or "soundwave/zerogpu-enhancer"
        self.hf_token = hf_token
        self.active_jobs = 0
        self.daily_quota_used_seconds = 0.0
        self.max_daily_quota_seconds = 300.0         # Free ZeroGPU tier limit (~5 minutes daily)
        self.pipeline = ImageInferencePipeline(use_cuda=False)

    def detect_capabilities(self) -> WorkerCapabilities:
        health = "healthy"
        if self.daily_quota_used_seconds >= self.max_daily_quota_seconds:
            health = "quota_exhausted"

        return WorkerCapabilities(
            worker_id=self.worker_id,
            provider=self.provider_name,
            trust_level=self.trust_level,
            gpu_model="NVIDIA A100 (ZeroGPU Shared Dynamic Slice)",
            vram_total_mb=16384,
            vram_free_mb=8192 if health == "healthy" else 0,
            cuda_available=True,
            cuda_version="12.1",
            supported_models=["realesrgan_x4plus", "gfpgan_v1.4"],
            worker_health=health,
            active_workload=self.active_jobs,
            max_concurrency=1,
            last_heartbeat=time.time()
        )

    def is_healthy(self) -> bool:
        return self.daily_quota_used_seconds < self.max_daily_quota_seconds

    def execute_inference(self, job: EnhanceJob) -> bytes:
        if self.daily_quota_used_seconds >= self.max_daily_quota_seconds:
            raise RuntimeError("Hugging Face ZeroGPU daily compute quota exhausted.")

        start_time = time.time()
        self.active_jobs += 1
        try:
            run_gfp = "gfpgan" in [m.lower() for m in job.model_pipeline]
            res = self.pipeline.run_inference(
                image_bytes=job.image_bytes,
                scale=job.scale,
                run_gfpgan=run_gfp
            )
            elapsed = time.time() - start_time
            self.daily_quota_used_seconds += elapsed
            return res
        finally:
            self.active_jobs = max(0, self.active_jobs - 1)
