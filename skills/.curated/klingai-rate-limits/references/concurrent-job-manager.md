# Concurrent Job Manager

## Concurrent Job Manager

```python
class ConcurrentJobManager:
    """Manage concurrent video generation jobs."""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.active_jobs = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def acquire_slot(self, timeout: float = None) -> bool:
        """Acquire a job slot."""
        with self.condition:
            start = time.time()
            while len(self.active_jobs) >= self.max_concurrent:
                remaining = None
                if timeout:
                    elapsed = time.time() - start
                    remaining = timeout - elapsed
                    if remaining <= 0:
                        return False

                self.condition.wait(timeout=remaining)

            job_id = str(uuid.uuid4())
            self.active_jobs.add(job_id)
            return job_id

    def release_slot(self, job_id: str):
        """Release a job slot."""
        with self.condition:
            self.active_jobs.discard(job_id)
            self.condition.notify()

    def get_active_count(self) -> int:
        """Get number of active jobs."""
        with self.lock:
            return len(self.active_jobs)

# Usage
job_manager = ConcurrentJobManager(max_concurrent=10)

def generate_with_slot(prompt: str):
    slot = job_manager.acquire_slot(timeout=60)
    if not slot:
        raise Exception("No available slots")

    try:
        return generate_video(prompt)
    finally:
        job_manager.release_slot(slot)
```
