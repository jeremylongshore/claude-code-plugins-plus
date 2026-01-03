# exa-rate-limits

## Skill Scaffold

```
exa-rate-limits/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement rate limiting, exponential backoff with jitter, and request queuing for reliable Exa API usage.
**Workflow:** Essential operations skill - prevents rate limit issues before they occur.
**Relates to:** Follows exa-sdk-patterns; foundational for exa-reliability-patterns

## Summary

This skill implements robust rate limit handling for Exa API: understanding Exa's rate limit headers, implementing exponential backoff with jitter, request queuing for burst protection, client-side rate limiting to stay under quotas, graceful degradation when limits are hit, and monitoring/alerting for rate limit events. Includes patterns for both synchronous and asynchronous usage.
