---
name: Analyzing Test Coverage
description: |
  This skill analyzes code coverage metrics to identify untested code and generate comprehensive coverage reports. It is triggered when the user requests analysis of code coverage, identification of coverage gaps, or generation of coverage reports. The skill is best used to improve code quality by ensuring adequate test coverage and identifying areas for improvement. Use trigger terms like "analyze coverage", "code coverage report", "untested code", or the shortcut "cov".
---

## Overview

This skill enables Claude to analyze code coverage metrics, pinpoint areas of untested code, and generate detailed reports. It helps you identify gaps in your test suite and ensure comprehensive code coverage.

## How It Works

1. **Coverage Data Collection**: Claude executes the project's test suite with coverage tracking enabled (e.g., using `nyc`, `coverage.py`, or JaCoCo).
2. **Report Generation**: The plugin parses the coverage data and generates a detailed report, including metrics for line, branch, function, and statement coverage.
3. **Uncovered Code Identification**: Claude highlights specific lines or blocks of code that are not covered by any tests.

## When to Use This Skill

This skill activates when you need to:
- Analyze the overall code coverage of your project.
- Identify specific areas of code that lack test coverage.
- Generate a detailed report of code coverage metrics.
- Enforce minimum code coverage thresholds.

## Examples

### Example 1: Analyzing Project Coverage

User request: "Analyze code coverage for the entire project"

The skill will:
1. Execute the project's test suite with coverage tracking.
2. Generate a comprehensive coverage report, showing line, branch, and function coverage.

### Example 2: Identifying Untested Code

User request: "Show me the untested code in the `src/utils.js` file"

The skill will:
1. Analyze the coverage data for `src/utils.js`.
2. Highlight the lines of code in `src/utils.js` that are not covered by any tests.

## Best Practices

- **Configuration**: Ensure your project has a properly configured coverage tool (e.g., `nyc` in package.json).
- **Thresholds**: Define minimum coverage thresholds to enforce code quality standards.
- **Report Review**: Regularly review coverage reports to identify and address coverage gaps.

## Integration

This skill can be integrated with other testing and CI/CD tools to automate coverage analysis and reporting. For example, it can be used in conjunction with a linting plugin to identify both code style issues and coverage gaps.