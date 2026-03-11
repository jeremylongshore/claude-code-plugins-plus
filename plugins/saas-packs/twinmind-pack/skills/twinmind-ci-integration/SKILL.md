---
name: twinmind-ci-integration
description: |
  Integrate TwinMind into CI/CD pipelines for automated testing and deployment.
  Use when setting up GitHub Actions, GitLab CI, or other CI systems
  with TwinMind API testing and validation.
  Trigger with phrases like "twinmind ci", "twinmind github actions",
  "twinmind pipeline", "automate twinmind testing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind CI Integration

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Integrate TwinMind testing and validation into CI/CD pipelines with GitHub Actions workflows, unit tests, integration tests, smoke tests, and GitLab CI configuration.

## Prerequisites
- TwinMind Pro/Enterprise API access
- CI/CD system (GitHub Actions, GitLab CI, etc.)
- Test audio samples
- Secrets management for API keys

## Instructions

### Step 1: GitHub Actions Workflow
Create a multi-job workflow with lint-and-typecheck, unit-tests, integration-tests (with API key from secrets), api-health-check, and transcription-smoke-test (on main/schedule only).

### Step 2: Write Unit Tests
Build Vitest unit tests mocking the TwinMind client. Test correct request formatting, rate limit handling (429 responses), and summary generation response parsing.

### Step 3: Write Integration Tests
Create integration tests that use real API keys (from environment variables). Test API health, account access, and actual transcription with configurable test audio URL.

### Step 4: Build Smoke Test Script
Create a standalone smoke test runner that checks API health, account access, and optionally transcription. Report pass/fail with duration for each test.

### Step 5: GitLab CI Configuration
Set up equivalent GitLab CI with lint, test, integration stages. Use YAML anchors for shared node template. Configure coverage reporting and scheduled runs.

### Step 6: Configure Vitest
Set up vitest.config.ts with V8 coverage provider, 30s test timeout, and separate test scripts for unit, integration, and smoke tests.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete GitHub Actions YAML, test files, smoke test runner, and GitLab CI config.

## Output
- GitHub Actions workflow
- Unit test suite
- Integration test suite
- Smoke test script
- GitLab CI configuration

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Not configured | Add to GitHub/GitLab Secrets |
| Test timeout | Large audio file | Use 10-30 second test samples |
| Rate limited in CI | Too many runs | Use dedicated test API key |
| API unavailable | TwinMind outage | Add retry logic to tests |

## Examples


**Basic usage**: Apply twinmind ci integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind ci integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
For deployment integration, see `twinmind-deploy-integration`.