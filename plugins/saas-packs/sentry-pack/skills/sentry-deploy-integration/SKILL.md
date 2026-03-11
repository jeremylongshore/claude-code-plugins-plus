---
name: sentry-deploy-integration
description: |
  Track deployments and releases in Sentry.
  Use when configuring deployment tracking, release health,
  or connecting deployments to error data.
  Trigger with phrases like "sentry deploy tracking", "sentry release health",
  "track deployments sentry", "sentry deployment notification".
allowed-tools: Read, Write, Edit, Bash(sentry-cli:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Deploy Integration

## Prerequisites

- Sentry CLI installed
- `SENTRY_AUTH_TOKEN` configured
- Build pipeline access
- Source maps generated during build

## Instructions

1. Create release using git SHA or semantic version with sentry-cli
2. Upload source maps from build output directory
3. Associate commits using sentry-cli releases set-commits --auto
4. Finalize the release to mark it complete
5. Deploy application to target environment
6. Notify Sentry of deployment with environment and timestamps
7. Enable session tracking for release health metrics
8. Configure environment-specific sample rates
9. Set up rollback tracking to record version changes
10. Use Sentry dashboard to compare releases and monitor health

## Output
- Releases created for each deployment
- Source maps uploaded and linked
- Deployment notifications sent
- Release health metrics tracked

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Releases](https://docs.sentry.io/product/releases/)
- [Release Health](https://docs.sentry.io/product/releases/health/)
