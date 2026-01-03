# supabase-rate-limits

## File Scaffold

```
supabase-rate-limits/
-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement Supabase rate limiting, backoff, and idempotency patterns. Handles 429 errors gracefully with exponential backoff and jitter.
**Workflow:** Operational skill for production reliability. Should be implemented before going to production.
**Relates to:** Complements supabase-sdk-patterns with rate limit handling; prerequisite for supabase-prod-checklist.

## Summary

This skill provides comprehensive guidance on handling Supabase rate limits. It covers understanding rate limit tiers, implementing exponential backoff with jitter, adding idempotency keys for safe retries, queue-based rate limiting, and monitoring rate limit usage. Use this skill when experiencing 429 errors, implementing retry logic, or preparing for production deployment.
