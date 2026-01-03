# exa-reliability-patterns

## Skill Scaffold

```
exa-reliability-patterns/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement circuit breakers, fallback search providers, and graceful degradation for Exa reliability.
**Workflow:** Resilience engineering skill - ensures search availability during outages.
**Relates to:** Follows exa-rate-limits; provides patterns for exa-incident-runbook

## Summary

This skill implements reliability patterns: circuit breaker for Exa API calls (opossum, resilience4j), fallback provider configuration (cached results, secondary search), bulkhead isolation for different search types, graceful degradation strategies (reduced features vs complete failure), dead letter queue for failed requests, retry with fallback chains, health-based routing, and chaos testing patterns. Target: 99.9% search availability through fallback activation.
