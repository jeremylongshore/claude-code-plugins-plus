---
name: Configuring Auto-Scaling Policies
description: |
  This skill configures auto-scaling policies for applications and infrastructure. It generates production-ready configurations based on user requirements, implementing best practices for scalability and security. Use this skill when the user requests help with auto-scaling setup, high availability, or dynamic resource allocation, specifically mentioning terms like "auto-scaling," "HPA," "scaling policies," or "dynamic scaling." This skill provides complete configuration code for various platforms.
---

## Overview

This skill empowers Claude to create and configure auto-scaling policies tailored to specific application and infrastructure needs. It streamlines the process of setting up dynamic resource allocation, ensuring optimal performance and resilience.

## How It Works

1. **Requirement Gathering**: Claude analyzes the user's request to understand the specific auto-scaling requirements, including target metrics (CPU, memory, etc.), scaling thresholds, and desired platform.
2. **Configuration Generation**: Based on the gathered requirements, Claude generates a production-ready auto-scaling configuration, incorporating best practices for security and scalability. This includes HPA configurations, scaling policies, and necessary infrastructure setup code.
3. **Code Presentation**: Claude presents the generated configuration code to the user, ready for deployment.

## When to Use This Skill

This skill activates when you need to:
- Configure auto-scaling for a Kubernetes deployment.
- Set up dynamic scaling policies based on CPU or memory utilization.
- Implement high availability and fault tolerance through auto-scaling.

## Examples

### Example 1: Scaling a Web Application

User request: "I need to configure auto-scaling for my web application in Kubernetes based on CPU utilization. Scale up when CPU usage exceeds 70%."

The skill will:
1. Analyze the request and identify the need for a Kubernetes HPA configuration.
2. Generate an HPA configuration file that scales the web application based on CPU utilization, with a target threshold of 70%.

### Example 2: Scaling Infrastructure Based on Load

User request: "Configure auto-scaling for my infrastructure to handle peak loads during business hours. Scale up based on the number of incoming requests."

The skill will:
1. Analyze the request and determine the need for infrastructure-level auto-scaling policies.
2. Generate configuration code for scaling the infrastructure based on the number of incoming requests, considering peak load times.

## Best Practices

- **Monitoring**: Ensure proper monitoring is in place to track the performance metrics used for auto-scaling decisions.
- **Threshold Setting**: Carefully choose scaling thresholds to avoid excessive scaling or under-provisioning.
- **Testing**: Thoroughly test the auto-scaling configuration to ensure it behaves as expected under various load conditions.

## Integration

This skill can be used in conjunction with other DevOps plugins to automate the entire deployment pipeline, from code generation to infrastructure provisioning.