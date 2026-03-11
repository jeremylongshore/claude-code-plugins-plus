---
name: juicebox-multi-env-setup
description: |
  Configure Juicebox multi-environment setup.
  Use when setting up dev/staging/production environments,
  managing per-environment configurations, or implementing environment isolation.
  Trigger with phrases like "juicebox environments", "juicebox staging",
  "juicebox dev prod", "juicebox environment setup".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Multi-Environment Setup

## Overview
Configure Juicebox across development, staging, and production environments with proper isolation and security.

## Prerequisites
- Separate Juicebox accounts or API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, etc.)
- CI/CD pipeline with environment variables
- Environment detection in application

## Instructions
1. Step 1: Environment Configuration
2. Step 2: Secret Management by Environment
3. Step 3: Environment-Aware Client Factory
4. Step 4: Kubernetes ConfigMaps
5. Step 5: Environment Guards

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Environment-specific configurations
- Secret management per environment
- Kubernetes overlays
- Environment guards

## Resources
- [Multi-Environment Guide](https://juicebox.ai/docs/environments)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
After environment setup, see `juicebox-observability` for monitoring.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Juicebox Multi Env Setup |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox multi env setup for production environments with multiple constraints and team-specific requirements.