---
name: guidewire-rate-limits
description: |
  Manage Guidewire Cloud API rate limits, quotas, and throttling.
  Use when encountering 429 errors, optimizing API call patterns,
  or implementing rate limit handling strategies.
  Trigger with phrases like "guidewire rate limit", "api quota",
  "429 error", "throttling", "api limits guidewire".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Guidewire Rate Limits

## Overview

Understand and manage Guidewire Cloud API rate limits, implement proper throttling, and optimize API usage patterns.

## Prerequisites

- Understanding of HTTP rate limiting concepts
- Access to Guidewire Cloud Console for quota monitoring
- Familiarity with exponential backoff patterns

## Default Limits (Guidewire Cloud)

| Limit Type | Default Value | Scope |
|------------|---------------|-------|
| Requests per second | 50 | Per tenant |
| Requests per minute | 1,000 | Per tenant |
| Requests per hour | 30,000 | Per tenant |
| Concurrent requests | 25 | Per application |
| Payload size | 10 MB | Per request |
| Query result limit | 1,000 | Per request |

## Instructions

### Step 1: Monitor Rate Limit Headers

Parse `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers from every response. Warn when remaining drops below 10% of the limit.

### Step 2: Implement Exponential Backoff

On 429 responses, use exponential backoff with jitter. Respect the `Retry-After` header when present. Start at 1s delay, max 60s, with 10% jitter.

### Step 3: Implement Request Queue

Use a queue (e.g., `p-queue`) to throttle requests to 80% of the per-second limit. Batch related items and add delays between batches.

### Step 4: Optimize API Patterns

- Use `?include=` to fetch related entities in one call instead of multiple
- Use server-side `?filter=` instead of client-side filtering
- Use pagination with `pageSize=100` for bulk retrieval

### Step 5: Implement Circuit Breaker

Open the circuit after 5 consecutive 429 errors. Wait 60s before half-open probe. Close after 3 successful requests.

For detailed implementation code (TypeScript and Gosu), load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Rate limit tracking and monitoring
- Exponential backoff implementation
- Request queue with throttling
- Circuit breaker protection

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded rate limit | Implement backoff, check headers |
| `503 Service Unavailable` | Temporary overload | Retry with backoff |
| Circuit breaker open | Repeated failures | Wait for reset timeout |
| Queue timeout | Backpressure | Increase queue capacity |

## Resources

- [Guidewire Cloud API Limits](https://docs.guidewire.com/cloud/)
- [Rate Limiting Best Practices](https://developer.guidewire.com/)

## Next Steps

For security implementation, see `guidewire-security-basics`.
