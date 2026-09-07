---
name: klingai-reference-architecture
description: 'Production reference architecture for Kling AI video generation platforms.
  Use when designing

  scalable systems. Trigger with phrases like ''klingai architecture'', ''kling ai
  system design'',

  ''video platform architecture'', ''klingai production setup''.

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kling-ai
- architecture
- scaling
compatibility: Designed for Claude Code
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

## Prerequisites

- Defined availability, latency, retention, residency, and cost objectives; a threat model; and named owners for policy, data rights, operations, and publication approval.
- A secret manager, private staging storage, immutable artifact digests, queue-level idempotency, and a bounded model/credit/concurrency allowlist.
- Synthetic or rights-cleared fixtures for load and integration tests. Production likeness or customer media requires consent and an explicit processing purpose; test runs must not export contacts or source media.

## Instructions

1. Keep the API gateway responsible for authentication, authorization, prompt and provenance validation, content-policy checks, destination allowlists, and budget estimation before queueing work.
2. Put only opaque job references and approved parameters on the queue. Workers obtain short-lived credentials from the secret manager, enforce idempotency, and submit a private draft rather than publishing directly.
3. Start each release with a watermarked sandbox canary. Verify policy, source rights, suppression/destination rules, output integrity, aggregate error rate, quota, and cost before an owner approves staged promotion.
4. Store generated media under encrypted, access-controlled paths with a retention deadline. Keep logs and events redacted; never copy prompts, source URLs, faces, contact data, credentials, or raw provider payloads into durable telemetry.
5. Promote by immutable digest and record the approval. On policy, quality, budget, storage, or provider failure, stop the queue, quarantine artifacts, revoke temporary links, delete staged data, and restore the previous approved manifest.
6. Test rollback and deletion in staging, then retain a receipt containing only opaque IDs, hashes, aggregate metrics, approval state, retention proof, and rollback reference.

## Output

The architecture decision should produce a component/data-flow map, trust boundaries, approved provider/model matrix, queue and retry policy, budget guard, policy and rights gate, storage/retention policy, canary and approval workflow, rollback runbook, and redacted evidence schema. A successful deployment receipt must identify the artifact digest and aggregate checks without containing user media or personal data.

## Error Handling

Return user-safe errors for invalid input, policy rejection, missing rights, quota,
budget, or authorization failures. Retry only bounded transient transport and
polling failures with idempotency protection; never replay a policy rejection or
unboundedly create billable tasks. Send unknown provider states to quarantine and
owner review, pause promotion, and use the prior manifest for rollback. If storage
or webhook delivery fails, preserve task state without exposing provider URLs,
clean temporary artifacts after recovery, and verify deletion at the retention
deadline.

## Examples

A staging deployment receipt may contain:

```text
artifact=sha256:opaque; environment=staging; fixture=synthetic-v4;
rights=cleared; policy=pass; canary=watermarked-private;
budget=within-limit; output_digest=sha256:opaque; approval=recorded;
retention=24h; deletion=verified; rollback=release-r31
```

The production path must reject a request with an unknown source or destination before enqueueing it; a green canary alone is not publication approval.

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
