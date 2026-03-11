---
name: openevidence-ci-integration
description: |
  Integrate OpenEvidence testing into CI/CD pipelines.
  Use when setting up automated testing, configuring GitHub Actions,
  or implementing continuous integration for clinical AI applications.
  Trigger with phrases like "openevidence ci", "openevidence github actions",
  "openevidence pipeline", "test openevidence ci", "automate openevidence tests".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence CI Integration

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Integrate OpenEvidence testing and validation into CI/CD pipelines. Covers GitHub Actions workflows, unit tests with SDK mocks, integration tests against sandbox, and clinical validation test suites.

## Prerequisites
- GitHub, GitLab, or other CI platform
- OpenEvidence sandbox API credentials
- Test suite configured (vitest recommended)
- Secret management in CI platform

## Instructions

### Step 1: Create GitHub Actions Workflow
Set up parallel jobs: lint-and-typecheck, unit-tests (with coverage), integration-tests (sandbox only, gated by branch/label), and clinical-validation (on main).

### Step 2: Configure Test Environments
Create separate vitest configs: base (unit, 10s timeout), integration (60s timeout, retry 2, maxConcurrency 1 to avoid rate limits).

### Step 3: Write Unit Tests with Mocks
Mock `@openevidence/sdk` to test clinical query service logic, error handling, and response formatting without API calls.

### Step 4: Write Integration Tests
Test against sandbox: verify clinical queries return answers with citations, validate empty queries fail gracefully, check citation fields.

### Step 5: Add Clinical Validation
Create known-answer test cases that verify responses contain expected medical keywords (e.g., "metformin" for diabetes, "statin" for cardiovascular) with confidence > 0.7.

### Step 6: Configure Secrets
Store `OPENEVIDENCE_SANDBOX_API_KEY` and `OPENEVIDENCE_SANDBOX_ORG_ID` as GitHub secrets. Use `.env.test` for local development.

## Output
- CI workflow with lint, unit tests, integration tests, clinical validation
- Vitest configurations (unit + integration)
- Unit tests with mocked SDK
- Integration tests against sandbox
- Clinical validation with known-answer testing
- Coverage reports

## Error Handling
| CI Issue | Cause | Solution |
|----------|-------|----------|
| Integration test timeout | API slow or rate limited | Increase timeout, add retry |
| Secret not found | Missing GitHub secret | Add secret in repo settings |
| Flaky tests | Network variability | Add retries, improve assertions |
| Coverage drop | New code untested | Add tests, adjust thresholds |

## Examples

### Package.json Scripts
```json
{
  "test:unit": "vitest run -c vitest.config.ts",
  "test:integration": "vitest run -c vitest.config.integration.ts",
  "test:clinical-validation": "vitest run tests/clinical-validation"
}
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)