---
name: Testing Load Balancers
description: |
  This skill enables Claude to test load balancing strategies. It validates traffic distribution across backend servers, tests failover scenarios when servers become unavailable, verifies sticky sessions, and assesses health check functionality. Use this skill when the user asks to "test load balancer", "validate traffic distribution", "test failover", "verify sticky sessions", or "test health checks". It is specifically designed for testing load balancing configurations using the `load-balancer-tester` plugin.
---

## Overview

This skill empowers Claude to thoroughly test load balancing configurations, ensuring high availability and optimal performance. It automates the process of validating traffic distribution, simulating server failures, and verifying session persistence.

## How It Works

1. **Initiating the Test**: Claude receives a request to test the load balancer.
2. **Executing the Test Suite**: Claude uses the `load-balancer-tester` plugin to run a series of tests, including traffic distribution validation, failover testing, sticky session verification, and health check testing.
3. **Presenting the Results**: Claude provides a summary of the test results, highlighting any issues or areas for improvement.

## When to Use This Skill

This skill activates when you need to:
- Validate traffic distribution across backend servers.
- Test the load balancer's ability to handle server failures.
- Verify that sticky sessions are functioning correctly.
- Ensure that health checks are effectively removing unhealthy servers from the pool.

## Examples

### Example 1: Validating Traffic Distribution

User request: "Test load balancer traffic distribution for even distribution across servers."

The skill will:
1. Execute the `lb-test` command.
2. Analyze the traffic distribution across the backend servers.
3. Report whether the traffic is evenly distributed.

### Example 2: Simulating a Failover Scenario

User request: "Test failover when one of the backend servers becomes unavailable."

The skill will:
1. Execute the `lb-test` command.
2. Simulate a server failure.
3. Verify that traffic is redirected to the remaining healthy servers.
4. Report on the success of the failover process.

## Best Practices

- **Configuration**: Ensure the load balancer is properly configured before testing.
- **Realistic Scenarios**: Test with realistic traffic patterns and failure scenarios.
- **Comprehensive Testing**: Test all aspects of the load balancer, including traffic distribution, failover, sticky sessions, and health checks.

## Integration

This skill works independently using the `load-balancer-tester` plugin. It can be used in conjunction with other skills to configure and manage the load balancer before testing.