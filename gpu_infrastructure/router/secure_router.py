"""
Secure GPU Router, Priority Queue, and Failover Manager.
Enforces:
  1. Horizontal worker scaling (1 suitable GPU worker per job).
  2. Strict Security Boundaries (Personal vs Community).
  3. Priority Queue (HIGH > NORMAL > BATCH).
  4. Automatic Failover & Retry on timeout or worker error.
  5. Multi-tiered Fallback: Primary -> Secondary -> Dev Fallback -> GPU_UNAVAILABLE.
  6. Zero false promises of unlimited free availability.
"""

import heapq
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from ..contracts import (
    EnhanceJob,
    JobPriority,
    JobPrivacy,
    JobStatus,
    WorkerCapabilities,
    WorkerTrustLevel,
)
from ..adapters.base_adapter import BaseGPUWorkerAdapter

logger = logging.getLogger("gpu_infrastructure.router")


class SecureGPURouter:
    """
    Central orchestration and security gateway for GPU compute.
    """

    def __init__(self):
        self._workers: Dict[str, BaseGPUWorkerAdapter] = {}
        self._jobs: Dict[str, EnhanceJob] = {}
        # Priority queue entries: (priority_int, created_at_timestamp, job_id)
        self._queue: List[Tuple[int, float, str]] = []
        self._lock = threading.RLock()
        self._audit_log: List[Dict[str, Any]] = []

    def register_worker(self, worker: BaseGPUWorkerAdapter) -> None:
        """Registers a worker adapter into the router pool."""
        with self._lock:
            self._workers[worker.worker_id] = worker
            logger.info(f"Registered GPU Worker: {worker.worker_id} ({worker.provider_name}, {worker.trust_level.value})")

    def unregister_worker(self, worker_id: str) -> None:
        """Removes a worker from the router pool."""
        with self._lock:
            if worker_id in self._workers:
                del self._workers[worker_id]
                logger.info(f"Unregistered GPU Worker: {worker_id}")

    def submit_job(
        self,
        image_bytes: bytes,
        privacy: JobPrivacy = JobPrivacy.PERSONAL,
        priority: JobPriority = JobPriority.NORMAL,
        has_contributor_consent: bool = False,
        scale: int = 4,
        timeout_seconds: float = 45.0
    ) -> EnhanceJob:
        """
        Accepts and registers a new image enhancement job.
        Validates input at the trust boundary.
        """
        if not image_bytes or len(image_bytes) < 16:
            raise ValueError("Invalid image: Payload is empty or corrupt.")

        # Cap input size at 25MB to prevent memory exhaustion DoS
        if len(image_bytes) > 25 * 1024 * 1024:
            raise ValueError("Payload too large: Max image size is 25MB.")

        job_id = f"gpu_job_{int(time.time() * 1000)}_{len(self._jobs) + 1}"

        job = EnhanceJob(
            job_id=job_id,
            image_bytes=image_bytes,
            privacy=privacy,
            priority=priority,
            scale=scale,
            has_contributor_consent=has_contributor_consent,
            status=JobStatus.QUEUED,
            timeout_seconds=timeout_seconds,
            created_at=time.time()
        )

        with self._lock:
            self._jobs[job_id] = job
            # Push to priority queue
            heapq.heappush(self._queue, (priority.value, job.created_at, job_id))

        self._audit_log.append({
            "event": "JOB_SUBMITTED",
            "job_id": job_id,
            "privacy": privacy.value,
            "priority": priority.name,
            "timestamp": time.time()
        })

        return job

    def get_job(self, job_id: str) -> Optional[EnhanceJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def select_best_worker(self, job: EnhanceJob, excluded_worker_ids: Optional[List[str]] = None) -> Tuple[Optional[BaseGPUWorkerAdapter], str]:
        """
        Selects the single most suitable GPU worker for this job following the strict fallback ladder:
          Tier 1: Primary Trusted Self-Hosted GPU
          Tier 2: Secondary Authorized External Cloud GPU
          Tier 3: Development Hugging Face ZeroGPU (if privacy allows or dev mode)
          Tier 4: Community Kalavai Worker (ONLY IF privacy == PUBLIC_TEST AND has_contributor_consent)
        """
        excluded = set(excluded_worker_ids or [])

        # Ordered candidate tiers
        tier_primary: List[BaseGPUWorkerAdapter] = []
        tier_secondary: List[BaseGPUWorkerAdapter] = []
        tier_dev_fallback: List[BaseGPUWorkerAdapter] = []
        tier_community: List[BaseGPUWorkerAdapter] = []

        with self._lock:
            for w_id, worker in self._workers.items():
                if w_id in excluded:
                    continue

                if worker.trust_level == WorkerTrustLevel.TRUSTED_SELF_HOSTED:
                    tier_primary.append(worker)
                elif worker.trust_level == WorkerTrustLevel.TRUSTED_EXTERNAL:
                    tier_secondary.append(worker)
                elif worker.trust_level == WorkerTrustLevel.DEV_FALLBACK:
                    tier_dev_fallback.append(worker)
                elif worker.trust_level == WorkerTrustLevel.COMMUNITY:
                    tier_community.append(worker)

        # Evaluate candidate tiers in strict sequence
        reasons = []
        for tier_name, tier_workers in [
            ("Primary Self-Hosted", tier_primary),
            ("Secondary External", tier_secondary),
            ("Dev Fallback (ZeroGPU)", tier_dev_fallback),
            ("Community Pool", tier_community)
        ]:
            for worker in tier_workers:
                can_accept, reason = worker.can_accept_job(job)
                if can_accept:
                    return worker, f"Assigned to {tier_name} worker '{worker.worker_id}'"
                reasons.append(f"{worker.worker_id}: {reason}")

        diagnostic = "; ".join(reasons) if reasons else "No workers registered in pool."
        return None, f"No capable GPU worker available ({diagnostic})"

    def process_job_with_failover(self, job: EnhanceJob) -> EnhanceJob:
        """
        Executes a job with automatic failover, timeout handling, and retry logic.
        """
        excluded_workers: List[str] = []

        while job.retry_count <= job.max_retries:
            worker, reason = self.select_best_worker(job, excluded_worker_ids=excluded_workers)

            if not worker:
                # Requirement 8 & 9: If no GPU is available, return clear unavailable status.
                # Never promise unlimited free processing or guaranteed availability.
                job.status = JobStatus.GPU_UNAVAILABLE
                job.error_message = (
                    "503 GPU_UNAVAILABLE: All GPU compute workers are currently busy or offline. "
                    "Capacity is finite; please retry in a few moments."
                )
                job.completed_at = time.time()
                self._record_audit("JOB_GPU_UNAVAILABLE", job.job_id, reason)
                return job

            # Assign and start job
            job.status = JobStatus.PROCESSING
            job.assigned_worker_id = worker.worker_id
            job.started_at = time.time()
            self._record_audit("JOB_ASSIGNED", job.job_id, f"Worker: {worker.worker_id}")

            try:
                # Execute inference on worker
                result = worker.execute_inference(job)
                job.result_bytes = result
                job.status = JobStatus.COMPLETED
                job.completed_at = time.time()
                job.log_attempt(worker.worker_id, "SUCCESS")
                self._record_audit("JOB_COMPLETED", job.job_id, f"Worker: {worker.worker_id}")
                return job

            except Exception as exc:
                job.retry_count += 1
                error_detail = str(exc)
                job.log_attempt(worker.worker_id, "FAILED", error_detail)
                excluded_workers.append(worker.worker_id)
                self._record_audit("WORKER_FAILOVER", job.job_id, f"Worker {worker.worker_id} failed: {error_detail}")

                if job.retry_count > job.max_retries:
                    job.status = JobStatus.FAILED
                    job.error_message = f"Job failed after {job.retry_count} attempts. Last error: {error_detail}"
                    job.completed_at = time.time()
                    return job
                
                # Small pause before retry failover
                time.sleep(0.5)

        return job

    def _record_audit(self, event: str, job_id: str, detail: str) -> None:
        self._audit_log.append({
            "event": event,
            "job_id": job_id,
            "detail": detail,
            "timestamp": time.time()
        })
        if len(self._audit_log) > 500:
            self._audit_log.pop(0)

    def get_capacity_metrics(self) -> Dict[str, Any]:
        """
        Returns real-time capacity and telemetry for the processing dashboard.
        """
        with self._lock:
            workers_list = [w.get_capabilities().to_dict() for w in self._workers.values()]
            total_vram = sum(w["vram_total_mb"] for w in workers_list)
            free_vram = sum(w["vram_free_mb"] for w in workers_list)
            active_load = sum(w["active_workload"] for w in workers_list)
            healthy_count = sum(1 for w in workers_list if w["worker_health"] == "healthy")

            return {
                "server_timestamp": time.time(),
                "total_workers": len(self._workers),
                "healthy_workers": healthy_count,
                "total_vram_mb": total_vram,
                "free_vram_mb": free_vram,
                "active_workload": active_load,
                "queued_jobs": len(self._queue),
                "total_jobs_tracked": len(self._jobs),
                "workers": workers_list,
                "audit_events_count": len(self._audit_log)
            }
