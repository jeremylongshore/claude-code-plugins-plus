# clay-rate-limits

## File Scaffold

```
clay-rate-limits/
|-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement Clay rate limiting, backoff strategies, and credit management patterns. Ensures reliable API usage while optimizing credit consumption.
**Workflow:** Reliability pattern skill. Use when building production integrations that need to handle rate limits gracefully.
**Relates to:** Builds on clay-enrichment-patterns; essential for clay-load-scale and high-volume operations.

## Summary

This skill implements robust rate limit handling for Clay API integrations. It covers reading rate limit headers, implementing exponential backoff with jitter, managing credit budgets, creating request queues for high-volume operations, and implementing idempotency to prevent duplicate enrichments. These patterns ensure reliable operation even under heavy load.
