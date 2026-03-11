---
name: sentry-ci-integration
description: |
  Manage integrate Sentry with CI/CD pipelines.
  Use when setting up GitHub Actions, GitLab CI, or other CI systems
  with Sentry releases and source maps.
  Trigger with phrases like "sentry github actions", "sentry CI",
  "sentry pipeline", "automate sentry releases".
allowed-tools: Read, Write, Edit, Bash(gh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Ci Integration

## Prerequisites

- Sentry CLI installed or available in CI
- `SENTRY_AUTH_TOKEN` secret configured
- `SENTRY_ORG` and `SENTRY_PROJECT` environment variables set
- Source maps generated during build

## Instructions

1. Add SENTRY_AUTH_TOKEN secret to CI platform (GitHub, GitLab, CircleCI)
2. Configure SENTRY_ORG and SENTRY_PROJECT environment variables
3. Create workflow step to build application with SENTRY_RELEASE env
4. Add step to create Sentry release using sentry-cli or action
5. Upload source maps from build output directory
6. Associate commits with release using set-commits --auto
7. Finalize the release to mark it complete
8. Add deploy notification step for environment tracking
9. Configure checkout with fetch-depth: 0 for full git history
10. Test workflow by pushing to trigger release creation

## Output
- Release created and finalized in Sentry
- Source maps uploaded for stack trace mapping
- Commits associated with release
- Deploy notification sent to Sentry

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry CI/CD](https://docs.sentry.io/product/releases/setup/release-automation/)
- [GitHub Action](https://github.com/getsentry/action-release)
