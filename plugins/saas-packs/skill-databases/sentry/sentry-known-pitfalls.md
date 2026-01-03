# sentry-known-pitfalls

## Skill Scaffold

```
sentry-known-pitfalls/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Common Sentry pitfalls and how to avoid them covering SDK initialization, error capture, configuration, performance, source maps, and monitoring anti-patterns.
**Workflow:** Reference during code review or when troubleshooting. Provides quick identification and resolution of common mistakes.
**Relates to:** Works with `sentry-common-errors` for troubleshooting. Complements all other skills by highlighting what not to do.

## Summary

This skill documents common mistakes and anti-patterns when using Sentry and how to avoid them. It covers SDK initialization pitfalls (late init, multiple init, wrong SDK), error capture pitfalls (swallowing errors, capturing non-errors, double capture), configuration pitfalls (hardcoded DSN, 100% sampling in production, ignoring beforeSend return), performance pitfalls, source maps pitfalls, integration pitfalls, and monitoring pitfalls. Use this as a reference to avoid common mistakes.
