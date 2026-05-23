# Polling Monitor

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
