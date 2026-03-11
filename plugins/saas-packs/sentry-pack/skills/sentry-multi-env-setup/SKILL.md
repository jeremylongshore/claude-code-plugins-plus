---
name: sentry-multi-env-setup
description: |
  Configure Sentry across multiple environments.
  Use when setting up Sentry for dev/staging/production,
  managing environment-specific configurations, or isolating data.
  Trigger with phrases like "sentry environments", "sentry staging setup",
  "multi-environment sentry", "sentry dev vs prod".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Multi Env Setup

## Prerequisites

- Environment naming convention defined
- DSN management strategy
- Sample rate requirements per environment
- Alert routing per environment

## Instructions

1. Set environment option in SDK init to match deployment target
2. Configure environment-specific sample rates (100% dev, 10% prod)
3. Choose project structure (single with environments vs separate projects)
4. Set up separate DSNs per environment in environment variables
5. Implement conditional DSN loading to disable in development
6. Add environment context and tags in beforeSend hook
7. Configure environment filters in Sentry dashboard
8. Create production-only alert rules with appropriate conditions
9. Set up lower-priority staging alerts for development feedback
10. Document environment configuration and best practices for team

## Output
- Environment-specific Sentry configuration
- Separate or shared projects configured
- Environment-based alert rules
- Sample rates optimized per environment

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Environments](https://docs.sentry.io/product/sentry-basics/environments/)
- [Filtering Events](https://docs.sentry.io/platforms/javascript/configuration/filtering/)

## Overview

Configure Sentry across multiple environments.