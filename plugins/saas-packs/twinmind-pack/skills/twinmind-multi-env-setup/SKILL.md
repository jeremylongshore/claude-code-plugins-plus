---
name: twinmind-multi-env-setup
description: |
  Set up TwinMind across multiple environments (dev, staging, production).
  Use when configuring environment-specific settings, managing multiple API keys,
  or implementing environment promotion workflows.
  Trigger with phrases like "twinmind environments", "twinmind multi-env",
  "twinmind staging setup", "twinmind dev vs prod".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# TwinMind Multi-Environment Setup

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure TwinMind for development, staging, and production environments with proper isolation, environment-aware client factory, validation scripts, config promotion workflows, and feature flags.

## Prerequisites
- Multiple TwinMind API keys (one per environment)
- Understanding of environment management
- CI/CD pipeline for deployments

## Instructions

### Step 1: Environment Configuration Structure
Define `EnvironmentConfig` interface covering TwinMind settings (API key, model, features, debug mode), rate limits, concurrency, daily quotas, and integration settings (Slack channel, calendar, email). Configure dev (ear-2, 30/min, quota 10), staging (ear-3, 60/min, quota 50), and production (ear-3, 300/min, unlimited).

### Step 2: Environment Variable Files
Create `.env.development`, `.env.staging`, `.env.production` with environment-specific API keys and webhook secrets. Commit `.env.example` with empty values.

### Step 3: Environment-Aware Client Factory
Build `getTwinMindClient()` factory that creates and caches clients per environment, automatically selecting the right API key and config.

### Step 4: Environment Validation
Create validation script that checks required environment variables, API key format (starts with `tm_sk_`), and API connectivity for each environment.

### Step 5: Config Promotion Workflow
Build `promoteConfig()` script to promote feature settings, webhook events, and integration configs from dev -> staging -> production while preserving environment-specific values.

### Step 6: Feature Flags per Environment
Implement `FeatureFlags` with environment overrides: beta features in dev only, diarization off in dev (faster), email follow-ups only in production, audio duration limits per environment.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete environment configs, client factory, validation scripts, promotion workflow, and feature flag code.

## Output
- Environment configuration structure
- Environment variable templates
- Client factory with environment awareness
- Environment validation script
- Config promotion workflow
- Feature flags per environment

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong API key used | Env mismatch | Validate before deploy |
| Feature not available | Wrong environment | Check feature flags |
| Config not loading | Missing file | Verify config paths |
| Promotion failed | Schema mismatch | Validate configs first |

## Examples
```typescript
// Get environment config
const config = getEnvironmentConfig();
console.log(`Environment: ${config.name}, Model: ${config.twinmind.model}`);

// Check feature flag
if (isFeatureEnabled('enableDiarization')) {
  options.diarization = true;
}

// Validate all environments
// $ ts-node scripts/validate-env.ts
// DEVELOPMENT: VALID
// STAGING: VALID
// PRODUCTION: VALID
```

## Environment Matrix

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Model | ear-2 | ear-3 | ear-3 |
| Diarization | Off | On | On |
| Debug mode | On | On | Off |
| Rate limit | 30/min | 60/min | 300/min |
| Email sending | Off | Off | On |

## Resources
- [12-Factor App Config](https://12factor.net/config)
- [Environment Best Practices](https://twinmind.com/docs/environments)

## Next Steps
For monitoring setup, see `twinmind-observability`.
