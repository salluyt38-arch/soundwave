"""
Worker Pool & Hardware Concurrency Manager for Adobe Studio Pro.
Coordinates active compute worker threads, queue backpressure, and automatic OOM recovery.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from ..contracts import EnhanceJob, JobPriority, JobStatus
from ..router.secure_router import SecureGPURouter

logger = logging.getLogger("gpu_infrastructure.workers")


class WorkerPoolManager:
    """Manages worker concurrency and health telemetry across execution cores."""

    def __init__(self, max_concurrency: int = 2):
        self.max_concurrency = max_concurrency
        self.active_jobs = 0
        self._lock = threading.Lock()
        self._completed_count = 0
        self._failed_count = 0

    def can_accept_job(self) -> bool:
        with self._lock:
            return self.active_jobs < self.max_concurrency

    def track_start(self):
        with self._lock:
            self.active_jobs += 1

    def track_finish(self, success: bool = True):
        with self._lock:
            self.active_jobs = max(0, self.active_jobs - 1)
            if success:
                self._completed_count += 1
            else:
                self._failed_count += 1

    def get_pool_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "max_concurrency": self.max_concurrency,
                "active_jobs": self.active_jobs,
                "completed_jobs": self._completed_count,
                "failed_jobs": self._failed_count,
                "is_available": self.active_jobs < self.max_concurrency,
            }


# Singleton worker pool
worker_pool = WorkerPoolManager(max_concurrency=2)
