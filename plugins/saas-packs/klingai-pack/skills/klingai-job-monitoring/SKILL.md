---
name: klingai-job-monitoring
description: |
  Track and monitor Kling AI video generation task status. Use when building dashboards,
  tracking batch jobs, or debugging stuck tasks. Trigger with phrases like 'klingai job status',
  'kling ai monitor', 'track klingai task', 'klingai progress'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, monitoring, jobs]

---
# Kling AI Job Monitoring

## Overview

Every Kling AI generation returns a `task_id`. This skill covers polling strategies, batch tracking, timeout handling, and callback-based monitoring for the `/v1/videos/text2video`, `/v1/videos/image2video`, and `/v1/videos/video-extend` endpoints.

## Task Lifecycle

| Status | Meaning | Typical Duration |
|--------|---------|-----------------|
| `submitted` | Queued for processing | 0-30s |
| `processing` | Generation in progress | 30-120s (standard), 60-300s (professional) |
| `succeed` | Complete, video URL available | Terminal |
| `failed` | Generation failed | Terminal |

## Polling a Single Task

```python
import jwt, time, os, requests

BASE = "https://api.klingai.com/v1"

def get_headers():
    ak, sk = os.environ["KLING_ACCESS_KEY"], os.environ["KLING_SECRET_KEY"]
    token = jwt.encode(
        {"iss": ak, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5},
        sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"}
    )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def poll_task(endpoint: str, task_id: str, interval: int = 10, timeout: int = 600):
    """Poll with adaptive interval and timeout."""
    start = time.monotonic()
    attempts = 0
    while time.monotonic() - start < timeout:
        time.sleep(interval)
        attempts += 1
        r = requests.get(f"{BASE}{endpoint}/{task_id}", headers=get_headers(), timeout=30)
        data = r.json()["data"]
        status = data["task_status"]
        elapsed = int(time.monotonic() - start)
        print(f"[{elapsed}s] Poll #{attempts}: {status}")

        if status == "succeed":
            return data["task_result"]
        elif status == "failed":
            raise RuntimeError(f"Task failed: {data.get('task_status_msg', 'unknown')}")

        if attempts > 5:
            interval = min(interval * 1.2, 30)
    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
```

## Batch Job Tracker

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class TrackedTask:
    task_id: str
    endpoint: str
    prompt: str
    status: str = "submitted"
    created_at: float = field(default_factory=time.time)
    result_url: Optional[str] = None
    error_msg: Optional[str] = None

class BatchTracker:
    def __init__(self):
        self.tasks: dict[str, TrackedTask] = {}

    def add(self, task_id, endpoint, prompt):
        self.tasks[task_id] = TrackedTask(task_id=task_id, endpoint=endpoint, prompt=prompt)

    def update_all(self):
        active = [t for t in self.tasks.values() if t.status in ("submitted", "processing")]
        for task in active:
            try:
                r = requests.get(
                    f"{BASE}{task.endpoint}/{task.task_id}",
                    headers=get_headers(), timeout=30
                ).json()
                data = r["data"]
                task.status = data["task_status"]
                if task.status == "succeed":
                    task.result_url = data["task_result"]["videos"][0]["url"]
                elif task.status == "failed":
                    task.error_msg = data.get("task_status_msg")
            except Exception as e:
                print(f"Error polling {task.task_id}: {e}")

    def print_report(self):
        by_status = {}
        for t in self.tasks.values():
            by_status.setdefault(t.status, 0)
            by_status[t.status] += 1
        active = sum(v for k, v in by_status.items() if k in ("submitted", "processing"))
        print(f"\n=== Batch: {len(self.tasks)} tasks, {active} active ===")
        for status, count in sorted(by_status.items()):
            print(f"  {status}: {count}")
```

## Stuck Task Detection

```python
def detect_stuck(tracker: BatchTracker, threshold_sec: int = 600):
    """Flag tasks processing longer than threshold."""
    now = time.time()
    stuck = []
    for t in tracker.tasks.values():
        if t.status in ("submitted", "processing"):
            elapsed = now - t.created_at
            if elapsed > threshold_sec:
                stuck.append((t.task_id, int(elapsed)))
    if stuck:
        print(f"WARNING: {len(stuck)} stuck tasks:")
        for tid, secs in stuck:
            print(f"  {tid}: {secs}s")
    return stuck
```

## Batch Monitor Loop

```python
tracker = BatchTracker()

# Submit batch
for prompt in prompts:
    r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
        "model_name": "kling-v2-master", "prompt": prompt, "duration": "5"
    }).json()
    tracker.add(r["data"]["task_id"], "/videos/text2video", prompt)

# Monitor until all complete
while any(t.status in ("submitted", "processing") for t in tracker.tasks.values()):
    time.sleep(15)
    tracker.update_all()
    tracker.print_report()
    detect_stuck(tracker)
```

## Resources

- [Task Query API](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
