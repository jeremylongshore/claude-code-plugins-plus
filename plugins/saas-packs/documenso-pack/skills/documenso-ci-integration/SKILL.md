---
name: documenso-ci-integration
description: |
  Configure CI/CD pipelines for Documenso integrations.
  Use when setting up automated testing, deployment pipelines,
  or continuous integration for Documenso projects.
  Trigger with phrases like "documenso CI", "documenso GitHub Actions",
  "documenso pipeline", "documenso automated testing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso CI Integration

## Overview
Configure CI/CD pipelines for testing and deploying Documenso integrations with GitHub Actions, GitLab CI, and other platforms.

## Prerequisites
- Source control (GitHub, GitLab, etc.)
- CI/CD platform access
- Staging Documenso API key
- Test environment configured

## Instructions

### Step 1: GitHub Actions Configuration
name: Documenso Integration CI
### Step 2: Test Scripts
// tests/integration/setup.ts
### Step 3: GitLab CI Configuration
stages:
### Step 4: Pre-commit Hooks
// package.json

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- GitHub Actions Configuration
- Test Scripts
- GitLab CI Configuration
- Pre-commit Hooks

## Error Handling
| CI Issue | Cause | Solution |
|----------|-------|----------|
| Integration test timeout | Slow API | Increase timeout |
| Rate limit in CI | Too many requests | Add delays between tests |
| Cleanup failed | API error | Manual cleanup or retry |
| Secret not found | Missing config | Add to CI secrets |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [Jest CI Configuration](https://jestjs.io/docs/cli#--ci)

## Next Steps
For deployment strategies, see `documenso-deploy-integration`.

## Examples

**Basic usage**: Apply documenso ci integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso ci integration for production environments with multiple constraints and team-specific requirements.