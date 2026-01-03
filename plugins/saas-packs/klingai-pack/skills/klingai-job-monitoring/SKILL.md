---
name: klingai-job-monitoring
description: |
  Monitor and track Kling AI video generation jobs. Use when managing multiple generations or
  building job dashboards. Trigger with phrases like 'klingai job status', 'track klingai jobs',
  'kling ai monitoring', 'klingai job queue'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Job Monitoring

## Overview

This skill covers job status tracking, progress monitoring, webhook notifications, and building dashboards to manage multiple concurrent video generation jobs.

## Prerequisites

- Kling AI API key configured
- Multiple concurrent jobs to track
- Python 3.8+ or Node.js 18+

## Instructions

Follow these steps to monitor jobs:

1. **Track Job Submission**: Record job IDs and metadata
2. **Poll for Status**: Implement efficient status polling
3. **Handle State Changes**: React to status transitions
4. **Build Dashboard**: Create monitoring interface
5. **Set Up Alerts**: Configure notifications

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

## Polling Monitor

```python
class PollingMonitor:
    """Background monitor that polls job statuses."""

    def __init__(self, tracker: JobTracker, poll_interval: int = 5):
        self.tracker = tracker
        self.poll_interval = poll_interval
        self.running = False
        self._thread = None

    def start(self):
        """Start background polling."""
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop background polling."""
        self.running = False
        if self._thread:
            self._thread.join()

    def _poll_loop(self):
        """Main polling loop."""
        while self.running:
            active_jobs = self.tracker.get_active_jobs()

            for job in active_jobs:
                try:
                    self.tracker.refresh_job(job.job_id)
                except Exception as e:
                    print(f"Error refreshing job {job.job_id}: {e}")

            time.sleep(self.poll_interval)

# Usage
tracker = JobTracker()
monitor = PollingMonitor(tracker)

# Register callback for completed jobs
def on_status_change(job: JobRecord, old_status: JobStatus):
    if job.status == JobStatus.COMPLETED:
        print(f"✅ Job {job.job_id} completed: {job.video_url}")
    elif job.status == JobStatus.FAILED:
        print(f"❌ Job {job.job_id} failed: {job.error}")

tracker.register_callback(on_status_change)
monitor.start()
```

## Dashboard View

```python
from rich.console import Console
from rich.table import Table
from rich.live import Live

def create_dashboard_table(tracker: JobTracker) -> Table:
    """Create rich table for dashboard display."""
    table = Table(title="Kling AI Job Monitor")

    table.add_column("Job ID", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Progress", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Prompt", style="white", max_width=40)

    for job in tracker.jobs.values():
        status_emoji = {
            JobStatus.PENDING: "⏳",
            JobStatus.QUEUED: "📋",
            JobStatus.PROCESSING: "🔄",
            JobStatus.COMPLETED: "✅",
            JobStatus.FAILED: "❌",
            JobStatus.CANCELLED: "🚫"
        }.get(job.status, "❓")

        elapsed = (job.updated_at - job.created_at).total_seconds()

        table.add_row(
            job.job_id[:8],
            f"{status_emoji} {job.status.value}",
            f"{job.progress:.0%}",
            f"{elapsed:.1f}s",
            job.prompt[:40] + "..." if len(job.prompt) > 40 else job.prompt
        )

    return table

def run_live_dashboard(tracker: JobTracker, refresh_rate: int = 2):
    """Run live updating dashboard."""
    console = Console()

    with Live(create_dashboard_table(tracker), refresh_per_second=1/refresh_rate) as live:
        while True:
            live.update(create_dashboard_table(tracker))
            time.sleep(refresh_rate)
```

## Batch Job Monitoring

```python
async def monitor_batch(
    tracker: JobTracker,
    job_ids: List[str],
    on_progress: Callable = None,
    on_complete: Callable = None,
    timeout: int = 600
) -> Dict[str, JobRecord]:
    """Monitor a batch of jobs until all complete."""
    start_time = time.time()
    completed = set()

    while len(completed) < len(job_ids):
        if time.time() - start_time > timeout:
            raise TimeoutError("Batch monitoring timed out")

        for job_id in job_ids:
            if job_id in completed:
                continue

            job = tracker.refresh_job(job_id)

            if on_progress:
                on_progress(job)

            if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
                completed.add(job_id)
                if on_complete:
                    on_complete(job)

        # Progress summary
        print(f"Progress: {len(completed)}/{len(job_ids)} jobs complete")

        await asyncio.sleep(5)

    return {job_id: tracker.jobs[job_id] for job_id in job_ids}
```

## Output

Successful execution produces:
- Real-time job status updates
- Progress tracking dashboard
- Status change notifications
- Batch completion monitoring

## Error Handling

Common errors and solutions:
1. **Job Not Found**: Verify job ID is correct
2. **Stale Status**: Decrease poll interval
3. **API Errors**: Implement retry logic in refresh

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Job API](https://docs.klingai.com/api/jobs)
- [Rich Library](https://rich.readthedocs.io/)
- [Async Monitoring Patterns](https://docs.python.org/3/library/asyncio.html)
