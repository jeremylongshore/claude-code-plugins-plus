---
name: Generating Test Doubles
description: |
  This skill uses the test-doubles-generator plugin to automatically create mocks, stubs, spies, and fakes for unit testing. It analyzes dependencies in the code and generates appropriate test doubles based on the chosen testing framework, such as Jest, Sinon, or others. Use this skill when you need to generate test doubles, mocks, stubs, spies, or fakes to isolate units of code during testing. Trigger this skill by requesting test double generation or using the `/gen-doubles` or `/gd` command.
---

## Overview

This skill empowers Claude to streamline unit testing by automatically generating test doubles (mocks, stubs, spies, and fakes). It analyzes the code under test, identifies dependencies, and creates the necessary test doubles, significantly reducing the time and effort required to write effective unit tests.

## How It Works

1. **Dependency Analysis**: Claude analyzes the code to identify dependencies that need to be replaced with test doubles.
2. **Test Double Generation**: Based on the dependencies and specified testing framework, Claude generates appropriate test doubles (mocks, stubs, spies, or fakes).
3. **Code Insertion**: Claude provides the generated test double code, ready for integration into your unit tests.

## When to Use This Skill

This skill activates when you need to:
- Create mocks for external API calls in a unit test.
- Generate stubs for service dependencies to control their behavior.
- Implement spies to track interactions with real objects during testing.

## Examples

### Example 1: Generating Mocks for API Calls

User request: "Generate mocks for the `fetchData` function in `dataService.js` using Jest."

The skill will:
1. Analyze the `dataService.js` file to identify the `fetchData` function and its dependencies.
2. Generate a Jest mock for `fetchData`, allowing you to simulate API responses.

### Example 2: Creating Stubs for Service Dependencies

User request: "Create stubs for the `NotificationService` in `userService.js` using Sinon."

The skill will:
1. Analyze `userService.js` and identify the `NotificationService` dependency.
2. Generate a Sinon stub for `NotificationService`, enabling you to control its behavior during testing of `userService.js`.

## Best Practices

- **Framework Selection**: Specify the testing framework you are using (e.g., Jest, Sinon) for optimal test double generation.
- **Code Context**: Provide the relevant code snippets or file paths to ensure accurate dependency analysis.
- **Test Double Type**: Consider the purpose of the test double. Use mocks for behavior verification, stubs for controlled responses, and spies for interaction tracking.

## Integration

This skill integrates directly with your codebase by providing generated test double code snippets that can be easily copied and pasted into your unit tests. It supports popular testing frameworks and enhances the overall testing workflow.