---
name: deepgram-ci-integration
description: |
  Configure Deepgram CI/CD integration for automated testing and deployment.
  Use when setting up continuous integration pipelines, automated testing,
  or deployment workflows for Deepgram integrations.
  Trigger with phrases like "deepgram CI", "deepgram CD", "deepgram pipeline",
  "deepgram github actions", "deepgram automated testing".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram CI Integration

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Set up continuous integration and deployment pipelines for Deepgram integrations. Covers GitHub Actions, GitLab CI, integration test suites, smoke tests, and automated key rotation.

## Prerequisites
- CI/CD platform access (GitHub Actions, GitLab CI, etc.)
- Deepgram API key for testing
- Secret management configured
- Test fixtures prepared

## Instructions

### Step 1: Configure Secrets
Store `DEEPGRAM_API_KEY` and `DEEPGRAM_PROJECT_ID` as CI/CD secrets. Use separate keys per environment.

### Step 2: Create Test Workflow
Set up automated testing on push/PR with unit tests, linting, and type checking.

### Step 3: Add Integration Tests
Implement Deepgram-specific integration tests: API connectivity, pre-recorded transcription, language detection, and error handling.

### Step 4: Configure Deployment
Set up staged deployment: test -> lint -> integration -> staging deploy -> smoke test.

### Step 5: Set Up Key Rotation
Configure monthly automated key rotation via `gh secret set` in a scheduled workflow.

## Output
- CI workflow configuration (GitHub Actions or GitLab CI)
- Automated test suite with integration tests
- Smoke test script for post-deploy verification
- Deployment pipeline with staging/production stages
- Automated key rotation schedule

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Integration tests fail | Invalid or expired API key | Rotate `DEEPGRAM_API_KEY` secret |
| Smoke test timeout | API latency or network issues | Increase timeout, check status page |
| Build fails | Missing dependencies | Verify `npm ci` succeeds |

## Examples

### Smoke Test
```bash
DEEPGRAM_API_KEY=xxx npx tsx scripts/smoke-test.ts
```

Tests API connectivity and transcription of the NASA podcast sample, exits non-zero on failure.

### Package.json Scripts
```json
{
  "test:integration": "vitest run --config vitest.integration.config.ts",
  "test:deepgram": "vitest run tests/integration/deepgram.test.ts",
  "smoke-test": "tsx scripts/smoke-test.ts"
}
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [Deepgram SDK Testing](https://developers.deepgram.com/docs/testing)