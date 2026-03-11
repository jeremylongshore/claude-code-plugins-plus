---
name: deepgram-rate-limits
description: |
  Implement Deepgram rate limiting and backoff strategies.
  Use when handling API quotas, implementing request throttling,
  or dealing with rate limit errors.
  Trigger with phrases like "deepgram rate limit", "deepgram throttling",
  "429 error deepgram", "deepgram quota", "deepgram backoff".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Rate Limits

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement proper rate limiting and backoff strategies for Deepgram API integration including request queuing, exponential backoff, circuit breaker pattern, and usage monitoring.

## Prerequisites
- Deepgram API key configured
- Understanding of your plan's rate limits
- Monitoring infrastructure (optional but recommended)

## Deepgram Rate Limits

| Plan | Concurrent Requests | Requests/Minute | Audio Hours/Month |
|------|---------------------|-----------------|-------------------|
| Pay As You Go | 100 | 1000 | Unlimited |
| Growth | 200 | 2000 | Included hours |
| Enterprise | Custom | Custom | Custom |

## Instructions

### Step 1: Implement Request Queue
Create a `DeepgramRateLimiter` class that manages concurrent request limits and per-minute quotas with automatic queue processing.

### Step 2: Add Exponential Backoff
Handle 429 responses with exponential backoff (base delay * 2^attempt) plus random jitter to avoid thundering herd.

### Step 3: Implement Circuit Breaker
Use CLOSED -> OPEN -> HALF_OPEN state machine to prevent cascade failures. Open after 5 consecutive failures, attempt recovery after 30s.

### Step 4: Monitor Usage
Track request counts, audio duration, error rates, and rate limit hits. Alert when hit rate exceeds 10%.

## Output
- Rate-limited request queue with concurrent/per-minute limits
- Exponential backoff handler with configurable base/max delay
- Circuit breaker with three-state pattern
- Usage monitoring with alert thresholds

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| 429 Too Many Requests | Rate limit exceeded | Backoff and retry, check queue config |
| Circuit breaker OPEN | Consecutive failures | Wait for reset timeout, check API status |
| Queue growing unbounded | Sustained high load | Increase limits or scale horizontally |
| Inaccurate usage stats | Counter reset missed | Check minute window reset logic |

## Examples

### Basic Rate Limiter Usage
```typescript
const limiter = new DeepgramRateLimiter({ maxConcurrent: 50, maxPerMinute: 500 });
const result = await limiter.execute(() => client.listen.prerecorded.transcribeUrl(url, opts));
```

### Backoff Configuration
```typescript
const backoff = new ExponentialBackoff({ baseDelay: 1000, maxDelay: 60000, factor: 2, jitter: true });
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Deepgram Pricing & Limits](https://deepgram.com/pricing)
- [Rate Limiting Best Practices](https://developers.deepgram.com/docs/rate-limits)
- [API Usage Dashboard](https://console.deepgram.com/usage)
