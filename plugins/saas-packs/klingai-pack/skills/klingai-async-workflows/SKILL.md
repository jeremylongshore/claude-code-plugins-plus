---
name: klingai-async-workflows
description: |
  Build asynchronous video generation workflows with Kling AI. Use when integrating video
  generation into larger systems or pipelines. Trigger with phrases like 'klingai async',
  'kling ai workflow', 'klingai pipeline', 'async video generation'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Async Workflows

## Overview

This skill demonstrates building asynchronous workflows for video generation, including job queues, state machines, event-driven processing, and integration with workflow orchestration systems.

## Prerequisites

- Kling AI API key configured
- Python 3.8+ or Node.js 18+
- Message queue (Redis, RabbitMQ) or workflow engine

## Instructions

Follow these steps to build async workflows:

1. **Design Workflow**: Map out the video generation pipeline
2. **Implement Queue**: Set up job queue for async processing
3. **Create Workers**: Build workers to process jobs
4. **Handle States**: Manage job state transitions
5. **Add Monitoring**: Track workflow progress

## Workflow State Machine

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import json

class WorkflowState(Enum):
    CREATED = "created"
    VALIDATED = "validated"
    QUEUED = "queued"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowJob:
    id: str
    prompt: str
    state: WorkflowState = WorkflowState.CREATED
    params: Dict = field(default_factory=dict)
    klingai_job_id: Optional[str] = None
    video_url: Optional[str] = None
    processed_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    history: list = field(default_factory=list)

class WorkflowEngine:
    """State machine for video generation workflows."""

    # Valid state transitions
    TRANSITIONS = {
        WorkflowState.CREATED: [WorkflowState.VALIDATED, WorkflowState.FAILED],
        WorkflowState.VALIDATED: [WorkflowState.QUEUED, WorkflowState.FAILED],
        WorkflowState.QUEUED: [WorkflowState.GENERATING, WorkflowState.CANCELLED],
        WorkflowState.GENERATING: [WorkflowState.POST_PROCESSING, WorkflowState.FAILED],
        WorkflowState.POST_PROCESSING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
        WorkflowState.COMPLETED: [],  # Terminal state
        WorkflowState.FAILED: [],     # Terminal state
        WorkflowState.CANCELLED: [],  # Terminal state
    }

    def __init__(self):
        self.handlers: Dict[WorkflowState, Callable] = {}
        self.on_transition: Optional[Callable] = None

    def register_handler(self, state: WorkflowState, handler: Callable):
        """Register a handler for a workflow state."""
        self.handlers[state] = handler

    def transition(self, job: WorkflowJob, new_state: WorkflowState, **kwargs):
        """Transition job to new state."""
        if new_state not in self.TRANSITIONS.get(job.state, []):
            raise ValueError(
                f"Invalid transition: {job.state.value} -> {new_state.value}"
            )

        old_state = job.state
        job.state = new_state
        job.updated_at = datetime.utcnow()
        job.history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": job.updated_at.isoformat(),
            "data": kwargs
        })

        # Update job with any additional data
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        if self.on_transition:
            self.on_transition(job, old_state, new_state)

    async def process(self, job: WorkflowJob) -> WorkflowJob:
        """Process job through workflow."""
        while job.state not in [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED
        ]:
            handler = self.handlers.get(job.state)
            if not handler:
                raise RuntimeError(f"No handler for state: {job.state.value}")

            try:
                await handler(self, job)
            except Exception as e:
                self.transition(job, WorkflowState.FAILED, error=str(e))

        return job
```

## Workflow Implementation

```python
import asyncio
import aiohttp
import os

async def validate_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Validate job parameters."""
    # Validation logic
    if not job.prompt or len(job.prompt) < 10:
        raise ValueError("Prompt too short")

    if len(job.prompt) > 2000:
        raise ValueError("Prompt too long")

    # Validate params
    duration = job.params.get("duration", 5)
    if duration not in [5, 10]:
        raise ValueError(f"Invalid duration: {duration}")

    engine.transition(job, WorkflowState.VALIDATED)

async def queue_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Queue job for processing."""
    # In production, this would add to a real queue
    # For now, transition directly
    engine.transition(job, WorkflowState.QUEUED)
    engine.transition(job, WorkflowState.GENERATING)

async def generate_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Submit to Kling AI and wait for completion."""
    api_key = os.environ["KLINGAI_API_KEY"]

    async with aiohttp.ClientSession() as session:
        # Submit job
        async with session.post(
            "https://api.klingai.com/v1/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": job.prompt,
                **job.params
            }
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"API error: {response.status}")

            data = await response.json()
            job.klingai_job_id = data["job_id"]

        # Poll for completion
        while True:
            async with session.get(
                f"https://api.klingai.com/v1/videos/{job.klingai_job_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                data = await response.json()

                if data["status"] == "completed":
                    job.video_url = data["video_url"]
                    break
                elif data["status"] == "failed":
                    raise RuntimeError(data.get("error", "Generation failed"))

            await asyncio.sleep(5)

    engine.transition(job, WorkflowState.POST_PROCESSING)

async def post_process_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Post-process the generated video."""
    # Example post-processing:
    # - Download video
    # - Generate thumbnails
    # - Add watermark
    # - Upload to CDN

    # For now, just use original URL
    job.processed_url = job.video_url

    engine.transition(job, WorkflowState.COMPLETED)

# Build workflow
async def create_workflow() -> WorkflowEngine:
    engine = WorkflowEngine()

    engine.register_handler(WorkflowState.CREATED, validate_handler)
    engine.register_handler(WorkflowState.VALIDATED, queue_handler)
    engine.register_handler(WorkflowState.GENERATING, generate_handler)
    engine.register_handler(WorkflowState.POST_PROCESSING, post_process_handler)

    def on_transition(job, old_state, new_state):
        print(f"[{job.id}] {old_state.value} -> {new_state.value}")

    engine.on_transition = on_transition

    return engine

# Usage
async def main():
    engine = await create_workflow()

    job = WorkflowJob(
        id="workflow_001",
        prompt="A beautiful sunset over a calm ocean with gentle waves",
        params={"duration": 5, "model": "kling-v1.5"}
    )

    result = await engine.process(job)

    if result.state == WorkflowState.COMPLETED:
        print(f"Success! Video: {result.processed_url}")
    else:
        print(f"Failed: {result.error}")

asyncio.run(main())
```

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

## Output

Successful execution produces:
- Validated and queued workflow jobs
- State machine driven processing
- Complete audit trail of transitions
- Reliable job completion or failure handling

## Error Handling

Common errors and solutions:
1. **State Transition Error**: Verify valid transitions in workflow design
2. **Queue Timeout**: Increase worker timeout or check Redis connection
3. **Stuck Jobs**: Implement job timeout and recovery

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI API](https://docs.klingai.com/api)
- [Redis Queues](https://redis.io/docs/data-types/lists/)
- [State Machine Patterns](https://python-statemachine.readthedocs.io/)
