---
name: managing-container-registries
description: |
  This skill enables Claude to manage container registries, including ECR, GCR, and Harbor. It should be used when the user needs to create, configure, or manage container image registries. It helps generate production-ready configurations, implement best practices, and ensure a security-first approach. Use this skill when the user mentions terms like "container registry," "ECR," "GCR," "Harbor," "image repository," or requests assistance with managing container images. It's also helpful for generating configuration code for DevOps pipelines related to container registries.
---

## Overview

This skill empowers Claude to assist users in managing their container registries across various platforms like AWS ECR, Google GCR, and Harbor. It provides the ability to generate configurations, implement best practices, and ensure secure and scalable architectures for container image storage and management.

## How It Works

1. **Receiving User Request**: Claude receives a request related to container registry management.
2. **Identifying Registry Type**: Claude identifies the specific container registry (ECR, GCR, Harbor, etc.) based on the user's input.
3. **Generating Configuration**: Claude generates the necessary configuration code and setup instructions based on the user's requirements and the identified registry.

## When to Use This Skill

This skill activates when you need to:
- Create a new container registry on ECR, GCR, or Harbor.
- Configure access permissions for a container registry.
- Generate deployment configurations for container images.

## Examples

### Example 1: Creating an ECR Repository

User request: "Create an ECR repository named 'my-app-images' in the 'us-west-2' region."

The skill will:
1. Generate the necessary AWS CLI commands or Terraform configuration to create the ECR repository.
2. Provide instructions on how to push container images to the newly created repository.

### Example 2: Configuring GCR Access

User request: "Grant read-only access to the 'my-gcp-project' GCR repository to the 'dev-team' Google Cloud group."

The skill will:
1. Generate the appropriate `gcloud` commands or IAM policy configuration to grant the requested access.
2. Provide instructions on how to verify the access permissions.

## Best Practices

- **Security**: Always use the principle of least privilege when granting access to container registries.
- **Versioning**: Implement a robust image tagging and versioning strategy.
- **Automation**: Automate the creation and configuration of container registries using infrastructure-as-code tools like Terraform.

## Integration

This skill integrates with other DevOps-related plugins to provide a seamless experience for managing containerized applications. It can be used in conjunction with plugins for CI/CD pipelines, infrastructure provisioning, and security scanning to build a complete DevOps workflow.