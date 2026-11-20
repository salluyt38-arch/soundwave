"""
Kalavai Community / P2P GPU Worker Adapter.
Requirement 1: Treated as an independent infrastructure integration (NOT assumed production-ready).
Requirement 6: Strictly COMMUNITY trust level.
  - Personal images are permanently BLOCKED.
  - Only non-sensitive PUBLIC_TEST images allowed.
  - Explicit contributor consent strictly enforced.
"""

import time
from typing import Optional

from .base_adapter import BaseGPUWorkerAdapter
from ..contracts import EnhanceJob, JobPrivacy, WorkerCapabilities, WorkerTrustLevel
from ..inference.pipeline_runner import ImageInferencePipeline


class KalavaiWorkerAdapter(BaseGPUWorkerAdapter):
    """
    Adapter for decentralized / community GPU nodes managed via Kalavai pool.
    Isolated completely from personal/private production queues.
    """

    def __init__(
        self,
        worker_id: str = "kalavai-community-node-88",
        pool_endpoint: Optional[str] = None,
        gpu_model: str = "NVIDIA GeForce RTX 3080 (Community P2P)",
        vram_total_mb: int = 10240
    ):
        super().__init__(
            worker_id=worker_id,
            provider_name="kalavai",
            trust_level=WorkerTrustLevel.COMMUNITY
        )
        self.pool_endpoint = pool_endpoint or "http://kalavai-pool.internal:8000"
        self.gpu_model = gpu_model
        self.vram_total_mb = vram_total_mb
        self.active_jobs = 0
        self.pipeline = ImageInferencePipeline(use_cuda=False)

    def detect_capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self.worker_id,
            provider=self.provider_name,
            trust_level=self.trust_level,
            gpu_model=self.gpu_model,
            vram_total_mb=self.vram_total_mb,
            vram_free_mb=self.vram_total_mb - (self.active_jobs * 3000),
            cuda_available=True,
            cuda_version="12.0",
            supported_models=["realesrgan_x4plus", "gfpgan_v1.4"],
            worker_health="healthy",
            active_workload=self.active_jobs,
            max_concurrency=1,
            last_heartbeat=time.time()
        )

    def is_healthy(self) -> bool:
        return True

    def execute_inference(self, job: EnhanceJob) -> bytes:
        # Hard Security Assertion at Execution Boundary
        if job.privacy != JobPrivacy.PUBLIC_TEST:
            raise PermissionError("CRITICAL SECURITY VIOLATION: Personal image sent to Kalavai community worker!")
        if not job.has_contributor_consent:
            raise PermissionError("CONSENT VIOLATION: Contributor consent required to process on Kalavai community worker!")

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
