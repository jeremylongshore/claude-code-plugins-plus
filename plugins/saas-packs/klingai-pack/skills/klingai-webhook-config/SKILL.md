---
name: klingai-webhook-config
description: |
  Configure webhooks for Kling AI job completion notifications. Use when building event-driven video
  pipelines or need real-time job status updates. Trigger with phrases like 'klingai webhook',
  'kling ai callback', 'klingai notifications', 'video completion webhook'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Webhook Configuration

## Overview

This skill shows how to configure webhook endpoints to receive real-time notifications when video generation jobs complete, fail, or change status in Kling AI.

## Prerequisites

- Kling AI API key configured
- Public HTTPS endpoint for webhook receiver
- Python 3.8+ or Node.js 18+

## Instructions

Follow these steps to configure webhooks:

1. **Create Endpoint**: Set up a webhook receiver endpoint
2. **Register Webhook**: Configure webhook URL with Kling AI
3. **Verify Signatures**: Validate webhook authenticity
4. **Handle Events**: Process different event types
5. **Implement Retries**: Handle delivery failures

## Webhook Event Types

```
Kling AI Webhook Events:

video.created      - Job submitted, processing started
video.processing   - Generation in progress (progress updates)
video.completed    - Video generation successful
video.failed       - Generation failed with error
video.cancelled    - Job was cancelled

Payload Structure:
{
  "event": "video.completed",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "job_id": "vid_abc123",
    "status": "completed",
    "video_url": "https://...",
    "thumbnail_url": "https://...",
    "duration": 5,
    "prompt": "Original prompt...",
    "model": "kling-v1.5",
    "created_at": "2025-01-15T10:25:00Z",
    "completed_at": "2025-01-15T10:30:00Z"
  },
  "signature": "sha256=..."
}
```

## Webhook Receiver (Python/Flask)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import os
import logging
from datetime import datetime

app = Flask(__name__)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.environ["KLINGAI_WEBHOOK_SECRET"]

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    provided = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, provided)

@app.route("/webhooks/klingai", methods=["POST"])
def handle_webhook():
    """Handle Kling AI webhook events."""
    # Verify signature
    signature = request.headers.get("X-Kling-Signature", "")
    if not verify_signature(request.data, signature):
        logger.warning("Invalid webhook signature")
        return jsonify({"error": "Invalid signature"}), 401

    # Parse event
    event = request.json
    event_type = event.get("event")
    data = event.get("data", {})

    logger.info(f"Received webhook: {event_type}")

    # Route to handler
    handlers = {
        "video.completed": handle_video_completed,
        "video.failed": handle_video_failed,
        "video.processing": handle_video_processing,
    }

    handler = handlers.get(event_type, handle_unknown_event)
    handler(data)

    # Always return 200 to acknowledge receipt
    return jsonify({"received": True}), 200

def handle_video_completed(data: dict):
    """Process completed video."""
    job_id = data["job_id"]
    video_url = data["video_url"]

    logger.info(f"Video completed: {job_id}")
    logger.info(f"Download URL: {video_url}")

    # Your processing logic here:
    # - Download and store video
    # - Update database
    # - Notify user
    # - Trigger downstream processing

def handle_video_failed(data: dict):
    """Process failed video generation."""
    job_id = data["job_id"]
    error = data.get("error", "Unknown error")

    logger.error(f"Video failed: {job_id} - {error}")

    # Your error handling logic:
    # - Log error details
    # - Notify operations team
    # - Possibly retry with different params

def handle_video_processing(data: dict):
    """Process progress update."""
    job_id = data["job_id"]
    progress = data.get("progress", 0)

    logger.info(f"Video {job_id} progress: {progress}%")

def handle_unknown_event(data: dict):
    """Handle unknown event types."""
    logger.warning(f"Unknown event type received: {data}")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

## Webhook Receiver (Node.js/Express)

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json({ verify: (req, res, buf) => { req.rawBody = buf; } }));

const WEBHOOK_SECRET = process.env.KLINGAI_WEBHOOK_SECRET;

function verifySignature(payload, signature) {
    const expected = crypto
        .createHmac('sha256', WEBHOOK_SECRET)
        .update(payload)
        .digest('hex');

    const provided = signature.replace('sha256=', '');
    return crypto.timingSafeEqual(
        Buffer.from(expected),
        Buffer.from(provided)
    );
}

app.post('/webhooks/klingai', (req, res) => {
    // Verify signature
    const signature = req.headers['x-kling-signature'] || '';
    if (!verifySignature(req.rawBody, signature)) {
        console.warn('Invalid webhook signature');
        return res.status(401).json({ error: 'Invalid signature' });
    }

    const { event, data } = req.body;
    console.log(`Received webhook: ${event}`);

    // Handle events
    switch (event) {
        case 'video.completed':
            handleVideoCompleted(data);
            break;
        case 'video.failed':
            handleVideoFailed(data);
            break;
        case 'video.processing':
            handleVideoProcessing(data);
            break;
        default:
            console.warn(`Unknown event: ${event}`);
    }

    res.json({ received: true });
});

function handleVideoCompleted(data) {
    console.log(`Video completed: ${data.job_id}`);
    console.log(`URL: ${data.video_url}`);
    // Your processing logic
}

function handleVideoFailed(data) {
    console.error(`Video failed: ${data.job_id} - ${data.error}`);
    // Your error handling
}

function handleVideoProcessing(data) {
    console.log(`Progress: ${data.job_id} - ${data.progress}%`);
}

app.listen(5000, () => console.log('Webhook server running on port 5000'));
```

## Register Webhook

```python
import requests
import os

def register_webhook(url: str, events: list = None) -> dict:
    """Register a webhook endpoint with Kling AI."""

    if events is None:
        events = ["video.completed", "video.failed"]

    response = requests.post(
        "https://api.klingai.com/v1/webhooks",
        headers={
            "Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "url": url,
            "events": events,
            "active": True
        }
    )
    response.raise_for_status()

    webhook_data = response.json()
    print(f"Webhook registered: {webhook_data['id']}")
    print(f"Secret: {webhook_data['secret']}")  # Save this securely!

    return webhook_data

# Register webhook
webhook = register_webhook(
    url="https://yourapp.com/webhooks/klingai",
    events=["video.completed", "video.failed", "video.processing"]
)
```

## Test Webhook Locally

```python
# Use ngrok for local testing
# ngrok http 5000

import requests

def send_test_webhook(endpoint: str):
    """Send a test webhook payload."""

    test_payload = {
        "event": "video.completed",
        "timestamp": "2025-01-15T10:30:00Z",
        "data": {
            "job_id": "test_vid_123",
            "status": "completed",
            "video_url": "https://example.com/test-video.mp4",
            "thumbnail_url": "https://example.com/test-thumb.jpg",
            "duration": 5,
            "prompt": "Test video prompt",
            "model": "kling-v1.5"
        }
    }

    # Note: In testing, skip signature verification
    response = requests.post(endpoint, json=test_payload)
    print(f"Response: {response.status_code}")
    print(response.json())

send_test_webhook("http://localhost:5000/webhooks/klingai")
```

## Output

Successful execution produces:
- Registered webhook endpoint
- Real-time event notifications
- Verified and secure webhook handling
- Event-specific processing logic

## Error Handling

Common errors and solutions:
1. **Invalid Signature**: Verify secret matches, check raw body encoding
2. **Timeout**: Return 200 quickly, process async
3. **Missing Events**: Check event subscription list

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Webhooks](https://docs.klingai.com/webhooks)
- [Webhook Security Best Practices](https://webhooks.fyi/security/hmac)
- [ngrok for Local Testing](https://ngrok.com/)
