---
name: klingai-reference-architecture
description: |
  Production reference architecture for Kling AI video generation platforms. Use when designing
  scalable systems. Trigger with phrases like 'klingai architecture', 'kling ai system design',
  'video platform architecture', 'klingai production setup'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, architecture, scaling]

---
# Kling AI Reference Architecture

## Overview

Production architecture for video generation platforms built on Kling AI. Covers API gateway, job queue, worker pool, storage, and monitoring layers.

## Architecture Diagram

```
User Request
    |
[API Gateway / Load Balancer]
    |
[Application Server]
    |--- validate prompt & estimate cost
    |--- enqueue job to Redis/SQS
    |
[Job Queue (Redis / SQS / Pub/Sub)]
    |
[Worker Pool (N workers)]
    |--- generate JWT token
    |--- POST https://api.klingai.com/v1/videos/text2video
    |--- receive task_id
    |--- register callback_url OR poll
    |
[Webhook Receiver / Poller]
    |--- receive completion callback
    |--- download video from Kling CDN
    |--- upload to S3/GCS
    |--- update job status in DB
    |--- notify user
    |
[Object Storage (S3 / GCS)]
    |
[CDN (CloudFront / Cloud CDN)]
    |
User views video
```

## Component Details

### API Layer

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class VideoRequest(BaseModel):
    prompt: str
    model: str = "kling-v2-master"
    duration: int = 5
    mode: str = "standard"

@app.post("/api/videos")
async def create_video(req: VideoRequest):
    # 1. Validate
    if len(req.prompt) > 2500:
        raise HTTPException(400, "Prompt exceeds 2500 chars")

    # 2. Estimate cost
    credits = estimate_credits(req.duration, req.mode)
    if not budget_guard.check(credits):
        raise HTTPException(402, "Budget exceeded")

    # 3. Enqueue
    job_id = await queue.enqueue({
        "prompt": req.prompt,
        "model": req.model,
        "duration": str(req.duration),
        "mode": req.mode,
    })

    return {"job_id": job_id, "status": "queued", "estimated_credits": credits}
```

### Worker Service

```python
import redis
import json

class VideoWorker:
    def __init__(self, kling_client, storage_client, redis_url="redis://localhost"):
        self.kling = kling_client
        self.storage = storage_client
        self.redis = redis.Redis.from_url(redis_url)

    def process_loop(self):
        while True:
            raw = self.redis.brpop("kling:jobs:pending", timeout=5)
            if not raw:
                continue

            job = json.loads(raw[1])
            try:
                # Submit to Kling API
                result = self.kling.text_to_video(
                    job["prompt"],
                    model=job["model"],
                    duration=int(job["duration"]),
                    mode=job["mode"],
                    callback_url=os.environ.get("WEBHOOK_URL"),
                )

                # If using polling (no callback)
                if isinstance(result, dict) and "videos" in result:
                    video_url = result["videos"][0]["url"]
                    stored_url = self.storage.download_and_upload(video_url, job["id"])
                    self.redis.publish("kling:events", json.dumps({
                        "type": "completed",
                        "job_id": job["id"],
                        "video_url": stored_url,
                    }))

            except Exception as e:
                self.redis.lpush("kling:jobs:failed", json.dumps({
                    **job, "error": str(e)
                }))
```

### Scaling Guidelines

| Component | Scaling Strategy |
|-----------|-----------------|
| Workers | Scale by queue depth (1 worker per 3 concurrent API tasks) |
| API servers | Horizontal, behind load balancer |
| Redis | Single instance for <1K jobs/day, cluster for more |
| Storage | S3/GCS scales automatically |
| CDN | CloudFront/Cloud CDN for global delivery |

### Concurrency Limits by Tier

| Tier | Max Concurrent Tasks | Workers Needed |
|------|---------------------|----------------|
| Free | 1 | 1 |
| Standard | 3 | 1 |
| Pro | 5 | 2 |
| Enterprise | 10+ | 3-4 |

## Docker Compose Setup

```yaml
# docker-compose.yml
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      - REDIS_URL=redis://redis:6379
      - KLING_ACCESS_KEY=${KLING_ACCESS_KEY}
      - KLING_SECRET_KEY=${KLING_SECRET_KEY}

  worker:
    build: ./worker
    deploy:
      replicas: 2
    environment:
      - REDIS_URL=redis://redis:6379
      - KLING_ACCESS_KEY=${KLING_ACCESS_KEY}
      - KLING_SECRET_KEY=${KLING_SECRET_KEY}
      - S3_BUCKET=${S3_BUCKET}

  webhook:
    build: ./webhook
    ports: ["8001:8001"]
    environment:
      - REDIS_URL=redis://redis:6379

  redis:
    image: redis:7-alpine
    volumes: ["redis-data:/data"]

volumes:
  redis-data:
```

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
