---
name: klingai-async-workflows
description: |
  Build async video generation workflows with Kling AI using queues, state machines, and
  event-driven patterns. Trigger with phrases like 'klingai async', 'kling ai workflow',
  'klingai pipeline', 'async video generation'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, async, workflows]

---
# Kling AI Async Workflows

## Overview

Kling AI video generation is inherently async: you submit a task, then poll or receive a callback when done. This skill covers production patterns for integrating this into larger systems using queues, state machines, and event-driven architectures.

## Core Pattern: Submit + Callback

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

def submit_async(prompt, callback_url=None, **kwargs):
    """Submit task and return immediately."""
    body = {
        "model_name": kwargs.get("model", "kling-v2-master"),
        "prompt": prompt,
        "duration": str(kwargs.get("duration", 5)),
        "mode": kwargs.get("mode", "standard"),
    }
    if callback_url:
        body["callback_url"] = callback_url

    r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json=body)
    return r.json()["data"]["task_id"]
```

## Redis Queue Workflow

```python
import redis
import json

r = redis.Redis()

# Producer: enqueue video generation requests
def enqueue_video_job(prompt, metadata=None):
    job = {
        "id": f"job_{int(time.time() * 1000)}",
        "prompt": prompt,
        "metadata": metadata or {},
        "status": "queued",
        "created_at": time.time(),
    }
    r.lpush("kling:jobs:pending", json.dumps(job))
    return job["id"]

# Worker: process jobs from queue
def process_jobs(max_concurrent=3):
    active_tasks = {}

    while True:
        # Submit new jobs if under concurrency limit
        while len(active_tasks) < max_concurrent:
            raw = r.rpop("kling:jobs:pending")
            if not raw:
                break
            job = json.loads(raw)
            task_id = submit_async(job["prompt"])
            active_tasks[task_id] = job
            r.hset("kling:jobs:active", task_id, json.dumps(job))

        # Check active tasks
        completed = []
        for task_id, job in active_tasks.items():
            result = requests.get(
                f"{BASE}/videos/text2video/{task_id}", headers=get_headers()
            ).json()
            status = result["data"]["task_status"]

            if status == "succeed":
                job["status"] = "completed"
                job["video_url"] = result["data"]["task_result"]["videos"][0]["url"]
                r.lpush("kling:jobs:completed", json.dumps(job))
                completed.append(task_id)
            elif status == "failed":
                job["status"] = "failed"
                job["error"] = result["data"].get("task_status_msg")
                r.lpush("kling:jobs:failed", json.dumps(job))
                completed.append(task_id)

        for tid in completed:
            active_tasks.pop(tid)
            r.hdel("kling:jobs:active", tid)

        time.sleep(10)
```

## State Machine Pattern

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class JobState(Enum):
    QUEUED = "queued"
    SUBMITTING = "submitting"
    PROCESSING = "processing"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class VideoJob:
    prompt: str
    state: JobState = JobState.QUEUED
    task_id: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3

    def can_retry(self) -> bool:
        return self.state == JobState.FAILED and self.attempts < self.max_attempts

    def transition(self, new_state: JobState):
        valid = {
            JobState.QUEUED: {JobState.SUBMITTING},
            JobState.SUBMITTING: {JobState.PROCESSING, JobState.FAILED},
            JobState.PROCESSING: {JobState.DOWNLOADING, JobState.FAILED},
            JobState.DOWNLOADING: {JobState.COMPLETED, JobState.FAILED},
            JobState.FAILED: {JobState.RETRYING},
            JobState.RETRYING: {JobState.SUBMITTING},
        }
        if new_state not in valid.get(self.state, set()):
            raise ValueError(f"Invalid transition: {self.state} -> {new_state}")
        self.state = new_state
```

## Multi-Step Pipeline

```python
async def video_pipeline(prompt, steps=None):
    """Chain: generate -> extend -> download -> upload."""
    steps = steps or ["generate", "extend", "download"]

    # Step 1: Generate
    task_id = submit_async(prompt, duration=5)
    result = poll_task("/videos/text2video", task_id)  # from job-monitoring skill
    video_url = result["videos"][0]["url"]

    # Step 2: Extend (optional)
    if "extend" in steps:
        ext_r = requests.post(f"{BASE}/videos/video-extend", headers=get_headers(), json={
            "task_id": task_id,
            "prompt": f"Continue: {prompt}",
            "duration": "5",
        }).json()
        ext_result = poll_task("/videos/video-extend", ext_r["data"]["task_id"])
        video_url = ext_result["videos"][0]["url"]

    # Step 3: Download
    if "download" in steps:
        video_data = requests.get(video_url).content
        filepath = f"output/{task_id}.mp4"
        with open(filepath, "wb") as f:
            f.write(video_data)
        return filepath

    return video_url
```

## Event-Driven with Webhook

```python
# Use callback_url to avoid polling entirely
task_id = submit_async(
    "Sunset over ocean with sailboats",
    callback_url="https://your-app.com/webhooks/kling"
)

# Your webhook handler triggers next pipeline step
# See klingai-webhook-config skill for receiver implementation
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
