# Complete Reference Implementation

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
