---
name: running-e2e-tests
description: |
  Execute end-to-end tests covering full user workflows across frontend and backend.
  Use when performing specialized testing.
  Trigger with phrases like "run end-to-end tests", "test user flows", or "execute E2E suite".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:e2e-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# E2E Test Framework

This skill provides automated assistance for e2e test framework tasks.

## Prerequisites

Before using this skill, ensure you have:
- Test environment configured and accessible
- Required testing tools and frameworks installed
- Test data and fixtures prepared
- Appropriate permissions for test execution
- Network connectivity if testing external services

## Instructions

### Step 1: Prepare Test Environment
Set up the testing context:
1. Use Read tool to examine configuration from {baseDir}/config/
2. Validate test prerequisites are met
3. Initialize test framework and load dependencies
4. Configure test parameters and thresholds

### Step 2: Execute Tests
Run the test suite:
1. Use Bash(test:e2e-*) to invoke test framework
2. Monitor test execution progress
3. Capture test outputs and metrics
4. Handle test failures and error conditions

### Step 3: Analyze Results
Process test outcomes:
- Identify passed and failed tests
- Calculate success rate and performance metrics
- Detect patterns in failures
- Generate insights for improvement

### Step 4: Generate Report
Document findings in {baseDir}/test-reports/:
- Test execution summary
- Detailed failure analysis
- Performance benchmarks
- Recommendations for fixes

## Output

The skill generates comprehensive test results:

### Test Summary
- Total tests executed
- Pass/fail counts and percentage
- Execution time metrics
- Resource utilization stats

### Detailed Results
Each test includes:
- Test name and identifier
- Execution status (pass/fail/skip)
- Actual vs. expected outcomes
- Error messages and stack traces

### Metrics and Analysis
- Code coverage percentages
- Performance benchmarks
- Trend analysis across runs
- Quality gate compliance status

## Error Handling

Common issues and solutions:

**Environment Setup Failures**
- Error: Test environment not properly configured
- Solution: Verify configuration files; check environment variables; ensure dependencies are installed

**Test Execution Timeouts**
- Error: Tests exceeded maximum execution time
- Solution: Increase timeout thresholds; optimize slow tests; parallelize test execution

**Resource Exhaustion**
- Error: Insufficient memory or disk space during testing
- Solution: Clean up temporary files; reduce concurrent test workers; increase resource allocation

**Dependency Issues**
- Error: Required services or databases unavailable
- Solution: Verify service health; check network connectivity; use mocks if services are down

## Resources

### Testing Tools
- Industry-standard testing frameworks for your language/platform
- CI/CD integration guides and plugins
- Test automation best practices documentation

### Best Practices
- Maintain test isolation and independence
- Use meaningful test names and descriptions
- Keep tests fast and focused
- Implement proper setup and teardown
- Version control test artifacts
- Run tests in CI/CD pipelines

## Overview


This skill provides automated assistance for e2e test framework tasks.
This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.