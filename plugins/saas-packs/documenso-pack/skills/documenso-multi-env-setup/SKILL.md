---
name: documenso-multi-env-setup
description: |
  Configure Documenso across multiple environments (dev, staging, production).
  Use when setting up environment-specific configurations, managing API keys,
  or implementing environment promotion workflows.
  Trigger with phrases like "documenso environments", "documenso staging",
  "documenso dev setup", "multi-environment documenso".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Documenso Multi-Environment Setup

## Overview
Configure and manage Documenso integrations across development, staging, and production environments with proper isolation and promotion workflows.

## Prerequisites
- Documenso accounts for each environment (or self-hosted instances)
- Environment management infrastructure
- Secret management solution (Vault, AWS Secrets Manager, etc.)

## Instructions

### Step 1: Environment Architecture
┌─────────────────────────────────────────────────────────┐
### Step 2: Configuration Files
// config/documenso.development.json
### Step 3: Environment Variables
NODE_ENV=development
### Step 4: Client Factory
// src/documenso/factory.ts
### Step 5: Mock Client for Development
// src/documenso/mock.ts
### Step 6: Environment Promotion
// scripts/promote-templates.ts
### Step 7: Webhook Configuration Per Environment
// src/webhooks/config.ts
### Step 8: Testing Across Environments
// tests/integration/environment.test.ts

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Environment Architecture
- Configuration Files
- Environment Variables
- Client Factory
- Mock Client for Development
- Environment Promotion

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing NODE_ENV | Set explicitly |
| Key mismatch | Using wrong key | Check env var names |
| Config not loading | File path wrong | Verify config files |
| Mock not working | mockEnabled: false | Enable in dev config |

## Resources
- [12-Factor App Config](https://12factor.net/config)
- [Environment Management](https://docs.documenso.com/developers)
- [Secret Management Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Next Steps
For monitoring setup, see `documenso-observability`.
