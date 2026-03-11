---
name: lindy-multi-env-setup
description: |
  Configure Lindy AI across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Lindy configurations.
  Trigger with phrases like "lindy environments", "lindy staging",
  "lindy dev prod", "lindy environment setup", "lindy config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy AI Multi-Environment Setup

## Overview
Configure Lindy AI across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage.

## Prerequisites
- Separate Lindy AI API keys per environment
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

### Step 1: Configuration Structure
### Step 2: Base Configuration
### Step 3: Environment-Specific Configs
### Step 4: Environment Resolver
### Step 5: Secret Management

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing NODE_ENV | Set environment variable in deployment |
| Secret not found | Wrong secret path | Verify secret manager configuration |
| Cross-env data leak | Shared API key | Use separate keys per environment |
| Config validation fail | Missing field | Add startup validation with Zod schema |

## Examples

### Quick Environment Check
### Startup Validation
## Resources
- [Lindy AI Documentation](https://docs.lindy.ai)
- [Lindy API Reference](https://docs.lindy.ai/api)

## Next Steps
For deployment, see `lindy-deploy-integration`.
