---
name: running-mutation-tests
description: |
  This skill enables Claude to validate test suite quality by performing mutation testing. It is triggered when the user asks to run mutation tests, analyze test effectiveness, or improve test coverage. The skill introduces code mutations, runs tests against the mutated code, and reports on the "survival rate" of the mutations, indicating the effectiveness of the test suite. Use this skill when the user requests to assess the quality of their tests using mutation testing techniques. Specific trigger terms include "mutation testing", "test effectiveness", "mutation score", and "surviving mutants".
---

## Overview

This skill empowers Claude to execute mutation testing, providing insights into the effectiveness of a test suite. By introducing small changes (mutations) into the code and running the tests, it determines if the tests are capable of detecting these changes. This helps identify weaknesses in the test suite and improve overall code quality.

## How It Works

1. **Mutation Generation**: The plugin automatically introduces mutations (e.g., changing `+` to `-`) into the code.
2. **Test Execution**: The test suite is run against the mutated code.
3. **Result Analysis**: The plugin analyzes which mutations were "killed" (detected by tests) and which "survived" (were not detected).
4. **Reporting**:  A mutation score is calculated, and surviving mutants are identified for further investigation.

## When to Use This Skill

This skill activates when you need to:
- Validate the effectiveness of a test suite.
- Identify gaps in test coverage.
- Improve the mutation score of a project.
- Analyze surviving mutants to strengthen tests.

## Examples

### Example 1: Improving Test Coverage

User request: "Run mutation testing on the validator module and suggest improvements to the tests."

The skill will:
1. Execute mutation tests on the validator module.
2. Analyze the results and identify surviving mutants, indicating areas where tests are weak.
3. Suggest specific improvements to the tests based on the surviving mutants, such as adding new test cases or modifying existing ones.

### Example 2: Assessing Test Quality

User request: "What is the mutation score for the user authentication service?"

The skill will:
1. Execute mutation tests on the user authentication service.
2. Calculate the mutation score based on the number of killed mutants.
3. Report the mutation score to the user, providing a metric for test quality.

## Best Practices

- **Targeted Mutation**: Focus mutation testing on critical modules or areas with high complexity.
- **Analyze Survivors**: Prioritize the analysis of surviving mutants to identify the most impactful improvements to test coverage.
- **Iterative Improvement**: Use mutation testing as part of an iterative process to continuously improve test suite quality.

## Integration

This skill integrates well with other testing and code analysis tools. For example, it can be used in conjunction with code coverage tools to provide a more comprehensive view of test effectiveness.