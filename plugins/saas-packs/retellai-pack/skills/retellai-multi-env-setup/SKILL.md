---
name: retellai-multi-env-setup
description: |
  Configure Retell AI across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Retell AI configurations.
  Trigger with phrases like "retellai environments", "retellai staging",
  "retellai dev prod", "retellai environment setup", "retellai config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [retellai, voice-ai, saas]
---
# Retell AI Multi-Environment Setup

## Overview
Configure Retell AI across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage and ensure production hardening.

## Prerequisites
- Separate Retell AI API keys per environment
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
Set up a `config/retellai/` directory with base defaults and per-environment overrides. The base config defines shared settings like timeout and retry counts. See [environment configs](references/environment-configs.md) for the full TypeScript configuration structure.

### Step 2: Implement Environment Resolver
Create an auto-detection function that determines the current environment from `NODE_ENV` or platform-specific variables (e.g., `VERCEL_ENV`). Throw an error at startup if the API key is missing for the detected environment.

### Step 3: Configure Secrets Per Platform
Store API keys using the appropriate mechanism for each environment: `.env.local` for development, GitHub Actions environment secrets for CI/CD, and AWS Secrets Manager or GCP Secret Manager for production. See [environment configs](references/environment-configs.md) for platform-specific commands.

### Step 4: Add Startup Validation
Use Zod schema validation at application startup to catch missing or malformed configuration early, before the first API call fails. This prevents silent misconfigurations from reaching production.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment detected | Missing NODE_ENV | Set environment variable explicitly in deployment |
| Secret not found | Wrong secret path | Verify secret manager configuration and IAM roles |
| Cross-env data leak | Shared API key | Use separate keys per environment, audit regularly |
| Config validation fail | Missing field | Add startup validation with Zod schema |

## Examples

### Quick Environment Check
```typescript
const config = getRetellAIConfig();
console.log(`Running in ${config.environment}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

For complete TypeScript configs, resolver code, CI/CD workflow YAML, and Zod validation, see [environment configs](references/environment-configs.md).

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [Retell AI Agents](https://docs.retellai.com/agents)

## Output
- Environment-specific configuration files created in `config/retellai/`
- Auto-detection resolver selecting correct environment at startup
- Per-environment secrets stored in appropriate secret managers
- Zod-validated startup checks preventing misconfiguration
- Isolated API keys ensuring no cross-environment data leakage

## Next Steps
For deployment to specific platforms (Fly.io, Cloud Run), see `retellai-deploy-integration`. For security hardening of API keys, see `retellai-security-basics`.
