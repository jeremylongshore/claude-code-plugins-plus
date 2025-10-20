---
name: Generating Test Reports
description: |
  This skill generates comprehensive test reports with coverage metrics, trends, and stakeholder-friendly formats (HTML, PDF, JSON). It aggregates test results from various frameworks, calculates key metrics (coverage, pass rate, duration), and performs trend analysis. Use this skill when the user requests a test report, coverage analysis, failure analysis, or historical comparisons of test runs. Trigger terms include "test report", "coverage report", "testing trends", "failure analysis", and "historical test data".
---

## Overview

This skill empowers Claude to create detailed test reports, providing insights into code coverage, test performance trends, and failure analysis. It supports multiple output formats for easy sharing and analysis.

## How It Works

1. **Aggregating Results**: Collects test results from various test frameworks used in the project.
2. **Calculating Metrics**: Computes coverage metrics, pass rates, test duration, and identifies trends.
3. **Generating Report**: Produces comprehensive reports in HTML, PDF, or JSON format based on the user's preference.

## When to Use This Skill

This skill activates when you need to:
- Generate a test report after a test run.
- Analyze code coverage to identify areas needing more testing.
- Identify trends in test performance over time.

## Examples

### Example 1: Generating an HTML Test Report

User request: "Generate an HTML test report showing code coverage and failure analysis."

The skill will:
1. Aggregate test results from all available frameworks.
2. Calculate code coverage and identify failing tests.
3. Generate an HTML report summarizing the findings.

### Example 2: Comparing Test Results Over Time

User request: "Create a report comparing the test results from the last two CI/CD runs."

The skill will:
1. Retrieve test results from the two most recent CI/CD runs.
2. Compare key metrics like pass rate and duration.
3. Generate a report highlighting any regressions or improvements.

## Best Practices

- **Clarity**: Specify the desired output format (HTML, PDF, JSON) for the report.
- **Scope**: Define the scope of the report (e.g., specific test suite, time period).
- **Context**: Provide context about the project and testing environment to improve accuracy.

## Integration

This skill can integrate with CI/CD pipelines to automatically generate and share test reports after each build. It also works well with other analysis plugins to provide more comprehensive insights.