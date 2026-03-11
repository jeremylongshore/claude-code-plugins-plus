---
name: sentry-prod-checklist
description: |
  Execute production deployment checklist for Sentry integration.
  Use when preparing for production deployment, reviewing
  Sentry configuration, or verifying production readiness.
  Trigger with phrases like "sentry production", "deploy sentry",
  "sentry checklist", "sentry go-live".
allowed-tools: Read, Grep, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Prod Checklist

## Prerequisites

- Sentry account with project created
- Production DSN separate from development/staging
- Build pipeline with source map generation
- sentry-cli installed and configured with auth token

## Instructions

1. Configure production DSN via environment variables (never hardcode)
2. Set environment to "production" and configure release version
3. Generate source maps during build process
4. Upload source maps using sentry-cli releases commands
5. Verify security settings (sendDefaultPii: false, debug: false)
6. Configure appropriate sample rates for production volume
7. Set up alert rules with team notification channels
8. Connect source control and issue tracker integrations
9. Run verification test to confirm error capture and source maps
10. Document rollback procedure for emergency disable

## Output

- Production-ready Sentry configuration
- Verified source map uploads
- Configured alert rules and notifications
- Documented release workflow
- Validated error capture with test events

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Production Checklist](https://docs.sentry.io/product/releases/setup/)
- [Sentry Release Health](https://docs.sentry.io/product/releases/health/)

## Overview

Execute production deployment checklist for Sentry integration.