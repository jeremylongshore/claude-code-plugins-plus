---
name: customerio-rate-limits
description: |
  Implement Customer.io rate limiting and backoff.
  Use when handling high-volume API calls, implementing
  retry logic, or optimizing API usage.
  Trigger with phrases like "customer.io rate limit", "customer.io throttle",
  "customer.io 429", "customer.io backoff".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Rate Limits

## Overview
Understand and implement proper rate limiting and backoff strategies for Customer.io API to handle high-volume operations reliably.

## Rate Limit Details

### Track API Limits
| Endpoint | Limit | Window |
|----------|-------|--------|
| Identify | 100 requests/second | Per workspace |
| Track events | 100 requests/second | Per workspace |
| Batch operations | 100 requests/second | Per workspace |

### App API Limits
| Endpoint | Limit | Window |
|----------|-------|--------|
| Transactional email/push | 100/second | Per workspace |
| API queries | 10/second | Per workspace |

## Instructions

### Step 1: Implement Token Bucket Rate Limiter
Build a rate limiter with configurable tokens per second, automatic refill, and async waiting when tokens are depleted.

### Step 2: Add Exponential Backoff
Create retry logic with configurable max retries, base delay, max delay, and jitter factor. Skip retries on client errors (4xx except 429).

### Step 3: Create Rate-Limited Client
Wrap the Customer.io client to acquire a rate limit token before each request and apply backoff on failures.

### Step 4: Handle 429 Response Headers
Parse `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` headers to adapt dynamically.

### Step 5: Add Queue-Based Rate Limiting
Use p-queue with interval-based rate limiting for cleaner high-volume processing.

For detailed implementation code, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Scenario | Action |
|----------|--------|
| 429 received | Respect Retry-After header |
| Burst traffic | Use queue with concurrency limit |
| Sustained high volume | Implement sliding window |

## Resources
- [API Rate Limits](https://customer.io/docs/api/track/#section/Limits)
- [Best Practices](https://customer.io/docs/best-practices/)

## Next Steps
After implementing rate limits, proceed to `customerio-security-basics` for security best practices.
