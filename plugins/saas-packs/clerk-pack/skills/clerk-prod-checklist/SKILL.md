---
name: clerk-prod-checklist
description: |
  Production readiness checklist for Clerk deployment.
  Use when preparing to deploy, reviewing production configuration,
  or auditing Clerk implementation before launch.
  Trigger with phrases like "clerk production", "clerk deploy checklist",
  "clerk go-live", "clerk launch ready".
allowed-tools: Read, Write, Edit, Grep, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Production Checklist

## Overview
Complete checklist to ensure your Clerk integration is production-ready.

## Prerequisites
- Clerk integration working in development
- Production environment configured
- Domain and hosting ready

## Instructions
- Production Checklist
- Validation Script

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Complete production configuration
- Security hardening applied
- Monitoring configured
- Testing completed

## Resources
- [Clerk Production Checklist](https://clerk.com/docs/deployments/overview)
- [Security Best Practices](https://clerk.com/docs/security/overview)
- [Performance Guide](https://clerk.com/docs/quickstarts/nextjs)

## Next Steps
Proceed to `clerk-upgrade-migration` for SDK version upgrades.
