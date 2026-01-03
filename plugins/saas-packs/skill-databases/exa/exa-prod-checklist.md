# exa-prod-checklist

## Skill Scaffold

```
exa-prod-checklist/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Execute production deployment checklist for Exa integrations including pre-flight checks, monitoring setup, and fallback procedures.
**Workflow:** Final operations skill before production launch - ensures deployment readiness.
**Relates to:** Follows exa-security-basics; precedes exa-observability

## Summary

This skill provides a comprehensive production checklist: API key configured in production secrets manager, rate limit handling tested under load, error handling and fallbacks verified, monitoring and alerting configured, health check endpoint implemented, cache layer configured, logging sanitized (no keys exposed), fallback procedure documented and tested, and rollback procedure prepared. Includes verification commands for each checkpoint.
