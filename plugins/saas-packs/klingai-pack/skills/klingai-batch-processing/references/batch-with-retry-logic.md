# Batch With Retry Logic

## Batch with Retry Logic

```python
async def process_batch_with_retry(
    processor: KlingAIBatchProcessor,
    jobs: List[BatchJob],
    max_retries: int = 3
) -> BatchResult:
    """Process batch with automatic retry for failures."""

    for attempt in range(max_retries):
        result = await processor.process_batch(jobs)

        # Get failed jobs
        failed_jobs = [j for j in jobs if j.status == JobStatus.FAILED]

        if not failed_jobs:
            break

        print(f"Retry attempt {attempt + 1}: {len(failed_jobs)} failed jobs")

        # Reset failed jobs for retry
        for job in failed_jobs:
            job.status = JobStatus.PENDING
            job.job_id = None
            job.error = None

        # Only retry failed jobs
        jobs = failed_jobs

    return result
```
