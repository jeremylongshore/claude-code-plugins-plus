---
name: clerk-multi-env-setup
description: |
  Configure Clerk for multiple environments (dev, staging, production).
  Use when setting up environment-specific configurations,
  managing multiple Clerk instances, or implementing environment promotion.
  Trigger with phrases like "clerk environments", "clerk staging",
  "clerk dev prod", "clerk multi-environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Multi-Environment Setup

## Overview
Configure Clerk across development, staging, and production environments.

## Prerequisites
- Clerk account with multiple instances
- Understanding of environment management
- CI/CD pipeline configured

## Instructions
1. Step 1: Create Clerk Instances
2. Step 2: Environment Configuration
3. Step 3: Environment-Aware Configuration
4. Step 4: ClerkProvider Configuration
5. Step 5: Webhook Configuration Per Environment
6. Step 6: CI/CD Environment Promotion
7. Step 7: User Data Isolation

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Separate Clerk instances per environment
- Environment-aware configuration
- Webhook handling per environment
- CI/CD pipeline configured

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Wrong environment keys | Misconfiguration | Validate at startup |
| Webhook signature fails | Wrong secret | Check env-specific secret |
| User not found | Env mismatch | Check environment isolation |

## Resources
- [Clerk Instances](https://clerk.com/docs/deployments/overview)
- [Environment Variables](https://clerk.com/docs/deployments/set-up-preview-environment)
- [Next.js Environments](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)

## Next Steps
Proceed to `clerk-observability` for monitoring and logging.

## Examples

**Basic usage**: Apply clerk multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk multi env setup for production environments with multiple constraints and team-specific requirements.