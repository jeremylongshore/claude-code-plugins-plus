---
name: klingai-reference-architecture
description: |
  Production-ready reference architecture for Kling AI video platforms. Use when designing
  scalable video generation systems. Trigger with phrases like 'klingai architecture',
  'kling ai system design', 'video platform architecture', 'klingai production setup'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Reference Architecture

## Overview

This skill provides production-ready reference architectures for building scalable video generation platforms using Kling AI, including microservices design, event-driven patterns, and infrastructure recommendations.

## Prerequisites

- Understanding of distributed systems
- Cloud infrastructure experience (AWS/GCP/Azure)
- Docker/Kubernetes knowledge helpful

## Instructions

Follow these steps to design your architecture:

1. **Choose Pattern**: Select appropriate architecture pattern
2. **Design Components**: Map out service boundaries
3. **Plan Infrastructure**: Choose cloud services
4. **Implement Resilience**: Add fault tolerance
5. **Monitor & Scale**: Set up observability

## Architecture Patterns

### Pattern 1: Simple Queue-Based

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   API GW    │───▶│  Job Queue  │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                   ┌─────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│                    Worker Pool                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │Worker 1 │  │Worker 2 │  │Worker N │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
└───────┼────────────┼────────────┼───────────────────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
              ┌─────────────┐    ┌─────────────┐
              │  Kling AI   │───▶│   Storage   │
              │    API      │    │   (S3/GCS)  │
              └─────────────┘    └─────────────┘
```

Best for: Small to medium workloads, simple requirements

### Pattern 2: Event-Driven Microservices

```
┌───────────────────────────────────────────────────────────────┐
│                         Event Bus (Kafka/SNS)                  │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│   │ video.  │  │ video.  │  │ video.  │  │ video.  │         │
│   │ request │  │ started │  │complete │  │ failed  │         │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
└────────┼────────────┼────────────┼────────────┼───────────────┘
         │            │            │            │
    ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
    │ Request │  │Generator│  │ Storage │  │  Alert  │
    │ Service │  │ Service │  │ Service │  │ Service │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

Best for: Complex workflows, high scalability needs

### Pattern 3: Serverless

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  API GW/    │───▶│   Lambda/   │───▶│  Step       │
│  Cloud Run  │    │   Cloud Fn  │    │  Functions  │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                   ┌─────────────────────────┘
                   ▼
           ┌─────────────┐
           │   Submit    │──┐
           │   Job       │  │
           └─────────────┘  │
                            │
           ┌─────────────┐  │     ┌─────────────┐
           │   Wait for  │◀─┘     │  Kling AI   │
           │   Complete  │───────▶│    API      │
           └──────┬──────┘        └─────────────┘
                  │
           ┌──────┴──────┐
           ▼             ▼
    ┌─────────────┐  ┌─────────────┐
    │   Store     │  │   Notify    │
    │   Video     │  │   User      │
    └─────────────┘  └─────────────┘
```

Best for: Variable workloads, cost optimization

## Complete Reference Implementation

```python
# architecture/services/api_gateway.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid
import redis
import json

app = FastAPI(title="Video Generation Platform")
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

class VideoRequest(BaseModel):
    prompt: str
    duration: int = 5
    model: str = "kling-v1.5"
    webhook_url: Optional[str] = None
    metadata: Optional[dict] = None

class VideoResponse(BaseModel):
    request_id: str
    status: str
    message: str

