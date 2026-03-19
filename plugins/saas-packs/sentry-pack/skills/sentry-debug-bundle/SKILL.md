---
name: sentry-debug-bundle
description: |
  Execute collect debug information for Sentry support tickets.
  Use when preparing support requests, debugging complex issues,
  or gathering diagnostic information.
  Trigger with phrases like "sentry debug info", "sentry support ticket",
  "gather sentry diagnostics", "sentry debug bundle".
allowed-tools: Read, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Prerequisites

- Debug mode enabled in SDK
- Sentry CLI installed for source map diagnostics
- Access to environment variables
- Application logs available

## Instructions

1. Run npm list to get SDK version for all Sentry packages
2. Create debug config export with DSN redacted for sharing
3. Test network connectivity to sentry.io API endpoint
4. Capture test event and record event ID
5. Check integrations loaded with getIntegrations call
6. Run debug script to collect comprehensive diagnostic info
7. Format output in markdown template for support ticket
8. List uploaded source maps using sentry-cli releases files
9. Use sentry-cli sourcemaps explain for specific event debugging
10. Include relevant logs and reproduction steps in debug bundle

## Output
- Debug information bundle generated
- SDK version and configuration documented
- Network connectivity verified
- Test event capture confirmed

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Support](https://sentry.io/support/)
- [Sentry GitHub Issues](https://github.com/getsentry/sentry-javascript/issues)

## Overview

Execute collect debug information for Sentry support tickets.