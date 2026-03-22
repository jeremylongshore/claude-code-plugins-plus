---
name: klingai-webhook-config
description: |
  Configure webhook callbacks for Kling AI task completion. Use when building event-driven
  pipelines or replacing polling. Trigger with phrases like 'klingai webhook', 'kling ai callback',
  'klingai notifications', 'video completion webhook'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, webhooks, callbacks]

---
# Kling AI Webhook Configuration

## Overview

Instead of polling task status, pass a `callback_url` when creating a task. Kling AI will POST the completed task result to your URL when generation finishes. This eliminates polling overhead and reduces API calls.

**Supported on:** All video generation endpoints (`text2video`, `image2video`, `video-extend`, `lip-sync`, `effects`)

## How It Works

1. Include `callback_url` in your task creation request
2. Kling queues the task normally
3. When task reaches terminal state (`succeed` or `failed`), Kling POSTs the full result to your URL
4. Your webhook handler processes the result

## Sending a Task with Callback

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

# Create task with callback
response = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
    "model_name": "kling-v2-master",
    "prompt": "A futuristic city skyline at night with neon lights",
    "duration": "5",
    "mode": "standard",
    "callback_url": "https://your-app.com/webhooks/kling",  # your endpoint
})

task_id = response.json()["data"]["task_id"]
print(f"Task {task_id} submitted with callback -- no polling needed")
```

## Webhook Receiver (Flask)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import json

app = Flask(__name__)

@app.route("/webhooks/kling", methods=["POST"])
def kling_webhook():
    payload = request.get_json()

    task_id = payload["data"]["task_id"]
    status = payload["data"]["task_status"]

    if status == "succeed":
        video_url = payload["data"]["task_result"]["videos"][0]["url"]
        print(f"Task {task_id} complete: {video_url}")
        # Download video, store to S3, notify user, etc.
        process_completed_video(task_id, video_url)
    elif status == "failed":
        error = payload["data"].get("task_status_msg", "Unknown error")
        print(f"Task {task_id} failed: {error}")
        handle_failure(task_id, error)

    return jsonify({"received": True}), 200
```

## Webhook Receiver (Express.js)

```javascript
import express from "express";
const app = express();
app.use(express.json());

app.post("/webhooks/kling", (req, res) => {
  const { data } = req.body;
  const { task_id, task_status } = data;

  if (task_status === "succeed") {
    const videoUrl = data.task_result.videos[0].url;
    console.log(`Task ${task_id} complete: ${videoUrl}`);
    processVideo(task_id, videoUrl);
  } else if (task_status === "failed") {
    console.error(`Task ${task_id} failed: ${data.task_status_msg}`);
  }

  res.json({ received: true });
});

app.listen(3000);
```

## Callback Payload Shape

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "abc123...",
    "task_status": "succeed",
    "task_status_msg": "",
    "task_result": {
      "videos": [{
        "id": "vid_001",
        "url": "https://cdn.klingai.com/...",
        "duration": "5.0"
      }]
    }
  }
}
```

## Webhook Reliability Pattern

```python
import time
from collections import defaultdict

class WebhookManager:
    """Track webhook delivery and fall back to polling on failure."""

    def __init__(self, poll_fallback_sec: int = 300):
        self.pending = {}  # task_id -> submission_time
        self.poll_fallback_sec = poll_fallback_sec

    def register(self, task_id: str):
        self.pending[task_id] = time.time()

    def mark_received(self, task_id: str):
        self.pending.pop(task_id, None)

    def get_stale_tasks(self) -> list:
        """Tasks that haven't received a callback within threshold."""
        now = time.time()
        return [tid for tid, submitted in self.pending.items()
                if now - submitted > self.poll_fallback_sec]

    def fallback_poll(self, client):
        """Poll stale tasks that missed their callback."""
        for task_id in self.get_stale_tasks():
            try:
                result = client._get(f"/videos/text2video/{task_id}")
                status = result["data"]["task_status"]
                if status in ("succeed", "failed"):
                    self.mark_received(task_id)
                    return result
            except Exception:
                pass
```

## Requirements for Your Webhook Endpoint

| Requirement | Detail |
|------------|--------|
| Protocol | HTTPS only |
| Response | Return `2xx` within 5 seconds |
| Availability | Must be publicly reachable |
| Idempotency | Handle duplicate deliveries gracefully |
| Timeout | Kling retries on timeout, so process async |

## Resources

- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [Developer Portal](https://app.klingai.com/global/dev)
