---
name: mistral-rate-limits
description: |
  Implement Mistral AI rate limiting, backoff, and request management.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Mistral AI.
  Trigger with phrases like "mistral rate limit", "mistral throttling",
  "mistral 429", "mistral retry", "mistral backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral Rate Limits

## Overview
Rate limit management for Mistral AI API. Mistral enforces per-minute request and token limits that vary by model tier and subscription plan.

## Prerequisites
- Mistral API key configured
- Understanding of token vs request rate limits
- Retry infrastructure

## Mistral Rate Limits by Tier

| Model | Requests/min | Tokens/min | Tokens/month |
|-------|-------------|------------|--------------|
| mistral-small | 120 | 500,000 | Varies by plan |
| mistral-medium | 60 | 500,000 | Varies by plan |
| mistral-large | 30 | 200,000 | Varies by plan |
| mistral-embed | 300 | 1,000,000 | Varies by plan |

## Instructions

### Step 1: Token-Aware Rate Limiter

Mistral limits both requests and tokens per minute. Track both.

```python
import time, threading

class MistralRateLimiter:
    def __init__(self, rpm: int = 60, tpm: int = 200000):
        self.rpm = rpm
        self.tpm = tpm
        self.request_times = []
        self.token_usage = []
        self.lock = threading.Lock()

    def wait_if_needed(self, estimated_tokens: int = 1000):
        with self.lock:
            now = time.time()
            cutoff = now - 60
            self.request_times = [t for t in self.request_times if t > cutoff]
            self.token_usage = [(t, n) for t, n in self.token_usage if t > cutoff]

            current_rpm = len(self.request_times)
            current_tpm = sum(n for _, n in self.token_usage)

            if current_rpm >= self.rpm:
                sleep_time = self.request_times[0] - cutoff
                time.sleep(sleep_time + 0.1)

            if current_tpm + estimated_tokens > self.tpm:
                sleep_time = self.token_usage[0][0] - cutoff
                time.sleep(sleep_time + 0.1)

            self.request_times.append(time.time())

    def record_usage(self, tokens: int):
        with self.lock:
            self.token_usage.append((time.time(), tokens))

# Usage
limiter = MistralRateLimiter(rpm=30, tpm=200000)

def rate_limited_chat(client, messages, model="mistral-large-latest"):
    estimated = sum(len(m["content"]) // 4 for m in messages)
    limiter.wait_if_needed(estimated)
    response = client.chat.complete(model=model, messages=messages)
    limiter.record_usage(response.usage.total_tokens)
    return response
```

### Step 2: Handle 429 Responses

```python
import time

def chat_with_retry(client, messages, model, max_retries=5):
    for attempt in range(max_retries):
        try:
            return client.chat.complete(model=model, messages=messages)
        except Exception as e:
            if hasattr(e, 'status_code') and e.status_code == 429:
                wait = min(2 ** attempt + 1, 60)
                print(f"Rate limited, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
```

### Step 3: Model-Tier Routing for Throughput

Route requests to cheaper models when premium capacity is exhausted.

```python
class ModelRouter:
    def __init__(self):
        self.limiters = {
            "mistral-large-latest": MistralRateLimiter(rpm=30, tpm=200000),
            "mistral-small-latest": MistralRateLimiter(rpm=120, tpm=500000),
        }

    def get_available_model(self, preferred: str = "mistral-large-latest") -> str:
        limiter = self.limiters[preferred]
        if limiter.has_capacity():
            return preferred
        # Fall back to smaller model with more capacity
        return "mistral-small-latest"
```

### Step 4: Batch Embedding with Rate Awareness

```python
def batch_embed(client, texts: list[str], batch_size: int = 32):
    limiter = MistralRateLimiter(rpm=300, tpm=1000000)
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        estimated_tokens = sum(len(t) // 4 for t in batch)
        limiter.wait_if_needed(estimated_tokens)
        response = client.embeddings.create(model="mistral-embed", inputs=batch)
        all_embeddings.extend([d.embedding for d in response.data])
        limiter.record_usage(response.usage.total_tokens)
    return all_embeddings
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 errors | Exceeded RPM or TPM | Use rate limiter, exponential backoff |
| Inconsistent limits | Different limits per model | Configure limiter per model tier |
| Batch embedding failures | Too many tokens per batch | Reduce batch size |
| Spike traffic blocked | No smoothing | Queue requests, spread over time |

## Examples

### Rate Limit Dashboard
```python
status = {
    "rpm_used": len(limiter.request_times),
    "rpm_limit": limiter.rpm,
    "tpm_used": sum(n for _, n in limiter.token_usage),
    "tpm_limit": limiter.tpm,
    "utilization_pct": len(limiter.request_times) / limiter.rpm * 100
}
```

## Resources
- [Mistral Rate Limits](https://docs.mistral.ai/capabilities/rate-limiting/)
- [Mistral API Reference](https://docs.mistral.ai/api/)
