# exa-security-basics

## Skill Scaffold

```
exa-security-basics/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Apply security best practices for API key management, secrets rotation, and secure request handling in Exa integrations.
**Workflow:** Security hardening skill - essential before production deployment.
**Relates to:** Follows exa-install-auth; precedes exa-prod-checklist

## Summary

This skill covers Exa security fundamentals: secure API key storage (never in code, use environment variables or secret managers), key rotation procedures and automation, environment-specific keys (dev/staging/prod), request logging without exposing keys, audit trails for API usage, access control patterns for multi-developer teams, and handling keys in CI/CD pipelines securely.
