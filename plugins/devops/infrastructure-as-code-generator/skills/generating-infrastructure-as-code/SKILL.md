---
name: generating-infrastructure-as-code
description: |
  Execute use when generating infrastructure as code configurations. Trigger with phrases like "create Terraform config", "generate CloudFormation template", "write Pulumi code", or "IaC for AWS/GCP/Azure". Produces production-ready code for Terraform, CloudFormation, Pulumi, ARM templates, and CDK across multiple cloud providers.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(terraform:*), Bash(aws:*), Bash(gcloud:*), Bash(az:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Generating Infrastructure as Code

## Overview

Generate production-ready infrastructure as code for Terraform, CloudFormation, Pulumi, ARM templates, and AWS CDK. Produce modular, well-structured configurations with proper variable definitions, outputs, remote state management, and deployment guidance for AWS, GCP, and Azure cloud stacks.

## Prerequisites

- Target cloud provider CLI installed and authenticated (`aws`, `gcloud`, `az`)
- IaC tool installed: Terraform 1.0+, Pulumi 3+, AWS CDK, or relevant SDK
- Cloud credentials configured with permissions to create the target resources
- Understanding of the desired infrastructure architecture (compute, networking, storage, database)
- Version control repository for storing IaC configurations

## Instructions

1. Identify the IaC tool and cloud provider based on the project requirements and existing codebase
2. Scan the project for existing IaC files to understand current patterns and conventions
3. Define the modular file structure: separate files for providers, networking, compute, storage, and databases
4. Generate the provider configuration with version pinning and remote backend for state storage
5. Define input variables with types, descriptions, defaults, and validation rules for all configurable values
6. Write resource definitions following cloud provider best practices: encryption enabled, logging configured, least-privilege IAM
7. Add outputs for resource identifiers, endpoints, and connection strings needed by other modules or applications
8. Configure remote state backend: S3 + DynamoDB for Terraform, Pulumi Cloud, or CloudFormation stack exports
9. Create environment-specific variable files (`terraform.tfvars`, `dev.tfvars`, `prod.tfvars`) for multi-environment deployment
10. Validate with `terraform validate`, `terraform plan`, or equivalent tool-specific linting

## Output

- IaC configuration files organized by resource type or module
- Variable definition files with documented inputs and sensible defaults
- Output definitions for cross-module references and application configuration
- Backend configuration for remote state storage
- Environment-specific variable files for dev, staging, and production
- Deployment instructions with prerequisite setup and apply commands

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Invalid HCL syntax` | Malformed Terraform configuration | Run `terraform validate` to identify the error; check bracket matching and attribute syntax |
| `Unable to authenticate with cloud provider` | Missing or expired credentials | Run `aws configure`, `gcloud auth login`, or `az login` to refresh credentials |
| `Resource already exists` | Trying to create a resource that exists outside of IaC management | Use `terraform import` to bring the existing resource under management |
| `Error acquiring state lock` | Another process holding the state lock | Wait for the other process to finish; use `terraform force-unlock <ID>` if the lock is stale |
| `Dependency cycle detected` | Resources referencing each other circularly | Refactor to remove the cycle; use data sources or `depends_on` to establish explicit ordering |

## Examples

- "Generate Terraform for a production VPC on AWS with public/private subnets across 3 AZs, NAT gateways, VPC flow logs, and an EKS cluster."
- "Create a CloudFormation template for an S3 bucket with versioning, server-side encryption (KMS), public access block, and lifecycle rules."
- "Write Pulumi TypeScript code for a GCP Cloud Run service with a custom domain, Cloud SQL database, and Secret Manager integration."

## Resources

- Terraform documentation: https://developer.hashicorp.com/terraform/docs
- AWS CloudFormation: https://docs.aws.amazon.com/cloudformation/
- Pulumi: https://www.pulumi.com/docs/
- AWS CDK: https://docs.aws.amazon.com/cdk/v2/guide/
- Azure ARM/Bicep: https://learn.microsoft.com/en-us/azure/azure-resource-manager/
