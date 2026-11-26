"""
APEX Job Tracking & Queue Management Service
Tracks job state, progress percentage, quality metrics, and results.
"""

import threading
import time
import uuid
from typing import Dict, List, Optional
from ..schemas.models import JobResponse, JobStatus, QualityMetrics


class JobService:
    """
    Thread-safe job manager for tracking real-time inference lifecycle.
    """

    _jobs: Dict[str, JobResponse] = {}
    _lock = threading.Lock()

    @classmethod
    def create_job(cls, task_type: str, models_used: Optional[List[str]] = None) -> JobResponse:
        """Initializes a new job in queued state."""
        job_id = f"apex_job_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        now = time.time()

        job = JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress_percent=10,
            task_type=task_type,
            models_used=models_used or [],
            created_at=now,
        )

        with cls._lock:
            cls._jobs[job_id] = job
            # Keep at most 200 jobs in history
            if len(cls._jobs) > 200:
                oldest_key = min(cls._jobs.keys(), key=lambda k: cls._jobs[k].created_at)
                cls._jobs.pop(oldest_key, None)

        return job

    @classmethod
    def get_job(cls, job_id: str) -> Optional[JobResponse]:
        with cls._lock:
            return cls._jobs.get(job_id)

    @classmethod
    def update_progress(cls, job_id: str, progress: int, status: Optional[JobStatus] = None) -> None:
        with cls._lock:
            job = cls._jobs.get(job_id)
            if job:
                job.progress_percent = progress
                if status:
                    job.status = status

    @classmethod
    def complete_job(
        cls,
        job_id: str,
        image_b64: str,
        quality_metrics: QualityMetrics,
        models_used: List[str],
        result_url: str,
    ) -> JobResponse:
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                raise KeyError(f"Job {job_id} not found.")

            now = time.time()
            job.status = JobStatus.COMPLETED
            job.progress_percent = 100
            job.completed_at = now
            job.duration_sec = round(now - job.created_at, 2)
            job.image = image_b64
            job.quality_metrics = quality_metrics
            job.models_used = models_used
            job.result_url = result_url
            job.input_resolution = quality_metrics.input_resolution
            job.output_resolution = quality_metrics.output_resolution
            return job

    @classmethod
    def fail_job(cls, job_id: str, error_message: str) -> Optional[JobResponse]:
        with cls._lock:
            job = cls._jobs.get(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.progress_percent = 0
                job.error = error_message
                job.completed_at = time.time()
                return job
            return None

    @classmethod
    def cancel_job(cls, job_id: str) -> bool:
        with cls._lock:
            job = cls._jobs.get(job_id)
            if job and job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                job.status = JobStatus.CANCELLED
                job.progress_percent = 0
                job.completed_at = time.time()
                return True
            return False

    @classmethod
    def list_recent_jobs(cls, limit: int = 20) -> List[JobResponse]:
        with cls._lock:
            sorted_jobs = sorted(cls._jobs.values(), key=lambda j: j.created_at, reverse=True)
            return sorted_jobs[:limit]
