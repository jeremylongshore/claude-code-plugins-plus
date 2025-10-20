---
name: Orchestrating Test Workflows
description: |
  This skill enables Claude to orchestrate complex test workflows using the test-orchestrator plugin. It allows Claude to define test execution graphs with dependencies, execute tests in parallel, and intelligently select tests to run based on code changes. Use this skill when a user requests test orchestration, dependency management for tests, parallel test execution, smart test selection, or CI/CD integration for testing. Trigger terms include "orchestrate tests", "test workflow", "parallel testing", "smart test selection", "test dependencies", and "/orchestrate".
---

## Overview

This skill empowers Claude to manage and execute complex test suites efficiently. It leverages the test-orchestrator plugin to handle test dependencies, parallel execution, and intelligent test selection, resulting in faster and more reliable testing processes.

## How It Works

1. **Workflow Definition**: Claude uses the plugin to define the test workflow, specifying dependencies between tests.
2. **Parallelization**: The plugin identifies independent tests and executes them in parallel to reduce overall execution time.
3. **Smart Selection**: Based on code changes, the plugin selects only the affected tests to run, minimizing unnecessary execution.

## When to Use This Skill

This skill activates when you need to:
- Optimize test execution time.
- Manage dependencies between tests.
- Run only relevant tests after code changes.

## Examples

### Example 1: Optimizing Regression Testing

User request: "Orchestrate the regression tests for the user authentication module after the recent code changes."

The skill will:
1. Use the test-orchestrator plugin to identify the tests affected by the changes in the user authentication module.
2. Execute those tests in parallel, respecting any dependencies.

### Example 2: Setting up a CI/CD Pipeline

User request: "Set up a test workflow for the CI/CD pipeline that runs unit tests, integration tests, and end-to-end tests with appropriate dependencies."

The skill will:
1. Define a test workflow using the test-orchestrator plugin, specifying the order and dependencies between the different test suites (unit, integration, end-to-end).
2. Configure the pipeline to trigger the orchestrated test execution upon code commits.

## Best Practices

- **Dependency Mapping**: Clearly define dependencies between tests to ensure correct execution order.
- **Granularity**: Break down large test suites into smaller, more manageable units for better parallelization.
- **Change Tracking**: Integrate the test-orchestrator with version control to accurately identify affected tests.

## Integration

This skill integrates with the test-orchestrator plugin and can be incorporated into CI/CD pipelines. It can also be used in conjunction with other code analysis tools to further refine test selection.