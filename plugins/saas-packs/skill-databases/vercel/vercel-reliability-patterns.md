# vercel-reliability-patterns

## Skill Scaffold

```
vercel-reliability-patterns/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement circuit breakers, idempotency, bulkhead pattern, dead letter queues, and graceful degradation.
**Workflow:** Applied during production hardening phase after basic integration works.
**Relates to:** Follows vercel-load-scale; leads to vercel-policy-guardrails for governance

## Summary

This skill provides production-grade reliability patterns for Vercel. It covers circuit breaker implementation with opossum including state events, idempotency key generation (deterministic and random), bulkhead pattern with separate queues for different priorities, timeout hierarchy for different operation types, graceful degradation with fallback functions, dead letter queue implementation for failed operations, and health checks with degraded state support. The goal is zero cascading failures.
