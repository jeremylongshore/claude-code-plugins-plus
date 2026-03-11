---
name: clerk-ci-integration
description: |
  Configure Clerk CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Clerk tests into your build process.
  Trigger with phrases like "clerk CI", "clerk GitHub Actions",
  "clerk automated tests", "CI clerk", "clerk pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk CI Integration

## Overview
Set up CI/CD pipelines with Clerk authentication testing.

## Prerequisites
- GitHub repository with Actions enabled
- Clerk test API keys
- npm/pnpm project configured

## Instructions
1. Step 1: GitHub Actions Workflow
2. Step 2: E2E Testing with Playwright
3. Step 3: Test User Setup
4. Step 4: Playwright Test Configuration
5. Step 5: Authentication Test Helpers
6. Step 6: Sample E2E Tests

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- GitHub Actions workflows configured
- E2E tests with Playwright
- Test user management
- CI/CD pipeline ready

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | Add secret in repo settings |
| Test user not found | User not created | Run setup script first |
| Timeout on sign-in | Slow response | Increase timeout, check network |
| Build fails | Missing env vars | Check all NEXT_PUBLIC vars set |

## Resources
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Playwright Testing](https://playwright.dev)
- [Clerk Testing Guide](https://clerk.com/docs/testing/overview)

## Next Steps
Proceed to `clerk-deploy-integration` for deployment platform setup.

## Examples

**Basic usage**: Apply clerk ci integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk ci integration for production environments with multiple constraints and team-specific requirements.