# vercel-multi-env-setup

## Skill Scaffold

```
vercel-multi-env-setup/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure Vercel across development, staging, and production environments with secure secret management.
**Workflow:** Used during initial project setup and when adding new environments.
**Relates to:** Follows vercel-reference-architecture; complements vercel-observability for monitoring

## Summary

This skill addresses multi-environment configuration for Vercel. It covers environment strategy (dev/staging/prod with different API keys), configuration file structure with base and override patterns, environment detection logic, secret management for each context (local .env, GitHub Actions, Vault/Secrets Manager), environment isolation guards to prevent dangerous operations in wrong environments, and feature flags per environment. The goal is zero cross-environment configuration incidents.
