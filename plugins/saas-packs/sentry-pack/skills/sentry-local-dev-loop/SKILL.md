---
name: sentry-local-dev-loop
description: |
  Execute set up local development workflow with Sentry.
  Use when configuring Sentry for development environments,
  setting up debug mode, or testing error capture locally.
  Trigger with phrases like "sentry local dev", "sentry development",
  "debug sentry", "sentry dev environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Local Dev Loop

## Prerequisites
- Sentry SDK installed
- Development environment set up
- Separate Sentry project for development (recommended)


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Environment-aware Sentry configuration
- Debug logging enabled for development
- Separate project/DSN for development events

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Environment Config](https://docs.sentry.io/platforms/javascript/configuration/environments/)
- [Sentry Debug Mode](https://docs.sentry.io/platforms/javascript/configuration/options/#debug)

## Overview

Execute set up local development workflow with Sentry.

## Instructions

1. Assess the current state of the testing configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference