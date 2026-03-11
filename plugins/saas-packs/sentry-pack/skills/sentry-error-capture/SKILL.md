---
name: sentry-error-capture
description: |
  Execute advanced error capture and context enrichment with Sentry.
  Use when implementing detailed error tracking, adding context,
  or customizing error capture behavior.
  Trigger with phrases like "sentry error capture", "sentry context",
  "enrich sentry errors", "sentry exception handling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Error Capture

## Prerequisites
- Sentry SDK installed and configured
- Understanding of error handling
- Application logging infrastructure


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Errors with full context in Sentry dashboard
- Filterable tags for issue management
- User attribution for error tracking

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Enriching Events](https://docs.sentry.io/platforms/javascript/enriching-events/)
- [Sentry Scopes](https://docs.sentry.io/platforms/javascript/enriching-events/scopes/)

## Overview

Execute advanced error capture and context enrichment with Sentry.

## Instructions

1. Assess the current state of the Sentry Error Capture configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference