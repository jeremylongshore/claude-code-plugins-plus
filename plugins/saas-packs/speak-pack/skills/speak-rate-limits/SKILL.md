---
name: speak-rate-limits
description: |
  Implement Speak rate limiting, backoff, and idempotency patterns for language learning APIs.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Speak integrations.
  Trigger with phrases like "speak rate limit", "speak throttling",
  "speak 429", "speak retry", "speak backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Rate Limits

## Overview
Rate limit management for Speak's language learning API. Audio processing endpoints are computationally expensive, with stricter limits on pronunciation assessment than text-based endpoints.

## Prerequisites
- Speak API access configured
- Understanding of audio processing latency
- Queue infrastructure for batch assessments

## Speak API Rate Limits

| Endpoint | Limit | Notes |
|----------|-------|-------|
| Pronunciation Assessment | 30/min | Audio processing intensive |
| Conversation Start | 20/min | Creates session state |
| Conversation Turn | 60/min | Within active sessions |
| Translation | 120/min | Text-only, faster |

## Instructions

### Step 1: Audio-Aware Rate Limiter

Audio endpoints are slower and more resource-intensive. Track per-endpoint.

```python
import time, threading

class SpeakRateLimiter:
    def __init__(self):
        self.limits = {
            "pronunciation": 30,
            "conversation_start": 20,
            "conversation_turn": 60,
            "translation": 120,
        }
        self.windows = {k: [] for k in self.limits}
        self.lock = threading.Lock()

    def wait_if_needed(self, endpoint: str):
        with self.lock:
            now = time.time()
            self.windows[endpoint] = [t for t in self.windows[endpoint] if now - t < 60]
            if len(self.windows[endpoint]) >= self.limits[endpoint]:
                sleep_time = 60 - (now - self.windows[endpoint][0])
                time.sleep(sleep_time + 0.1)
            self.windows[endpoint].append(time.time())

limiter = SpeakRateLimiter()

def assess_pronunciation(client, audio_path, text):
    limiter.wait_if_needed("pronunciation")
    return client.assess_pronunciation(audio_path, text)
```

### Step 2: Batch Assessment Queue

Queue multiple student recordings and process within rate limits.

```python
from queue import PriorityQueue
import threading

class AssessmentQueue:
    def __init__(self, client, limiter):
        self.queue = PriorityQueue()
        self.client = client
        self.limiter = limiter
        self.results = {}

    def submit(self, student_id: str, audio_path: str, text: str, priority: int = 5):
        self.queue.put((priority, student_id, audio_path, text))

    def process_all(self) -> dict:
        while not self.queue.empty():
            priority, student_id, audio_path, text = self.queue.get()
            self.limiter.wait_if_needed("pronunciation")
            try:
                result = self.client.assess_pronunciation(audio_path, text)
                self.results[student_id] = {"score": result["score"], "status": "ok"}
            except Exception as e:
                self.results[student_id] = {"error": str(e), "status": "failed"}
        return self.results
```

### Step 3: Handle 429 with Retry-After

```python
def speak_with_retry(fn, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn(*args)
        except requests.HTTPError as e:
            if e.response.status_code == 429:  # HTTP 429 Too Many Requests
                wait = int(e.response.headers.get("Retry-After", 5))
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 on assessment | Exceeded 30/min | Queue assessments, spread over time |
| Slow batch processing | Sequential audio processing | Respect rate limits, don't parallelize too much |
| Session timeout | Conversation idle too long | Send turns within session timeout |
| Audio upload rejected | File too large | Compress audio, limit to 25MB |

## Examples

### Rate Status Check
```python
status = {endpoint: {
    "used": len(limiter.windows[endpoint]),
    "limit": limiter.limits[endpoint],
    "available": limiter.limits[endpoint] - len(limiter.windows[endpoint])
} for endpoint in limiter.limits}
```

## Resources
- [Speak API Docs](https://docs.speak.com)

## Output

- Rate limiter implementation configured per endpoint
- Retry logic with exponential backoff for 429 responses
- Monitoring dashboard or log output showing rate limit usage