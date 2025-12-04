---
name: generating-infrastructure-as-code
description: |
  This skill enables Claude to generate Infrastructure as Code (IaC) configurations. It uses the infrastructure-as-code-generator plugin to create production-ready IaC for Terraform, CloudFormation, Pulumi, ARM Templates, and CDK. Use this skill when the user requests IaC configurations for cloud infrastructure, specifying the platform (e.g., Terraform, CloudFormation) and cloud provider (e.g., AWS, Azure, GCP), or when the user needs help automating infrastructure deployment. Trigger terms include: "generate IaC", "create Terraform", "CloudFormation template", "Pulumi program", "infrastructure code".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to automate the creation of infrastructure code, streamlining the deployment and management of cloud resources. It supports multiple IaC platforms and cloud providers, ensuring flexibility and best practices.

## How It Works

1. **Receiving Request**: Claude receives a request for IaC generation, identifying the desired platform and cloud provider.
2. **Invoking Plugin**: Claude invokes the infrastructure-as-code-generator plugin with the user's specifications.
3. **Generating Code**: The plugin generates the requested IaC configuration based on the user's requirements.
4. **Presenting Code**: Claude presents the generated IaC code to the user for review and deployment.

## When to Use This Skill

This skill activates when you need to:
- Generate Terraform configurations for AWS, GCP, or Azure.
- Create CloudFormation templates for AWS infrastructure.
- Develop Pulumi programs for multi-cloud deployments.

## Examples

### Example 1: AWS ECS Fargate Infrastructure

User request: "Generate Terraform configuration for an AWS ECS Fargate cluster."

The skill will:
1. Invoke the infrastructure-as-code-generator plugin, specifying Terraform and AWS ECS Fargate.
2. Generate a Terraform configuration file defining the ECS cluster, task definition, and related resources.

### Example 2: Azure Resource Group Deployment

User request: "Create an ARM template for deploying an Azure Resource Group with a virtual network."

The skill will:
1. Invoke the infrastructure-as-code-generator plugin, specifying ARM template and Azure Resource Group.
2. Generate an ARM template defining the resource group and virtual network resources.

## Best Practices

- **Specificity**: Provide clear and specific requirements for the desired infrastructure.
- **Platform Selection**: Choose the appropriate IaC platform based on your cloud provider and organizational standards.
- **Review & Validation**: Always review and validate the generated IaC code before deploying it to production.

## Integration

This skill can be integrated with other Claude Code plugins for deployment automation, security scanning, and cost estimation, providing a comprehensive DevOps workflow. For example, it can be used with a deployment plugin to automatically deploy the generated infrastructure.