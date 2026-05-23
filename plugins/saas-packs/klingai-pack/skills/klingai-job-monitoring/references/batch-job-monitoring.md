# Batch Job Monitoring

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
