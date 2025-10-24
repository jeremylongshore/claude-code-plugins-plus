---
name: conducting-chaos-engineering
description: |
  This skill enables Claude to design and execute chaos engineering experiments to test system resilience. It is used when the user requests help with failure injection, latency simulation, resource exhaustion testing, or resilience validation. The skill is triggered by discussions of chaos experiments (GameDays), failure injection strategies, resilience testing, and validation of recovery mechanisms like circuit breakers and retry logic. It leverages tools like Chaos Mesh, Gremlin, Toxiproxy, and AWS FIS to simulate real-world failures and assess system behavior.
---

## Overview

This skill empowers Claude to act as a chaos engineering specialist, guiding users through the process of designing and implementing controlled failure scenarios to identify weaknesses and improve the robustness of their systems. It facilitates the creation of chaos experiments to validate system resilience and recovery mechanisms.

## How It Works

1. **Experiment Design**: Claude helps define the scope, target system, and failure scenarios for the chaos experiment based on the user's objectives.
2. **Tool Selection**: Claude recommends appropriate chaos engineering tools (e.g., Chaos Mesh, Gremlin, Toxiproxy, AWS FIS) based on the target environment and desired failure types.
3. **Execution and Monitoring**: Claude assists with configuring and executing the chaos experiment, while monitoring key metrics to observe system behavior under stress.
4. **Analysis and Recommendations**: Claude analyzes the results of the experiment, identifies vulnerabilities, and provides recommendations for improving system resilience.

## When to Use This Skill

This skill activates when you need to:
- Design a chaos experiment to test the resilience of a specific service or application.
- Implement failure injection strategies to simulate real-world outages.
- Validate the effectiveness of circuit breakers and retry mechanisms.
- Analyze system behavior under stress and identify potential vulnerabilities.

## Examples

### Example 1: Database Failover Testing

User request: "Help me design a chaos experiment to test our database failover process."

The skill will:
1. Design a chaos experiment involving simulated database failures and automated failover.
2. Recommend using Chaos Mesh for Kubernetes environments or AWS FIS for AWS-hosted databases.

### Example 2: API Latency Simulation

User request: "Create a latency injection test for our API gateway to simulate network congestion."

The skill will:
1. Design a latency injection test using Toxiproxy to introduce delays in API requests.
2. Monitor API response times and error rates to assess the impact of latency.

## Best Practices

- **Define Clear Objectives**: Clearly define the goals of the chaos experiment and the specific system behavior you want to test.
- **Start Small**: Begin with small-scale experiments and gradually increase the scope and intensity of the failures.
- **Automate and Monitor**: Automate the execution and monitoring of chaos experiments to ensure repeatability and accurate data collection.

## Integration

This skill integrates with various chaos engineering tools, allowing Claude to orchestrate failure injection, latency simulation, and resource exhaustion testing across different environments. It can also be used in conjunction with monitoring tools to track system behavior and identify potential vulnerabilities.