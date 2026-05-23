# Redis Queue Integration

## Redis Queue Integration

```python
import redis
import json
from typing import Optional

class RedisJobQueue:
    """Redis-backed job queue for video workflows."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.queue_key = "klingai:jobs:pending"
        self.processing_key = "klingai:jobs:processing"
        self.results_key = "klingai:jobs:results"

    def enqueue(self, job: WorkflowJob):
        """Add job to queue."""
        job_data = {
            "id": job.id,
            "prompt": job.prompt,
            "params": job.params,
            "metadata": job.metadata
        }
        self.redis.lpush(self.queue_key, json.dumps(job_data))
        print(f"Enqueued job: {job.id}")

    def dequeue(self, timeout: int = 0) -> Optional[WorkflowJob]:
        """Get next job from queue."""
        result = self.redis.brpoplpush(
            self.queue_key,
            self.processing_key,
            timeout=timeout
        )

        if result:
            data = json.loads(result)
            return WorkflowJob(
                id=data["id"],
                prompt=data["prompt"],
                params=data.get("params", {}),
                metadata=data.get("metadata", {})
            )
        return None

    def complete(self, job: WorkflowJob):
        """Mark job as complete."""
        # Remove from processing
        self.redis.lrem(self.processing_key, 1, json.dumps({
            "id": job.id,
            "prompt": job.prompt,
            "params": job.params,
            "metadata": job.metadata
        }))

        # Store result
        self.redis.hset(self.results_key, job.id, json.dumps({
            "id": job.id,
            "state": job.state.value,
            "video_url": job.video_url,
            "processed_url": job.processed_url,
            "error": job.error
        }))

    def get_result(self, job_id: str) -> Optional[dict]:
        """Get job result."""
        result = self.redis.hget(self.results_key, job_id)
        if result:
            return json.loads(result)
        return None

# Worker process
async def worker(queue: RedisJobQueue, engine: WorkflowEngine):
    """Worker that processes jobs from queue."""
    print("Worker started, waiting for jobs...")

    while True:
        job = queue.dequeue(timeout=5)

        if job:
            print(f"Processing job: {job.id}")
            try:
                result = await engine.process(job)
                queue.complete(result)
                print(f"Completed job: {job.id}")
            except Exception as e:
                job.state = WorkflowState.FAILED
                job.error = str(e)
                queue.complete(job)
                print(f"Failed job: {job.id} - {e}")
```
