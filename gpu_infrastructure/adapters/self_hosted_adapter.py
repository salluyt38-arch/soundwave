"""
Primary Self-Hosted GPU Worker Adapter.
Represents your own dedicated private infrastructure (e.g. RTX 4090 / A100 server).
Trust Level: TRUSTED_SELF_HOSTED (Authorized for Personal and Confidential images).
"""

import os
import time
from typing import List

from .base_adapter import BaseGPUWorkerAdapter
from ..contracts import EnhanceJob, WorkerCapabilities, WorkerTrustLevel
from ..inference.pipeline_runner import ImageInferencePipeline


class SelfHostedGPUAdapter(BaseGPUWorkerAdapter):
    """
    Primary worker for processing production workloads.
    """

    def __init__(
        self,
        worker_id: str = "primary-self-hosted-01",
        gpu_model: str = "NVIDIA GeForce RTX 4090",
        vram_total_mb: int = 24576,
        cuda_version: str = "12.4"
    ):
        super().__init__(
            worker_id=worker_id,
            provider_name="self_hosted",
            trust_level=WorkerTrustLevel.TRUSTED_SELF_HOSTED
        )
        self.gpu_model = gpu_model
        self.vram_total_mb = vram_total_mb
        self.cuda_version = cuda_version
        self.pipeline = ImageInferencePipeline(use_cuda=True)
        self.active_jobs = 0

    def detect_capabilities(self) -> WorkerCapabilities:
        cuda_avail = False
        vram_free = self.vram_total_mb - (self.active_jobs * 3500)

        try:
            import torch
            if torch.cuda.is_available():
                cuda_avail = True
                self.gpu_model = torch.cuda.get_device_name(0)
                # Query free memory if torch supports it
                vram_free = int(torch.cuda.mem_get_info()[0] / (1024 * 1024))
        except Exception:
            pass

        return WorkerCapabilities(
            worker_id=self.worker_id,
            provider=self.provider_name,
            trust_level=self.trust_level,
            gpu_model=self.gpu_model,
            vram_total_mb=self.vram_total_mb,
            vram_free_mb=max(0, vram_free),
            cuda_available=cuda_avail,
            cuda_version=self.cuda_version,
            supported_models=["realesrgan_x4plus", "realesrgan_x2plus", "gfpgan_v1.4"],
            worker_health="healthy",
            active_workload=self.active_jobs,
            max_concurrency=1,
            last_heartbeat=time.time()
        )

    def is_healthy(self) -> bool:
        return True

    def execute_inference(self, job: EnhanceJob) -> bytes:
        self.active_jobs += 1
        try:
            run_gfp = "gfpgan" in [m.lower() for m in job.model_pipeline]
            return self.pipeline.run_inference(
                image_bytes=job.image_bytes,
                scale=job.scale,
                run_gfpgan=run_gfp
            )
        finally:
            self.active_jobs = max(0, self.active_jobs - 1)