@app.post("/api/v1/videos", response_model=VideoResponse)
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Submit a video generation request."""
    request_id = str(uuid.uuid4())

    # Store request
    job_data = {
        "request_id": request_id,
        "status": "pending",
        "prompt": request.prompt,
        "duration": request.duration,
        "model": request.model,
        "webhook_url": request.webhook_url,
        "metadata": request.metadata or {}
    }

    # Save to Redis
    redis_client.hset(f"job:{request_id}", mapping={
        k: json.dumps(v) if isinstance(v, dict) else str(v)
        for k, v in job_data.items()
    })

    # Add to queue
    redis_client.lpush("video:queue:pending", request_id)

    return VideoResponse(
        request_id=request_id,
        status="pending",
        message="Video generation request submitted"
    )

@app.get("/api/v1/videos/{request_id}")
async def get_video_status(request_id: str):
    """Get status of a video generation request."""
    job_data = redis_client.hgetall(f"job:{request_id}")

    if not job_data:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "request_id": request_id,
        "status": job_data.get("status"),
        "video_url": job_data.get("video_url"),
        "error": job_data.get("error")
    }
```

```python
# architecture/services/worker.py
import os
import time
import redis
import requests
import json
from typing import Optional

class VideoWorker:
    """Worker that processes video generation jobs."""

    def __init__(self):
        self.redis = redis.Redis(host="redis", port=6379, decode_responses=True)
        self.api_key = os.environ["KLINGAI_API_KEY"]
        self.base_url = "https://api.klingai.com/v1"

    def run(self):
        """Main worker loop."""
        print("Worker started, waiting for jobs...")

        while True:
            # Blocking pop from queue
            result = self.redis.brpop("video:queue:pending", timeout=5)

            if result:
                _, request_id = result
                self.process_job(request_id)

    def process_job(self, request_id: str):
        """Process a single video generation job."""
        print(f"Processing job: {request_id}")

        try:
            # Get job data
            job_data = self.redis.hgetall(f"job:{request_id}")

            # Update status
            self.update_status(request_id, "generating")

            # Submit to Kling AI
            klingai_job_id = self.submit_to_klingai(job_data)
            self.redis.hset(f"job:{request_id}", "klingai_job_id", klingai_job_id)

            # Poll for completion
            result = self.wait_for_completion(klingai_job_id)

            # Update with result
            self.update_status(request_id, "completed", result)

            # Send webhook if configured
            webhook_url = job_data.get("webhook_url")
            if webhook_url:
                self.send_webhook(webhook_url, request_id, "completed", result)

            print(f"Job completed: {request_id}")

        except Exception as e:
            print(f"Job failed: {request_id} - {e}")
            self.update_status(request_id, "failed", error=str(e))

    def submit_to_klingai(self, job_data: dict) -> str:
        """Submit job to Kling AI API."""
        response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": job_data["prompt"],
                "duration": int(job_data["duration"]),
                "model": job_data["model"]
            }
        )
        response.raise_for_status()
        return response.json()["job_id"]

    def wait_for_completion(self, job_id: str, timeout: int = 600) -> dict:
        """Poll Kling AI until job completes."""
        start = time.time()

        while time.time() - start < timeout:
            response = requests.get(
                f"{self.base_url}/videos/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            data = response.json()

            if data["status"] == "completed":
                return {
                    "video_url": data["video_url"],
                    "thumbnail_url": data.get("thumbnail_url")
                }
            elif data["status"] == "failed":
                raise Exception(data.get("error", "Generation failed"))

            time.sleep(5)

        raise Exception("Timeout waiting for video generation")

    def update_status(self, request_id: str, status: str, result: dict = None, error: str = None):
        """Update job status in Redis."""
        updates = {"status": status}
        if result:
            updates.update(result)
        if error:
            updates["error"] = error

        self.redis.hset(f"job:{request_id}", mapping=updates)

    def send_webhook(self, url: str, request_id: str, status: str, result: dict):
        """Send webhook notification."""
        try:
            requests.post(url, json={
                "request_id": request_id,
                "status": status,
                **result
            }, timeout=10)
        except Exception as e:
            print(f"Webhook failed: {e}")

if __name__ == "__main__":
    worker = VideoWorker()
    worker.run()
```

## Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
    deploy:
      replicas: 2

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - REDIS_HOST=redis
      - KLINGAI_API_KEY=${KLINGAI_API_KEY}
    depends_on:
      - redis
    deploy:
      replicas: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api

volumes:
  redis_data:
```

## Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: video-api
  template:
    metadata:
      labels:
        app: video-api
    spec:
      containers:
      - name: api
        image: video-platform/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_HOST
          value: redis-service
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-worker
spec:
  replicas: 10
  selector:
    matchLabels:
      app: video-worker
  template:
    metadata:
      labels:
        app: video-worker
    spec:
      containers:
      - name: worker
        image: video-platform/worker:latest
        env:
        - name: REDIS_HOST
          value: redis-service
        - name: KLINGAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: klingai-secrets
              key: api-key
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-worker
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_length
      target:
        type: AverageValue
        averageValue: 10
```

## Output

Successful execution produces:
- Scalable video generation platform
- Event-driven processing pipeline
- Container-ready deployment configs
- Auto-scaling based on queue depth

## Error Handling

Common errors and solutions:
1. **Queue Buildup**: Scale workers horizontally
2. **API Timeouts**: Implement circuit breaker
3. **Storage Failures**: Add retry with exponential backoff

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI API](https://docs.klingai.com/api)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Redis Queues](https://redis.io/docs/data-types/lists/)
