---
name: customerio-ci-integration
description: |
  Configure Customer.io CI/CD integration.
  Use when setting up automated testing, deployment pipelines,
  or continuous integration for Customer.io integrations.
  Trigger with phrases like "customer.io ci", "customer.io github actions",
  "customer.io pipeline", "customer.io automated testing".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io CI Integration

## Overview
Set up CI/CD pipelines for Customer.io integrations with automated testing, smoke tests, and deployment workflows for GitHub Actions and GitLab CI.

## Prerequisites
- CI/CD platform (GitHub Actions, GitLab CI, etc.)
- Separate Customer.io workspace for testing
- Secrets management configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Set up unit tests, integration tests, and smoke tests with separate test workspaces. Include coverage reporting and test user cleanup.

### Step 2: Build Test Fixtures
Create reusable test helpers for client creation, test user ID generation, and cleanup functions.

### Step 3: Write Integration Test Suite
Test identify, track, and error handling with vitest. Use unique test user IDs and clean up in afterAll hooks.

### Step 4: Configure GitLab CI (if applicable)
Set up equivalent stages for unit tests, integration tests, and deployment with environment-specific variables.

### Step 5: Set Up Pre-commit Hooks
Add linting and type-checking hooks that run on Customer.io integration files before commit.

### Step 6: Manage CI Environments
Create environment validation scripts that verify credentials are available before tests run.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- GitHub Actions workflow for testing
- GitLab CI configuration
- Integration test suite with vitest
- Pre-commit hooks
- Environment management scripts

## Error Handling
| Issue | Solution |
|-------|----------|
| Secrets not available | Check CI environment secrets config |
| Test user pollution | Use unique IDs and cleanup in afterAll |
| Rate limiting in CI | Add delays between test batches |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitLab CI Variables](https://docs.gitlab.com/ee/ci/variables/)

## Next Steps
After CI setup, proceed to `customerio-deploy-pipeline` for production deployment.
