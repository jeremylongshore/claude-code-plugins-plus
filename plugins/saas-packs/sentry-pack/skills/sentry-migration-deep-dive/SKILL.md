---
name: sentry-migration-deep-dive
description: |
  Execute migrate to Sentry from other error tracking tools.
  Use when migrating from Rollbar, Bugsnag, Raygun,
  or other error tracking solutions.
  Trigger with phrases like "migrate to sentry", "sentry migration",
  "switch from rollbar to sentry", "replace bugsnag with sentry".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Prerequisites

- Current error tracking tool access
- Sentry project created
- API access to old tool (for data export)
- Parallel run timeline established

## Instructions

1. Complete assessment phase documenting current tool usage
2. Set up Sentry projects matching existing structure
3. Install Sentry SDK alongside existing tool for parallel running
4. Map feature equivalents between old tool and Sentry APIs
5. Run both tools in parallel for 2-4 weeks
6. Compare error capture rates and verify parity
7. Recreate alert rules in Sentry matching old tool
8. Export historical data from old tool API if needed
9. Remove old SDK dependencies and configuration
10. Train team on Sentry dashboard and cancel old subscription

## Output
- SDK migration complete
- Historical data exported (if needed)
- Alert rules recreated
- Team transitioned to Sentry

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Migration Guide](https://docs.sentry.io/product/accounts/migration/)
- [SDK Documentation](https://docs.sentry.io/platforms/)

## Overview

Execute migrate to Sentry from other error tracking tools.