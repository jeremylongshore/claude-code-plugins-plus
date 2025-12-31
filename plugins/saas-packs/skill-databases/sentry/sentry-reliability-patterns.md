# sentry-reliability-patterns

## Skill Scaffold

```
sentry-reliability-patterns/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Build reliable Sentry integrations with graceful degradation, retry logic, circuit breaker patterns, and health checks to ensure monitoring uptime.
**Workflow:** Implement during production hardening. Ensures the application continues functioning even if Sentry has issues.
**Relates to:** Works with `sentry-load-scale` for high-volume. Connects to `sentry-advanced-troubleshooting` for diagnosis.

## Summary

This skill builds reliable Sentry integrations that handle failures gracefully. It covers graceful degradation on SDK initialization failure, network failure handling with retry and backoff, offline event queue, circuit breaker pattern, timeout handling, graceful shutdown, dual-write pattern for redundancy, and health check endpoints. Use this skill when reliability of the monitoring system is critical.
