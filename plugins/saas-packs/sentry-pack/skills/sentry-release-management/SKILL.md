---
name: sentry-release-management
description: |
  Manage Sentry releases and associate commits.
  Use when creating releases, tracking commits,
  or managing release artifacts.
  Trigger with phrases like "sentry release", "sentry commits",
  "manage sentry versions", "sentry release workflow".
allowed-tools: Read, Write, Edit, Bash(sentry-cli:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Release Management

## Prerequisites

- Sentry CLI installed (`npm install -g @sentry/cli`)
- `SENTRY_AUTH_TOKEN` environment variable set
- `SENTRY_ORG` and `SENTRY_PROJECT` configured
- Source maps available in build output

## Instructions

1. Create release using git SHA, semantic version, or package.json version
2. Associate commits with sentry-cli releases set-commits --auto
3. Upload source maps from build directory with URL prefix if needed
4. Finalize release to mark it complete
5. Configure SDK release option to match CLI release version
6. Set up Webpack DefinePlugin or environment variable for build-time injection
7. Use release management API to list, view, or delete releases
8. Connect GitHub/GitLab integration for automatic commit linking
9. Create release script to automate the full workflow
10. Implement source map cleanup for old releases to manage storage

## Output
- Release created with version identifier
- Commits associated with release
- Source maps uploaded
- Release finalized and ready

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Releases](https://docs.sentry.io/product/releases/)
- [Sentry CLI Releases](https://docs.sentry.io/product/cli/releases/)

## Overview

Manage Sentry releases and associate commits.