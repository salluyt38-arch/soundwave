"""
Base Abstract GPU Worker Adapter.
Provides a unified, provider-independent interface for all GPU infrastructures:
  - Self-Hosted Private GPUs
  - Authorized External Cloud GPUs
  - Hugging Face ZeroGPU (Dev/Fallback)
  - GPUStack (Cluster Manager)
  - Kalavai (Community / P2P Worker Pool)
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import time

from ..contracts import EnhanceJob, JobPrivacy, WorkerCapabilities, WorkerTrustLevel


class BaseGPUWorkerAdapter(ABC):
    """
    Abstract contract that all GPU worker providers must implement.
    Decouples GPU infrastructure implementations from scheduling and business logic.
    """

    def __init__(self, worker_id: str, provider_name: str, trust_level: WorkerTrustLevel):
        self.worker_id = worker_id
        self.provider_name = provider_name
        self.trust_level = trust_level
        self._capabilities: Optional[WorkerCapabilities] = None

    @abstractmethod
    def detect_capabilities(self) -> WorkerCapabilities:
        """
        Polls or introspects hardware capabilities:
        GPU Model, VRAM (Total/Free), CUDA support, pre-loaded models, and active load.
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Checks if the worker is reachable, responsive, and ready for work."""
        pass

    @abstractmethod
    def execute_inference(self, job: EnhanceJob) -> bytes:
        """
        Runs the actual enhancement job on this worker.
        Returns the enhanced image bytes or raises an Exception.
        """
        pass

    def can_accept_job(self, job: EnhanceJob) -> Tuple[bool, str]:
        """
        Strict capability and security check before assigning a job to this worker:
          1. Security boundary: Personal images MUST NOT go to community workers.
          2. Explicit consent: Required if using community workers even for test images.
          3. Model requirements: Worker must support requested models (Real-ESRGAN, GFPGAN).
          4. Workload: Worker must have an available execution slot.
          5. Health: Worker must be healthy and not timed out.
        """
        caps = self.get_capabilities()

        # 1. Security Check: Personal Image Protection
        if job.privacy == JobPrivacy.PERSONAL and self.trust_level == WorkerTrustLevel.COMMUNITY:
            return False, f"SECURITY REJECT: Personal images cannot be routed to community worker '{self.worker_id}'."

        # 2. Security Check: Contributor Consent for Community Workers
        if self.trust_level == WorkerTrustLevel.COMMUNITY and not job.has_contributor_consent:
            return False, f"CONSENT REQUIRED: Explicit contributor consent needed for community worker '{self.worker_id}'."

        # 3. Health & Heartbeat
        if caps.worker_health != "healthy":
            return False, f"Worker '{self.worker_id}' is currently {caps.worker_health}."

        if (time.time() - caps.last_heartbeat) > 60.0:
            return False, f"Worker '{self.worker_id}' heartbeat timed out."

        # 4. Workload Concurrency (Horizontal scaling: normally 1 job per worker)
        if caps.active_workload >= caps.max_concurrency:
            return False, f"Worker '{self.worker_id}' is at full capacity ({caps.active_workload}/{caps.max_concurrency})."

        # 5. Model Availability
        for required_model in job.model_pipeline:
            # Match model prefix (e.g. 'realesrgan', 'gfpgan')
            model_matched = any(required_model in m.lower() for m in caps.supported_models)
            if not model_matched:
                return False, f"Worker '{self.worker_id}' does not have model '{required_model}' loaded."

        return True, "OK"

    def get_capabilities(self, force_refresh: bool = False) -> WorkerCapabilities:
        """Returns cached capabilities or refreshes if older than 15 seconds."""
        if (
            self._capabilities is None
            or force_refresh
            or (time.time() - self._capabilities.last_heartbeat) > 15.0
        ):
            self._capabilities = self.detect_capabilities()
        return self._capabilities
