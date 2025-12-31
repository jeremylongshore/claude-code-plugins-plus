# vercel-rate-limits

## Skill Scaffold

```
vercel-rate-limits/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement rate limiting, exponential backoff with jitter, and idempotency patterns for Vercel API interactions.
**Workflow:** Applied during initial integration development and when encountering 429 errors.
**Relates to:** Complements vercel-sdk-patterns; monitoring aspects connect to vercel-observability

## Summary

This skill addresses rate limit handling for Vercel APIs. It covers understanding tier-based limits (Hobby, Pro, Enterprise), implementing exponential backoff with jitter to prevent thundering herd problems, using idempotency keys for safe retries, and queue-based rate limiting with p-queue. The monitoring component tracks rate limit headers to proactively throttle before hitting limits.
