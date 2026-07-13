# Dashboard View

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
