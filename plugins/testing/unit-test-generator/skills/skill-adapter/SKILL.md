---
name: Generating Unit Tests
description: |
  This skill enables Claude to automatically generate comprehensive unit tests from source code. It is triggered when the user requests unit tests, test cases, or test suites for specific files or code snippets. The skill supports multiple testing frameworks including Jest, pytest, JUnit, and others, intelligently detecting the appropriate framework or using one specified by the user. Use this skill when the user asks to "generate tests", "create unit tests", or uses the shortcut "gut" followed by a file path.
---

## Overview

This skill empowers Claude to rapidly create robust unit tests, saving developers time and ensuring code quality. It analyzes source code, identifies key functionalities, and generates test cases covering various scenarios, including happy paths, edge cases, and error conditions.

## How It Works

1. **Analyze Source Code**: The skill analyzes the provided source code file to understand its functionality, inputs, and outputs.
2. **Determine Testing Framework**: The skill either detects the appropriate testing framework based on the file type and project structure or uses the framework specified by the user.
3. **Generate Test Cases**: The skill generates comprehensive test cases, including tests for valid inputs, invalid inputs, boundary conditions, and error scenarios.
4. **Create Mock Dependencies**: The skill automatically creates mocks and stubs for external dependencies to isolate the code being tested.
5. **Output Test File**: The skill outputs a new test file containing the generated test cases, imports, setup, and assertions.

## When to Use This Skill

This skill activates when you need to:
- Create unit tests for a specific file or code snippet.
- Generate test cases for a function, class, or module.
- Quickly add test coverage to existing code.
- Ensure code quality and prevent regressions.

## Examples

### Example 1: Generating Tests for a JavaScript Utility Function

User request: "generate tests src/utils/validator.js"

The skill will:
1. Analyze the `validator.js` file to understand its functions and dependencies.
2. Detect that the file is JavaScript and default to Jest.
3. Generate a `validator.test.js` file with test cases covering various validation scenarios.

### Example 2: Generating Tests for a Python API Endpoint using pytest

User request: "generate tests --framework pytest src/api/users.py"

The skill will:
1. Analyze the `users.py` file to understand its API endpoints and dependencies.
2. Use pytest as the testing framework, as specified by the user.
3. Generate a `test_users.py` file with test cases covering various API scenarios, including successful requests, error handling, and authentication.

## Best Practices

- **Framework Specification**: Explicitly specify the testing framework when the default is not desired or ambiguous.
- **File Granularity**: Generate tests for individual files or modules to maintain focus and testability.
- **Review and Refine**: Always review and refine the generated tests to ensure they accurately reflect the desired behavior and coverage.

## Integration

This skill can be used in conjunction with other code analysis and refactoring tools to improve code quality and maintainability. It also integrates with CI/CD pipelines to automatically run tests and prevent regressions.