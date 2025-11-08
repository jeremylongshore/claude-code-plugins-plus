---
name: tracking-regression-tests
description: |
  This skill enables Claude to track and run regression tests, ensuring new changes don't break existing functionality. It is triggered when the user asks to "track regression", "run regression tests", or uses the shortcut "reg". The skill helps in maintaining code stability by identifying critical tests, automating their execution, and analyzing the impact of changes. It also provides insights into test history and identifies flaky tests. The skill uses the `regression-test-tracker` plugin.
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill allows Claude to track and execute regression tests, which are crucial for maintaining software quality and preventing unintended consequences from new code changes. By automating the regression testing process, Claude can quickly identify and address potential issues before they impact users.

## How It Works

1. **Identify Regression Tests**: The user marks specific tests as part of the regression suite using the `--mark` flag.
2. **Execute Regression Suite**: The skill runs the designated regression tests.
3. **Analyze Results**: The skill analyzes the test results, highlighting failures and potential flaky tests.

## When to Use This Skill

This skill activates when you need to:
- Run the regression test suite before deploying new code.
- Mark a specific test as part of the regression suite.
- Investigate potential regressions after making code changes.

## Examples

### Example 1: Running the Regression Suite

User request: "run regression tests"

The skill will:
1. Execute all tests marked as part of the regression suite.
2. Report the results, including any failures or flaky tests.

### Example 2: Marking a Test for Regression

User request: "track regression --mark test_example"

The skill will:
1. Mark the test `test_example` as part of the regression suite.
2. Confirm that the test has been added to the suite.

## Best Practices

- **Test Selection**: Choose tests that cover critical functionality and are likely to be affected by changes.
- **Frequency**: Run the regression suite frequently, especially before deployments.
- **Analysis**: Carefully analyze test failures to identify the root cause of regressions.

## Integration

This skill can be integrated with other testing and CI/CD tools to automate the regression testing process as part of a larger development workflow.