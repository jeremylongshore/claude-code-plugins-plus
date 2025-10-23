---
name: performance-testing
description: |
  This skill enables Claude to design, execute, and analyze performance tests using the performance-test-suite plugin. It is activated when the user requests load testing, stress testing, spike testing, or endurance testing, and when discussing performance metrics such as response time, throughput, and error rates. It identifies performance bottlenecks related to CPU, memory, database, or network issues. The plugin provides comprehensive reporting, including percentiles, graphs, and recommendations.
---

## Overview

This skill automates performance testing workflows, allowing Claude to create and run various tests to assess system performance under different conditions. It facilitates bottleneck identification and provides actionable recommendations for optimization.

## How It Works

1. **Test Design**: Claude analyzes the user's request to determine the appropriate test type (load, stress, spike, or endurance) and configures test parameters such as target users, duration, and ramp-up time.
2. **Test Execution**: The performance-test-suite plugin executes the designed test, collecting performance metrics like response times, throughput, and error rates.
3. **Metrics Analysis**: Claude analyzes the collected metrics to identify performance bottlenecks and potential issues.
4. **Report Generation**: Claude generates a comprehensive report summarizing the test results, highlighting key performance indicators, and providing recommendations for improvement.

## When to Use This Skill

This skill activates when you need to:
- Create a load test for an API.
- Design a stress test to determine the breaking point of a system.
- Simulate a spike test to evaluate system behavior during sudden traffic surges.
- Develop an endurance test to detect memory leaks or stability issues.

## Examples

### Example 1: Load Testing an API

User request: "Create a load test for the /users API, ramping up to 200 concurrent users over 10 minutes."

The skill will:
1. Design a load test configuration with a ramp-up stage to 200 users over 10 minutes.
2. Execute the load test using the performance-test-suite plugin.
3. Generate a report showing response times, throughput, and error rates for the /users API.

### Example 2: Stress Testing a Checkout Process

User request: "Design a stress test to find the breaking point of the checkout process."

The skill will:
1. Design a stress test configuration with gradually increasing load on the checkout process.
2. Execute the stress test, monitoring response times and error rates.
3. Identify the point at which the checkout process fails and generate a report detailing the system's breaking point.

## Best Practices

- **Realistic Scenarios**: Design tests that accurately reflect real-world usage patterns.
- **Comprehensive Metrics**: Monitor a wide range of performance metrics to gain a holistic view of system performance.
- **Iterative Testing**: Run multiple tests with different configurations to fine-tune performance and identify optimal settings.

## Integration

This skill integrates with other monitoring and alerting plugins to provide real-time feedback on system performance during testing. It can also be used in conjunction with deployment plugins to automatically validate performance after code changes.