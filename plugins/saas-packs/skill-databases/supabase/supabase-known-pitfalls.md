# supabase-known-pitfalls

## File Scaffold

```
supabase-known-pitfalls/
-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Identify and avoid the top 10 Supabase anti-patterns including synchronous API calls in request path, rate limit ignoring, key leakage, missing idempotency, and more.
**Workflow:** Final advanced skill. Used for code review and onboarding.
**Relates to:** Culmination of all patterns; used to validate implementations against all previous skills.

## Summary

This skill provides a comprehensive reference of common mistakes and anti-patterns in Supabase integrations. It covers synchronous API calls in request path, rate limit ignoring, API key leakage, missing idempotency, unverified webhooks, missing error handling, hardcoded configuration, no circuit breaker, logging sensitive data, and no graceful degradation. Each pitfall includes the anti-pattern, better approach, and detection methods. Use this skill when reviewing Supabase code or onboarding new developers.
