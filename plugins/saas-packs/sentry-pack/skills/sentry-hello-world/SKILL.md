---
name: sentry-hello-world
description: |
  Execute capture your first error with Sentry and verify it appears in the dashboard.
  Use when testing Sentry integration or verifying error capture works.
  Trigger with phrases like "test sentry", "sentry hello world",
  "verify sentry", "first sentry error".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(python:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Hello World

## Prerequisites
- Sentry SDK installed and initialized
- Valid DSN configured
- Network access to Sentry servers

## Instructions

1. Open https://sentry.io
2. Navigate to your project
3. Check Issues tab for the test error
4. Verify event details are correct


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Test error visible in Sentry dashboard
- Event contains stack trace and metadata
- User context and tags attached to event

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Error Capture](https://docs.sentry.io/platforms/javascript/usage/)
- [Sentry Context](https://docs.sentry.io/platforms/javascript/enriching-events/context/)
