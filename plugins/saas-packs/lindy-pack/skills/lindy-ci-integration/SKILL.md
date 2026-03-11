---
name: lindy-ci-integration
description: |
  Configure Lindy AI CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Lindy tests into your build process.
  Trigger with phrases like "lindy CI", "lindy GitHub Actions",
  "lindy automated tests", "CI lindy pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy CI Integration

## Overview
Configure CI/CD pipelines for Lindy AI agent testing and deployment.

## Prerequisites
- GitHub repository with Actions enabled
- Lindy test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
### Step 2: Configure Test API Key
### Step 3: Create Integration Tests
### Step 4: Add PR Checks

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Automated test pipeline
- PR checks configured
- Coverage reports uploaded
- Integration test suite

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Not configured | Add via `gh secret set` |
| Tests timeout | Agent slow | Increase jest timeout |
| Rate limited | Too many tests | Add delays or use test key |

## Examples


**Basic usage**: Apply lindy ci integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy ci integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Lindy CI Guide](https://docs.lindy.ai/ci)
- [Jest Configuration](https://jestjs.io/docs/configuration)

## Next Steps
Proceed to `lindy-deploy-integration` for deployment automation.