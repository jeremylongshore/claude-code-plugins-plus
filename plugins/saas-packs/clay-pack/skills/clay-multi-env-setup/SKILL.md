---
name: clay-multi-env-setup
description: |
  Configure Clay across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Clay configurations.
  Trigger with phrases like "clay environments", "clay staging",
  "clay dev prod", "clay environment setup", "clay config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Multi-Environment Setup

## Overview

Configure Clay across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management.

## Prerequisites

- Separate Clay API keys per environment
- Secret management solution (environment variables, Vault, or cloud secrets)
- CI/CD pipeline with environment-aware deployment
- Application with environment detection logic

## Environment Strategy

| Environment | Purpose | API Key Source | Settings |
|-------------|---------|---------------|----------|
| Development | Local development | `.env.local` | Debug enabled, relaxed limits |
| Staging | Pre-production testing | CI/CD secrets | Production-like settings |
| Production | Live traffic | Secret manager | Optimized, hardened |

## Instructions

### Step 1: Create Configuration Structure

Create `config/clay/` with `base.ts` (shared defaults), per-environment override files, and an `index.ts` resolver.

### Step 2: Define Base and Environment Configs

Base config sets timeout (30s), retries (3), and cache (5 min TTL). Dev disables cache and enables debug. Prod extends timeout to 60s, retries to 5, and cache TTL to 10 min.

### Step 3: Implement Environment Detection

Detect environment from `NODE_ENV` and `VERCEL_ENV`. Throw if API key is missing for the detected environment.

### Step 4: Configure Secret Management

Store keys in `.env.local` (dev), GitHub Environment Secrets (staging/prod), or cloud secret managers (AWS/GCP). Reference in CI workflows per environment.

### Step 5: Add Startup Validation

Use Zod to validate config at startup, ensuring API key is set, environment is valid, and timeout is positive.

For detailed TypeScript implementations and CI workflow configs, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing NODE_ENV | Set environment variable in deployment |
| Secret not found | Wrong secret path | Verify secret manager configuration |
| Cross-env data leak | Shared API key | Use separate keys per environment |
| Config validation fail | Missing field | Add startup validation with Zod schema |

## Resources

- [Clay API Documentation](https://docs.clay.com/api)
- [Clay Environments](https://docs.clay.com/environments)

## Next Steps

For deployment, see `clay-deploy-integration`.
