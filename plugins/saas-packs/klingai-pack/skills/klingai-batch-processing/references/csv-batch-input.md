# Csv Batch Input

## CSV Batch Input

```python
import csv
from typing import List

def load_batch_from_csv(filepath: str) -> List[BatchJob]:
    """Load batch jobs from CSV file."""
    jobs = []

    with open(filepath) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            job = BatchJob(
                id=row.get("id", f"job_{i}"),
                prompt=row["prompt"],
                params={
                    "duration": int(row.get("duration", 5)),
                    "model": row.get("model", "kling-v1.5"),
                    "aspect_ratio": row.get("aspect_ratio", "16:9")
                }
            )
            jobs.append(job)

    return jobs

def save_results_to_csv(result: BatchResult, filepath: str):
    """Save batch results to CSV file."""
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "prompt", "status", "video_url", "error", "duration_seconds"
        ])
        writer.writeheader()

        for job in result.jobs:
            duration = None
            if job.submitted_at and job.completed_at:
                duration = (job.completed_at - job.submitted_at).total_seconds()

            writer.writerow({
                "id": job.id,
                "prompt": job.prompt,
                "status": job.status.value,
                "video_url": job.video_url or "",
                "error": job.error or "",
                "duration_seconds": duration or ""
            })

# Usage
jobs = load_batch_from_csv("prompts.csv")
result = asyncio.run(processor.process_batch(jobs))
save_results_to_csv(result, "results.csv")
```
