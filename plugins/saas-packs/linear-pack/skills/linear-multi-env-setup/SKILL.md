---
name: linear-multi-env-setup
description: |
  Configure Linear across development, staging, and production environments.
  Use when setting up multi-environment deployments, managing per-environment API keys,
  or implementing environment-specific Linear configurations.
  Trigger with phrases like "linear environments", "linear staging",
  "linear dev prod", "linear environment setup", "multi-environment linear".
allowed-tools: Read, Write, Edit, Bash(vault:*), Bash(gcloud:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Multi-Environment Setup

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure Linear integrations across development, staging, and production environments with proper secret management and environment guards.

## Prerequisites
- Separate Linear workspaces or API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)
- CI/CD pipeline with environment variables
- Environment detection in application

## Instructions

### Step 1: Define Environment Config Structure
Create typed config with per-environment API keys, webhook secrets, team keys, and feature flags (e.g., disable webhooks in dev, enable debug in staging).

### Step 2: Integrate Secret Management
Use Vault, AWS Secrets Manager, or GCP Secret Manager to store API keys securely. Fetch secrets at runtime in production.

### Step 3: Build Environment-Aware Client Factory
Singleton client that auto-configures based on `NODE_ENV` with test injection support.

### Step 4: Add Environment Guards
- `requireProduction()` for prod-only operations
- `preventProduction()` for dangerous dev operations
- `safeDeleteIssue()` that archives in prod, deletes in dev

### Step 5: Configure Per-Environment Webhooks
Dev uses polling (localhost), staging uses full event set, production adds Label events.

### Step 6: Set Up CI/CD
GitHub Actions with environment-scoped secrets for staging (main branch) and production (release branches).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for full code examples including secret manager integrations and CI/CD workflows.

## Output
- Environment-specific configuration active
- Secrets managed securely per environment
- Environment guards preventing accidental cross-env operations
- CI/CD deploying to correct environments

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Wrong environment | API key mismatch | Verify secrets for correct env |
| Secret not found | Missing secret | Add secret to secret manager |
| Team not found | Wrong workspace | Check defaultTeamKey setting |
| Permission denied | Insufficient scope | Regenerate API key |

## Examples

### Validate Environment
```bash
NODE_ENV=staging npx ts-node scripts/validate-environment.ts
# Output: API Key: Valid, Default Team: Found, Webhook Secret: Set
```

## Resources
- [Linear API Authentication](https://developers.linear.app/docs/graphql/authentication)
- [12-Factor App Config](https://12factor.net/config)
- [HashiCorp Vault](https://www.vaultproject.io/docs)

## Next Steps
Set up observability with `linear-observability`.