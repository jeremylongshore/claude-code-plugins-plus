---
name: juicebox-ci-integration
description: |
  Configure Juicebox CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Juicebox tests into your build process.
  Trigger with phrases like "juicebox CI", "juicebox GitHub Actions",
  "juicebox automated tests", "CI juicebox".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox CI Integration

## Overview
Configure CI/CD pipelines for Juicebox integration testing and deployment.

## Prerequisites
- GitHub repository with Actions enabled
- Juicebox test API key
- npm/pnpm project configured

## Instructions
- Step 1: Configure GitHub Secrets
- Step 2: Create Test Workflow
- Step 3: Add Integration Tests
- Step 4: Configure Branch Protection
- Step 5: Add Deployment Pipeline

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- GitHub Actions workflow files
- Integration test suite
- Branch protection rules
- Deployment pipeline

## Error Handling
| CI Issue | Cause | Solution |
|----------|-------|----------|
| Secret not found | Not configured | Run `gh secret set` |
| Rate limited | Too many test runs | Use sandbox mode |
| Flaky tests | Network issues | Add retry logic |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Juicebox CI Guide](https://juicebox.ai/docs/ci)

## Next Steps
After CI setup, see `juicebox-deploy-integration` for deployment configuration.
