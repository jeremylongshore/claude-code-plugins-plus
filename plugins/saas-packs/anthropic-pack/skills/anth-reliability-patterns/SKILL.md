---
name: anth-reliability-patterns
description: |
  Implement reliability patterns for Claude API: circuit breakers,
  graceful degradation, idempotency, and fallback strategies.
  Trigger with phrases like "anthropic reliability", "claude circuit breaker",
  "claude fallback", "anthropic fault tolerance".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Reliability Patterns

## Overview

Production reliability patterns for Claude API: circuit breaker (prevent cascading failures), graceful degradation (serve fallbacks), idempotency (safe retries), and timeout management.

## Circuit Breaker

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery

class ClaudeCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0.0

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker OPEN — Claude API unavailable")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = CircuitState.OPEN
            raise

# Usage
breaker = ClaudeCircuitBreaker(failure_threshold=5, recovery_timeout=60)

def safe_claude_call(prompt: str) -> str:
    try:
        return breaker.call(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text
    except Exception:
        return "AI assistant is temporarily unavailable."
```

## Graceful Degradation

```python
import anthropic

def complete_with_fallback(prompt: str) -> str:
    """Try Sonnet → Haiku → cached response → static fallback."""
    models = ["claude-sonnet-4-20250514", "claude-haiku-4-20250514"]

    for model in models:
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except anthropic.RateLimitError:
            continue  # Try cheaper model
        except anthropic.APIStatusError:
            continue  # Try next model

    # All models failed — return cached or static response
    cached = cache.get(f"claude:{hash(prompt)}")
    if cached:
        return f"[Cached response] {cached}"

    return "Our AI assistant is temporarily unavailable. Please try again in a few minutes."
```

## Idempotent Requests

```python
import hashlib
import json

class IdempotentClaude:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.cache = {}  # Use Redis in production

    def create_message(self, idempotency_key: str | None = None, **kwargs) -> str:
        # Generate deterministic key from request params if not provided
        if not idempotency_key:
            idempotency_key = hashlib.sha256(
                json.dumps(kwargs, sort_keys=True, default=str).encode()
            ).hexdigest()

        # Return cached result for duplicate requests
        if idempotency_key in self.cache:
            return self.cache[idempotency_key]

        msg = self.client.messages.create(**kwargs)
        result = msg.content[0].text
        self.cache[idempotency_key] = result
        return result
```

## Timeout Configuration

```python
# Layer timeouts for defense-in-depth
client = anthropic.Anthropic(
    timeout=60.0,      # SDK-level timeout (covers connect + read)
    max_retries=3,     # Auto-retry on 429/5xx
)

# Per-request timeout override
msg = client.messages.create(
    model="claude-haiku-4-20250514",
    max_tokens=64,
    messages=[{"role": "user", "content": "Quick question"}],
    timeout=10.0  # Override for fast operations
)
```

## Reliability Checklist

- [ ] Circuit breaker prevents cascading failures
- [ ] Graceful degradation serves fallback responses
- [ ] Idempotency keys prevent duplicate processing
- [ ] Timeouts configured at SDK and application level
- [ ] Health check probes API connectivity
- [ ] Retry logic uses exponential backoff (SDK default)
- [ ] Rate limit headers monitored for pre-emptive throttling

## Resources

- [API Error Types](https://docs.anthropic.com/en/api/errors)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)

## Next Steps

For policy guardrails, see `anth-policy-guardrails`.
