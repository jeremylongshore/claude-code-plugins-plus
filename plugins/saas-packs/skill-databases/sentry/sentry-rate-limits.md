# sentry-rate-limits

## Skill Scaffold

```
sentry-rate-limits/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Manage Sentry rate limits and quota optimization through error sampling, transaction sampling, ignoring common errors, and client-side filtering.
**Workflow:** Use when hitting rate limits or proactively managing event volume. Implements strategies to reduce events while maintaining visibility.
**Relates to:** Works with `sentry-cost-tuning` for cost management. Connects to `sentry-load-scale` for high-volume applications.

## Summary

This skill helps manage event volume and avoid hitting Sentry rate limits. It covers understanding different types of rate limits, error sampling strategies, transaction sampling, ignoring common noisy errors, deduplication, client-side filtering, and server-side controls. Use this skill when experiencing 429 errors or proactively optimizing quota usage.
