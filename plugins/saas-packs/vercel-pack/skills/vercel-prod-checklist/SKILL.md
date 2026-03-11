---
name: vercel-prod-checklist
description: |
  Execute Vercel production deployment checklist and rollback procedures.
  Use when deploying Vercel integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "vercel production", "deploy vercel",
  "vercel go-live", "vercel launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Prod Checklist

## Prerequisites
- Staging environment tested and verified
- Production API keys available
- Deployment pipeline configured
- Monitoring and alerting ready


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Deployed Vercel integration
- Health checks passing
- Monitoring active
- Rollback procedure documented

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Status](https://www.vercel-status.com)
- [Vercel Support](https://vercel.com/docs/support)
