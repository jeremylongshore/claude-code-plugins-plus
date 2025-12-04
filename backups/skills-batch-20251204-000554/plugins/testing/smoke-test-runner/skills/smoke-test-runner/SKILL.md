---
name: running-smoke-tests
description: |
  This skill runs smoke tests to verify critical application functionality. It executes pre-defined test suites that check system health, authentication, core features, and external integrations. Use this skill after deployments, upgrades, or significant configuration changes to ensure the application is operational. Trigger this skill using the terms "smoke test" or "st".
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill enables Claude to quickly verify the critical functionality of an application by running a suite of smoke tests. It provides a fast pass/fail assessment, helping to identify potential issues early in the deployment process.

## How It Works

1. **Initiate Smoke Test**: The user requests a smoke test using the `/smoke-test` or `/st` command.
2. **Execute Test Suite**: The skill executes the pre-defined suite of smoke tests, covering system health, authentication, core features, and external integrations.
3. **Report Results**: The skill provides a summary of the test results, indicating whether the tests passed or failed.

## When to Use This Skill

This skill activates when you need to:
- Verify application functionality after a deployment.
- Confirm system health after an upgrade.
- Sanity-check critical features after configuration changes.

## Examples

### Example 1: Post-Deployment Verification

User request: "Run a smoke test after deploying the new version."

The skill will:
1. Execute the smoke test suite.
2. Report the pass/fail status of each test, highlighting any failures in authentication or core feature validation.

### Example 2: Configuration Change Validation

User request: "/st to validate the recent database configuration changes."

The skill will:
1. Execute the smoke test suite.
2. Report the results, specifically checking the system health and integration tests to ensure the database changes didn't introduce issues.

## Best Practices

- **Focus**: Ensure smoke tests focus on the most critical user flows and system components.
- **Speed**: Keep the smoke test suite execution time under 5 minutes for rapid feedback.
- **Integration**: Integrate smoke tests into your CI/CD pipeline for automated post-deployment verification.

## Integration

This skill can be used in conjunction with other deployment and monitoring tools to provide a comprehensive view of application health and stability. It works independently, requiring only the `/smoke-test` or `/st` command to initiate.