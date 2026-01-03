# clay-reliability-patterns

## File Scaffold

```
clay-reliability-patterns/
|-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement Clay reliability patterns including circuit breakers, idempotency, and graceful degradation. Enables fault-tolerant enrichment operations.
**Workflow:** Reliability engineering skill. Use when building production-grade Clay integrations.
**Relates to:** Builds on clay-rate-limits; essential for clay-enterprise-rbac deployments.

## Summary

This skill implements reliability patterns for Clay integrations. It covers circuit breaker implementation to prevent cascade failures, idempotency keys to prevent duplicate enrichments, bulkhead isolation for different enrichment types, dead letter queues for failed operations, graceful degradation when Clay is unavailable, and fallback strategies for critical enrichments. Essential for production-grade deployments.
