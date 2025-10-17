---
name: Configuring Load Balancers
description: |
  This skill configures load balancers, including ALB, NLB, Nginx, and HAProxy. It generates production-ready configurations based on specified requirements and infrastructure. Use this skill when the user asks to "configure load balancer", "create load balancer config", "generate nginx config", "setup HAProxy", or mentions specific load balancer types like "ALB" or "NLB". It's ideal for DevOps tasks, infrastructure automation, and generating load balancer configurations for different environments.
---

## Overview

This skill enables Claude to generate complete and production-ready configurations for various load balancers. It supports ALB, NLB, Nginx, and HAProxy, providing a streamlined approach to infrastructure automation and DevOps tasks.

## How It Works

1. **Receiving Requirements**: The skill receives user specifications for the load balancer configuration, including type, ports, protocols, and other relevant details.
2. **Generating Configuration**: Based on the user's requirements, the skill generates a complete configuration file tailored to the specified load balancer type.
3. **Presenting Configuration**: The generated configuration is presented to the user, ready for deployment.

## When to Use This Skill

This skill activates when you need to:
- Generate a load balancer configuration for a new application deployment.
- Modify an existing load balancer configuration to accommodate changes in traffic patterns or application requirements.
- Automate the creation of load balancer configurations as part of an infrastructure-as-code workflow.

## Examples

### Example 1: Setting up an Nginx Load Balancer

User request: "Configure an Nginx load balancer to distribute traffic between two backend servers on ports 8080 and 8081."

The skill will:
1. Generate an Nginx configuration file that includes upstream definitions for the two backend servers.
2. Present the complete Nginx configuration file to the user.

### Example 2: Creating an ALB Configuration

User request: "Create an ALB configuration for a web application running on port 80, with health checks on /health."

The skill will:
1. Generate an ALB configuration that includes listener rules, target groups, and health check settings.
2. Present the complete ALB configuration to the user, ready for deployment via AWS CloudFormation or Terraform.

## Best Practices

- **Security**: Always review generated configurations for security vulnerabilities before deploying them to production.
- **Testing**: Thoroughly test load balancer configurations in a staging environment before deploying them to production.
- **Documentation**: Document the purpose and configuration details of each load balancer for future reference.

## Integration

This skill can be integrated with other tools and plugins in the Claude Code ecosystem, such as infrastructure-as-code tools like Terraform and CloudFormation, to automate the deployment and management of load balancer configurations. It can also be used in conjunction with monitoring and logging tools to track the performance and health of load balancers.