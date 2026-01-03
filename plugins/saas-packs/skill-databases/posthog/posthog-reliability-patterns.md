# posthog-reliability-patterns

> Implement reliability patterns for PostHog including graceful degradation retry logic and data buffering

## Directory Structure

```
posthog-reliability-patterns/
├── SKILL.md
└── examples/
    ├── resilient_client.ts
    ├── offline_buffer.py
    ├── circuit_breaker.md
    └── fallback_strategies.md
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for PostHog reliability implementation |
| resilient_client.ts | TypeScript | Resilient PostHog client wrapper with retry logic |
| offline_buffer.py | Python | Offline event buffer for handling PostHog outages |
| circuit_breaker.md | Markdown | Circuit breaker pattern for PostHog calls |
| fallback_strategies.md | Markdown | Graceful degradation strategies when PostHog is unavailable |

## Summary

**Category:** Advanced
**Target Audience:** Platform engineers implementing resilient applications with PostHog dependencies
**Trigger Phrases:** "posthog reliability", "posthog offline", "posthog retry", "resilient posthog", "posthog graceful degradation", "posthog circuit breaker"

---

**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**License:** MIT
**Version:** 1.0.0
