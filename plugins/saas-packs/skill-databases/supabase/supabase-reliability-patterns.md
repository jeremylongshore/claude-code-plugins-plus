# supabase-reliability-patterns

## File Scaffold

```
supabase-reliability-patterns/
-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement Supabase reliability patterns including circuit breaker with opossum, idempotency keys, bulkhead isolation, timeout hierarchy, graceful degradation, and dead letter queues.
**Workflow:** Reliability engineering skill. Essential for production-grade fault tolerance.
**Relates to:** Builds on supabase-load-scale; enables supabase-policy-guardrails for enforcement.

## Summary

This skill provides production-grade reliability patterns for Supabase integrations. It covers circuit breaker implementation with opossum, idempotency key generation, bulkhead pattern with p-queue, timeout hierarchy for different operation types, graceful degradation with fallback strategies, and dead letter queue for failed operations. Use this skill when building fault-tolerant Supabase integrations or adding resilience to production services.
