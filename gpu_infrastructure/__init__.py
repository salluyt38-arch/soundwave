"""
SoundWave Production GPU Infrastructure Package.
Orchestrates Provider-Independent Workers, Security Routing, Real-ESRGAN/GFPGAN Pipelines,
Capacity Monitoring, and Fallbacks.
"""

import os
from typing import Optional

from .contracts import (
    EnhanceJob,
    JobPriority,
    JobPrivacy,
    JobStatus,
    WorkerCapabilities,
    WorkerTrustLevel,
)
from .router.secure_router import SecureGPURouter
from .adapters.self_hosted_adapter import SelfHostedGPUAdapter
from .adapters.external_gpu_adapter import ExternalGPUAdapter
from .adapters.zerogpu_adapter import HFZeroGPUAdapter
from .adapters.kalavai_adapter import KalavaiWorkerAdapter
from .adapters.gpustack_adapter import GPUStackWorkerAdapter
from .dashboard.capacity_dashboard import CapacityDashboardRenderer

_default_router: Optional[SecureGPURouter] = None


def get_gpu_router() -> SecureGPURouter:
    """
    Returns the singleton router initialized with the appropriate workers
    based on the active environment configuration.
    """
    global _default_router
    if _default_router is not None:
        return _default_router

    router = SecureGPURouter()

    # 1. Primary Worker
    primary_worker = SelfHostedGPUAdapter(
        worker_id="primary-trusted-gpu-01",
        gpu_model=os.environ.get("PRIMARY_GPU_MODEL", "NVIDIA GeForce RTX 4090"),
        vram_total_mb=int(os.environ.get("PRIMARY_VRAM_MB", 24576))
    )
    router.register_worker(primary_worker)

    # 2. Secondary Cloud Worker (Failover)
    if os.environ.get("ENABLE_SECONDARY_CLOUD_WORKER", "true").lower() == "true":
        secondary_worker = ExternalGPUAdapter(
            worker_id="secondary-cloud-failover-01",
            gpu_model=os.environ.get("SECONDARY_GPU_MODEL", "NVIDIA A10G Cloud"),
            vram_total_mb=int(os.environ.get("SECONDARY_VRAM_MB", 24000))
        )
        router.register_worker(secondary_worker)

    # 3. Dev ZeroGPU Fallback
    if os.environ.get("ZERO_GPU_FALLBACK", "false").lower() == "true":
        zerogpu_worker = HFZeroGPUAdapter(worker_id="dev-zerogpu-fallback")
        router.register_worker(zerogpu_worker)

    # 4. Community Kalavai Node (Isolated for Public Test Images only)
    if os.environ.get("ENABLE_COMMUNITY_WORKERS", "false").lower() == "true":
        kalavai_worker = KalavaiWorkerAdapter(worker_id="kalavai-community-01")
        router.register_worker(kalavai_worker)

    # 5. GPUStack Integration
    if os.environ.get("ENABLE_GPUSTACK_INTEGRATION", "false").lower() == "true":
        gpustack_worker = GPUStackWorkerAdapter(worker_id="gpustack-cluster-01")
        router.register_worker(gpustack_worker)

    _default_router = router
    return _default_router
