# Batch Processor Class

## Batch Processor Class

```python
import asyncio
import aiohttp
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BatchJob:
    id: str
    prompt: str
    params: Dict = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    job_id: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class BatchResult:
    total: int
    completed: int
    failed: int
    jobs: List[BatchJob]
    duration_seconds: float

class KlingAIBatchProcessor:
    """Process multiple video generation requests efficiently."""

    def __init__(
        self,
        api_key: str = None,
        max_concurrent: int = 10,
        requests_per_minute: int = 60
    ):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.max_concurrent = max_concurrent
        self.rpm = requests_per_minute
        self.base_url = "https://api.klingai.com/v1"

    async def process_batch(
        self,
        jobs: List[BatchJob],
        on_progress: Callable = None,
        on_complete: Callable = None
    ) -> BatchResult:
        """Process a batch of video generation jobs."""
        start_time = datetime.utcnow()

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Calculate delay between submissions
        delay = 60.0 / self.rpm

        async with aiohttp.ClientSession() as session:
            # Submit all jobs
            submit_tasks = []
            for i, job in enumerate(jobs):
                task = self._submit_with_delay(
                    session, semaphore, job, i * delay, on_progress
                )
                submit_tasks.append(task)

            await asyncio.gather(*submit_tasks)

            # Poll for completion
            await self._poll_all_jobs(session, jobs, on_progress)

        # Calculate results
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        duration = (datetime.utcnow() - start_time).total_seconds()

        result = BatchResult(
            total=len(jobs),
            completed=completed,
            failed=failed,
            jobs=jobs,
            duration_seconds=duration
        )

        if on_complete:
            on_complete(result)

        return result

    async def _submit_with_delay(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        job: BatchJob,
        delay: float,
        on_progress: Callable
    ):
        """Submit a single job with rate limiting."""
        await asyncio.sleep(delay)

        async with semaphore:
            try:
                job.status = JobStatus.SUBMITTED
                job.submitted_at = datetime.utcnow()

                async with session.post(
                    f"{self.base_url}/videos/text-to-video",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": job.prompt,
                        **job.params
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        job.job_id = data["job_id"]
                        job.status = JobStatus.PROCESSING
                    else:
                        job.status = JobStatus.FAILED
                        job.error = f"HTTP {response.status}"

                if on_progress:
                    on_progress(job)

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)

    async def _poll_all_jobs(
        self,
        session: aiohttp.ClientSession,
        jobs: List[BatchJob],
        on_progress: Callable
    ):
        """Poll all jobs until completion."""
        pending_jobs = [j for j in jobs if j.status == JobStatus.PROCESSING]

        while pending_jobs:
            for job in pending_jobs[:]:
                try:
                    async with session.get(
                        f"{self.base_url}/videos/{job.job_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            if data["status"] == "completed":
                                job.status = JobStatus.COMPLETED
                                job.video_url = data["video_url"]
                                job.completed_at = datetime.utcnow()
                                pending_jobs.remove(job)

                            elif data["status"] == "failed":
                                job.status = JobStatus.FAILED
                                job.error = data.get("error", "Unknown error")
                                pending_jobs.remove(job)

                            if on_progress:
                                on_progress(job)

                except Exception as e:
                    job.error = str(e)

            if pending_jobs:
                await asyncio.sleep(5)  # Poll interval

# Usage
async def main():
    processor = KlingAIBatchProcessor(
        max_concurrent=10,
        requests_per_minute=60
    )

    # Create batch jobs
    prompts = [
        "A sunset over the ocean with waves crashing",
        "A city skyline at night with neon lights",
        "A forest path in autumn with falling leaves",
        "A mountain peak with clouds rolling by",
        "A busy street market with colorful vendors"
    ]

    jobs = [
        BatchJob(id=f"job_{i}", prompt=p, params={"duration": 5, "model": "kling-v1.5"})
        for i, p in enumerate(prompts)
    ]

    # Progress callback
    def on_progress(job: BatchJob):
        print(f"[{job.id}] {job.status.value}: {job.prompt[:30]}...")

    # Process batch
    result = await processor.process_batch(jobs, on_progress=on_progress)

    print(f"\nBatch complete:")
    print(f"  Total: {result.total}")
    print(f"  Completed: {result.completed}")
    print(f"  Failed: {result.failed}")
    print(f"  Duration: {result.duration_seconds:.1f}s")

asyncio.run(main())
```
