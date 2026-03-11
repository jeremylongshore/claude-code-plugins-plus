---
name: vercel-multi-env-setup
description: |
  Configure Vercel across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Vercel configurations.
  Trigger with phrases like "vercel environments", "vercel staging",
  "vercel dev prod", "vercel environment setup", "vercel config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Multi Env Setup

## Prerequisites
- Separate Vercel accounts or API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, etc.)
- CI/CD pipeline with environment variables
- Environment detection in application

## Instructions

### Step 1: Create Config Structure
Set up the base and per-environment configuration files.

### Step 2: Implement Environment Detection
Add logic to detect and load environment-specific config.

### Step 3: Configure Secrets
Store API keys securely using your secret management solution.

### Step 4: Add Environment Guards
Implement safeguards for production-only operations.

## Output
- Multi-environment config structure
- Environment detection logic
- Secure secret management
- Production safeguards enabled

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Environments Guide](https://vercel.com/docs/environments)
- [12-Factor App Config](https://12factor.net/config)
