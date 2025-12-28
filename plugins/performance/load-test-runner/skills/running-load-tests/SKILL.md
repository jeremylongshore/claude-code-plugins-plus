---
name: running-load-tests
description: Create and execute load tests for performance validation using k6, JMeter, and Artillery. Use when validating application performance under load conditions or identifying bottlenecks. Trigger with phrases like "run load test", "create stress test", or "validate performance under load".
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(k6:*), Bash(jmeter:*), Bash(artillery:*), Bash(performance:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Load Test Runner

This skill provides automated assistance for load test runner tasks.

## Overview

This skill empowers Claude to automate the creation and execution of load tests, ensuring applications can handle expected traffic and identify potential performance bottlenecks. It streamlines the process of defining test scenarios, generating scripts, and executing tests for comprehensive performance validation.

## How It Works

1. **Analyze Application**: Claude analyzes the user's request to understand the application's endpoints and critical paths.
2. **Identify Test Scenarios**: Claude identifies relevant test scenarios, such as baseline load, stress test, spike test, soak test, or scalability test, based on the user's requirements.
3. **Generate Load Test Scripts**: Claude generates load test scripts (k6, JMeter, Artillery, etc.) based on the selected scenarios and application details.
4. **Define Performance Thresholds**: Claude defines performance thresholds and provides execution instructions for the generated scripts.

## When to Use This Skill

This skill activates when you need to:
- Create load tests for a web application or API.
- Validate the performance of an application under different load conditions.
- Identify performance bottlenecks and breaking points.

## Examples

### Example 1: Creating a Stress Test

User request: "Create a stress test for the /api/users endpoint to simulate 1000 concurrent users."

The skill will:
1. Analyze the request and identify the need for a stress test on the /api/users endpoint.
2. Generate a k6 script that simulates 1000 concurrent users hitting the /api/users endpoint.

### Example 2: Validating Performance After a Code Change

User request: "Validate the performance of the application after the recent code changes with a baseline load test."

The skill will:
1. Identify the need for a baseline load test to validate performance.
2. Generate a JMeter script that simulates normal traffic patterns for the application.

## Best Practices

- **Realistic Scenarios**: Define load test scenarios that accurately reflect real-world usage patterns.
- **Threshold Definition**: Establish clear performance thresholds to identify potential issues.
- **Iterative Testing**: Run load tests iteratively to identify and address performance bottlenecks early in the development cycle.

## Integration

This skill can be integrated with CI/CD pipelines to automate performance testing as part of the deployment process. It can also be used in conjunction with monitoring tools to correlate performance metrics with application behavior.

## Prerequisites

- Load testing tools installed (k6, JMeter, or Artillery)
- Access to target application endpoints
- Test scenario definitions and expected load patterns
- Results storage location at {baseDir}/load-tests/

## Instructions

1. Analyze application architecture and identify critical endpoints
2. Define test scenarios (baseline, stress, spike, soak, scalability)
3. Generate appropriate load test scripts using selected tool
4. Configure performance thresholds and acceptance criteria
5. Execute load tests and capture metrics
6. Analyze results and identify performance bottlenecks

## Output

- Load test scripts (k6, JMeter, or Artillery format)
- Test execution logs and metrics
- Performance reports with response times and throughput
- Threshold violation alerts
- Recommendations for performance improvements

## Error Handling

If load test execution fails:
- Verify tool installation and configuration
- Check network connectivity to target endpoints
- Validate authentication and authorization
- Review test script syntax and parameters
- Ensure sufficient system resources for test execution

## Resources

- k6 documentation and examples
- JMeter user manual and best practices
- Artillery load testing guides
- Performance testing methodology references