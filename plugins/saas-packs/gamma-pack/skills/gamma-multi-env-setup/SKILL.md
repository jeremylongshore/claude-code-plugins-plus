---
name: gamma-multi-env-setup
description: |
  Configure Gamma across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Gamma configurations.
  Trigger with phrases like "gamma environments", "gamma staging",
  "gamma dev prod", "gamma environment setup", "gamma config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Gamma Multi-Environment Setup

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure Gamma across development, staging, and production environments with proper isolation, secrets management, and environment guards.

## Prerequisites
- Separate Gamma API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, etc.)
- CI/CD pipeline with environment variables
- Environment detection in application

## Instructions

### Step 1: Create Environment Configuration
Define per-environment settings (timeout, retries, debug mode) in a typed configuration object. Use `NODE_ENV` to select the active config.

### Step 2: Configure Per-Environment API Keys
Store separate API keys in `.env.development`, `.env.staging`, and `.env.production` files. Never commit keys to version control.

### Step 3: Integrate Secret Management
For production, use AWS Secrets Manager or Vault to fetch keys at runtime with caching (5-minute TTL recommended).

### Step 4: Build a Client Factory
Create a singleton factory that returns environment-aware Gamma clients. Production clients should fetch keys from secret manager; dev/staging can use env vars.

### Step 5: Add Environment Guards
Implement `requireProduction()` and `blockProduction()` guards to prevent destructive operations in the wrong environment.

### Step 6: Configure CI/CD
Set up GitHub Actions (or equivalent) with separate deployment jobs per environment, each using environment-specific secrets.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Environment-specific configuration files
- Secret management integration
- Client factory with environment detection
- CI/CD pipeline with environment isolation

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong API key used | Env var mismatch | Verify `NODE_ENV` matches key prefix |
| Secret fetch fails | IAM permissions | Check secrets manager access policy |
| Production data in dev | No env guard | Add `blockProduction()` guards |

## Examples

### Environment Checklist
| Check | Dev | Staging | Prod |
|-------|-----|---------|------|
| Separate API key | Yes | Yes | Yes |
| Debug logging | On | On | Off |
| Mock mode available | Yes | Yes | No |
| Secret manager | No | Yes | Yes |
| Rate limit tier | Low | Medium | High |

## Resources
- [Gamma Environments Guide](https://gamma.app/docs/environments)
- [12-Factor App Config](https://12factor.net/config)
