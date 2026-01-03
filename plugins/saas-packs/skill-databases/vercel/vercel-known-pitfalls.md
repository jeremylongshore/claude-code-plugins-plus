# vercel-known-pitfalls

## Skill Scaffold

```
vercel-known-pitfalls/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Identify and avoid 10 common anti-patterns including sync calls in request path, rate limit ignoring, and key leakage.
**Workflow:** Reference during code development and code review to catch common mistakes.
**Relates to:** Final skill in advanced track; synthesizes learnings from all other skills

## Summary

This skill documents the 10 most common mistakes in Vercel integrations. Each pitfall shows the anti-pattern code, explains why it's problematic, and provides the better approach. Covered pitfalls: synchronous API calls in request path, not handling rate limits, leaking API keys, ignoring idempotency, not validating webhooks, missing error handling, hardcoding configuration, no circuit breaker, logging sensitive data, and no graceful degradation. The quick reference card provides detection and prevention strategies for each.
