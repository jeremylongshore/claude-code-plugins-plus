---
name: Integrating Secrets Managers
description: |
  This skill enables Claude to seamlessly integrate with various secrets managers like HashiCorp Vault and AWS Secrets Manager. It generates configurations and setup code, ensuring best practices for secure credential management. Use this skill when you need to manage sensitive information, generate production-ready configurations, or implement a security-first approach for your DevOps infrastructure. Trigger terms include "integrate secrets manager", "configure Vault", "AWS Secrets Manager setup", "manage credentials securely", or requests for secure configuration generation.
---

## Overview

This skill empowers Claude to automate the integration of secrets managers into your infrastructure. It generates the necessary configuration files and setup code, ensuring a secure and efficient workflow for managing sensitive credentials.

## How It Works

1. **Identify Requirements**: Claude analyzes the user's request to determine the specific secrets manager and desired configurations.
2. **Generate Configuration**: Based on the identified requirements, Claude generates the appropriate configuration files (e.g., Vault policies, AWS IAM roles) and setup code.
3. **Provide Instructions**: Claude provides clear instructions on how to deploy and configure the generated code and integrate it into the existing infrastructure.

## When to Use This Skill

This skill activates when you need to:
- Integrate HashiCorp Vault into your infrastructure.
- Set up AWS Secrets Manager for secure credential storage.
- Generate configuration files for managing secrets.
- Implement best practices for secrets management.

## Examples

### Example 1: Integrating Vault with a Kubernetes Cluster

User request: "Integrate Vault with my Kubernetes cluster for managing database credentials."

The skill will:
1. Generate Vault policies for accessing database credentials.
2. Create Kubernetes service accounts with appropriate annotations for Vault integration.
3. Provide instructions for deploying the Vault agent injector to the Kubernetes cluster.

### Example 2: Setting up AWS Secrets Manager for API Keys

User request: "Set up AWS Secrets Manager to securely store API keys for my application."

The skill will:
1. Generate an IAM role with permissions to access AWS Secrets Manager.
2. Create a Secrets Manager secret containing the API keys.
3. Provide code snippets for retrieving the API keys from Secrets Manager within the application.

## Best Practices

- **Least Privilege**: Generate configurations that grant only the necessary permissions for accessing secrets.
- **Secure Storage**: Ensure that secrets are stored securely within the chosen secrets manager.
- **Regular Rotation**: Implement a strategy for regularly rotating secrets to minimize the impact of potential breaches.

## Integration

This skill can be used in conjunction with other skills for deploying applications, configuring infrastructure, and automating DevOps workflows. It provides a secure foundation for managing sensitive information across your entire infrastructure.