# sentry-multi-env-setup

## Skill Scaffold

```
sentry-multi-env-setup/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure Sentry across multiple environments with proper isolation, environment-specific sample rates, and DSN management strategies.
**Workflow:** Configure during initial setup or when adding new environments. Ensures proper separation between dev, staging, and production.
**Relates to:** Works with `sentry-local-dev-loop` for development. Connects to `sentry-reference-architecture` for overall design.

## Summary

This skill configures Sentry properly across development, staging, and production environments. It covers environment configuration, environment-specific sample rates, project structure options (single project vs multiple), DSN management, filtering by environment, and environment-specific alert rules. Use this skill when setting up multi-environment Sentry with proper data isolation.
