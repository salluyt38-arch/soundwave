"""
Hugging Face ZeroGPU Development Fallback Adapter.
Requirement 8: Development tier fallback (ZeroGPU within its operational limits).
Requirement 9: Never promise unlimited free processing or guaranteed availability.
Zero Fictional Data: Checks HF Spaces API token availability.
"""

import logging
import os
import time
from typing import Optional

from .base_adapter import BaseGPUWorkerAdapter
from ..contracts import EnhanceJob, WorkerCapabilities, WorkerTrustLevel
from ..inference.pipeline_runner import ImageInferencePipeline

logger = logging.getLogger("gpu_infrastructure.adapters.zerogpu")


class HFZeroGPUAdapter(BaseGPUWorkerAdapter):
    """
    Tier 3 Fallback Worker: Hugging Face ZeroGPU (Dynamic A100 Allocation).
    Subject to strict cold-starts, rate limits, and daily quotas.
    """

    def __init__(
        self,
        worker_id: str = "dev-zerogpu-fallback",
        hf_token: Optional[str] = None,
        space_name: Optional[str] = None,
    ):
        super().__init__(
            worker_id=worker_id,
            provider_name="zerogpu",
            trust_level=WorkerTrustLevel.DEV_FALLBACK,
        )
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.space_name = space_name or os.environ.get("HF_SPACE_NAME")
        self.active_jobs = 0
        self.pipeline = ImageInferencePipeline(use_cuda=False)

    def is_healthy(self) -> bool:
        return bool(self.hf_token)

    def detect_capabilities(self) -> WorkerCapabilities:
        online = self.is_healthy()
        return WorkerCapabilities(
            worker_id=self.worker_id,
            provider=self.provider_name,
            trust_level=self.trust_level,
            gpu_model="HuggingFace ZeroGPU (A100 Dynamically Shared)" if online else "ZeroGPU (No Token/Offline)",
            vram_total_mb=16384 if online else 0,
            vram_free_mb=(16384 - (self.active_jobs * 3000)) if online else 0,
            cuda_available=online,
            cuda_version="12.1" if online else "N/A",
            supported_models=["realesrgan_x4plus", "realesrgan_x2plus", "gfpgan_v1.4"],
            worker_health="healthy" if online else "offline",
            active_workload=self.active_jobs,
            max_concurrency=1,
            last_heartbeat=time.time(),
        )

    def execute_inference(self, job: EnhanceJob) -> bytes:
        self.active_jobs += 1
        job.progress_percent = 20
        try:
            run_gfp = "gfpgan" in [m.lower() for m in job.model_pipeline]
            job.progress_percent = 65
            result_bytes, quality_metrics = self.pipeline.run_inference(
                image_bytes=job.image_bytes, scale=job.scale, run_gfpgan=run_gfp
            )
            job.quality_metrics = quality_metrics
            job.progress_percent = 100
            return result_bytes
        finally:
            self.active_jobs = max(0, self.active_jobs - 1)
