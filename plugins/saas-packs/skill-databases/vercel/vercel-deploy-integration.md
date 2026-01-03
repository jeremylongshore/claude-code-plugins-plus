# vercel-deploy-integration

## Skill Scaffold

```
vercel-deploy-integration/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Deploy Vercel integrations to Vercel, Fly.io, and Cloud Run with proper secrets management.
**Workflow:** Used for initial deployment and when migrating between platforms.
**Relates to:** Follows vercel-ci-integration; complements vercel-webhooks-events for event handling

## Summary

This skill provides deployment guides for three major platforms: Vercel itself, Fly.io, and Google Cloud Run. Each platform section covers secrets configuration using the platform's native secret management, deployment commands, configuration files (vercel.json, fly.toml, Dockerfile), and health check endpoint implementation. The environment configuration pattern ensures consistent API key handling across all platforms.
