---
name: running-integration-tests
description: |
  This skill enables Claude to run and manage integration test suites. It automates environment setup, database seeding, service orchestration, and cleanup. Use this skill when the user asks to "run integration tests", "execute integration tests", or any command that implies running integration tests for a project, including specifying particular test suites or options like code coverage. It is triggered by phrases such as "/run-integration", "/rit", or requests mentioning "integration tests". The plugin handles database creation, migrations, seeding, and dependent service management.
---

## Overview

This skill empowers Claude to execute comprehensive integration tests, ensuring seamless interactions between various system components. It automates the often complex setup and teardown processes, providing reliable and repeatable test runs.

## How It Works

1. **Environment Preparation**: The plugin sets up the test environment, including creating/resetting databases, running migrations, and seeding test data.
2. **Test Execution**: The plugin executes the integration test suites, capturing detailed logs and reporting progress.
3. **Cleanup**: After the tests, the plugin cleans up the environment, dropping the test database, stopping services, and removing temporary files to prevent test pollution.

## When to Use This Skill

This skill activates when you need to:
- Run all integration tests for a project.
- Run a specific integration test suite (e.g., "API tests").
- Run integration tests with code coverage analysis.

## Examples

### Example 1: Running All Integration Tests

User request: "/run-integration"

The skill will:
1. Prepare the test environment (database, services).
2. Execute all integration test suites defined in the project.
3. Generate a report with pass/fail counts and coverage metrics.
4. Clean up the test environment.

### Example 2: Running a Specific Test Suite

User request: "/run-integration api"

The skill will:
1. Prepare the test environment.
2. Execute only the "api" integration test suite.
3. Generate a report specific to the "api" suite.
4. Clean up the test environment.

## Best Practices

- **Configuration**: Ensure test configurations are properly set up in `test/integration/config.json`, `.env.test`, or related files.
- **Dependencies**: Define all necessary services and dependencies in the test environment configuration.
- **Test Design**: Write focused integration tests that verify specific interactions between components.

## Integration

This skill works seamlessly with other plugins by ensuring a clean and isolated test environment. It avoids conflicts with other processes and provides reliable results.