# Job Tracker Class

## Job Tracker Class

```python
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
import requests
import os

class JobStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class JobRecord:
    job_id: str
    prompt: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[int] = None
    progress: float = 0.0
    metadata: Dict = field(default_factory=dict)

class JobTracker:
    """Track and monitor multiple video generation jobs."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.jobs: Dict[str, JobRecord] = {}
        self.callbacks: List[Callable] = []
        self.lock = threading.Lock()

    def add_job(self, job_id: str, prompt: str, **metadata) -> JobRecord:
        """Add a job to tracking."""
        now = datetime.utcnow()
        job = JobRecord(
            job_id=job_id,
            prompt=prompt,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata
        )
        with self.lock:
            self.jobs[job_id] = job
        return job

    def update_job(self, job_id: str, **updates) -> JobRecord:
        """Update job record with new data."""
        with self.lock:
            if job_id not in self.jobs:
                raise KeyError(f"Job {job_id} not found")

            job = self.jobs[job_id]
            old_status = job.status

            for key, value in updates.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            job.updated_at = datetime.utcnow()

            # Trigger callbacks on status change
            if "status" in updates and updates["status"] != old_status:
                self._trigger_callbacks(job, old_status)

            return job

    def register_callback(self, callback: Callable[[JobRecord, JobStatus], None]):
        """Register callback for status changes."""
        self.callbacks.append(callback)

    def _trigger_callbacks(self, job: JobRecord, old_status: JobStatus):
        """Trigger registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(job, old_status)
            except Exception as e:
                print(f"Callback error: {e}")

    def refresh_job(self, job_id: str) -> JobRecord:
        """Fetch latest status from API."""
        response = requests.get(
            f"https://api.klingai.com/v1/videos/{job_id}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        data = response.json()

        return self.update_job(
            job_id,
            status=JobStatus(data["status"]),
            video_url=data.get("video_url"),
            thumbnail_url=data.get("thumbnail_url"),
            error=data.get("error"),
            progress=data.get("progress", 0)
        )

    def get_jobs_by_status(self, status: JobStatus) -> List[JobRecord]:
        """Get all jobs with given status."""
        with self.lock:
            return [j for j in self.jobs.values() if j.status == status]

    def get_active_jobs(self) -> List[JobRecord]:
        """Get all non-terminal jobs."""
        active_statuses = {JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING}
        with self.lock:
            return [j for j in self.jobs.values() if j.status in active_statuses]

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        with self.lock:
            status_counts = {}
            for status in JobStatus:
                status_counts[status.value] = len([
                    j for j in self.jobs.values() if j.status == status
                ])

            return {
                "total": len(self.jobs),
                "by_status": status_counts,
                "active": len(self.get_active_jobs()),
                "success_rate": self._calculate_success_rate()
            }

    def _calculate_success_rate(self) -> float:
        completed = len(self.get_jobs_by_status(JobStatus.COMPLETED))
        failed = len(self.get_jobs_by_status(JobStatus.FAILED))
        total = completed + failed
        return (completed / total * 100) if total > 0 else 0
```
