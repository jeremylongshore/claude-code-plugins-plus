---
name: generating-infrastructure-as-code
description: |
  Use when generating infrastructure as code configurations. Trigger with phrases like "create Terraform config", "generate CloudFormation template", "write Pulumi code", or "IaC for AWS/GCP/Azure". Produces production-ready code for Terraform, CloudFormation, Pulumi, ARM templates, and CDK across multiple cloud providers.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(terraform:*), Bash(aws:*), Bash(gcloud:*), Bash(az:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Infrastructure As Code Generator

This skill provides automated assistance for infrastructure as code generator tasks.

## Overview

Generates production-ready IaC (Terraform/CloudFormation/Pulumi/etc.) with modular structure, variables, outputs, and deployment guidance for common cloud stacks.

## Prerequisites

Before using this skill, ensure:
- Target cloud provider CLI is installed (aws-cli, gcloud, az)
- IaC tool is installed (Terraform, Pulumi, AWS CDK)
- Cloud credentials are configured locally
- Understanding of target infrastructure architecture
- Version control system for IaC storage

## Instructions

1. **Identify Platform**: Determine IaC tool (Terraform, CloudFormation, Pulumi, ARM, CDK)
2. **Define Resources**: Specify cloud resources needed (compute, network, storage, database)
3. **Establish Structure**: Create modular file structure for maintainability
4. **Generate Code**: Write IaC configurations with proper syntax and formatting
5. **Add Variables**: Define input variables for environment-specific values
6. **Configure Outputs**: Specify outputs for resource references and integrations
7. **Implement State**: Set up remote state storage for team collaboration
8. **Document Usage**: Add README with deployment instructions and prerequisites

## Output

Generates infrastructure as code files:

**Terraform Example:**
```hcl
# {baseDir}/terraform/main.tf


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project}-vpc"
    Environment = var.environment
  }
}
```

**CloudFormation Example:**
```yaml
# {baseDir}/cloudformation/template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Production VPC infrastructure

Parameters:
  VpcCidr:
    Type: String
    Default: 10.0.0.0/16

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsHostnames: true
```

**Pulumi Example:**
```typescript
// {baseDir}/pulumi/index.ts
import * as aws from "@pulumi/aws";

const vpc = new aws.ec2.Vpc("main", {
    cidrBlock: "10.0.0.0/16",
    enableDnsHostnames: true,
    tags: {
        Name: "production-vpc"
    }
});

export const vpcId = vpc.id;
```

## Error Handling

Common issues and solutions:

**Syntax Errors**
- Error: "Invalid resource syntax in configuration"
- Solution: Validate syntax with `terraform validate` or respective tool linter

**Provider Authentication**
- Error: "Unable to authenticate with cloud provider"
- Solution: Configure credentials via environment variables or CLI login

**Resource Conflicts**
- Error: "Resource already exists"
- Solution: Import existing resources or use data sources instead of creating new ones

**State Lock Issues**
- Error: "Error acquiring state lock"
- Solution: Ensure no other process is running, or force unlock if safe

**Dependency Errors**
- Error: "Resource depends on resource that does not exist"
- Solution: Check resource references and ensure proper dependency ordering

## Examples

- "Generate Terraform for a VPC + private subnets + NAT + EKS cluster on AWS."
- "Create a minimal CloudFormation template for an S3 bucket with encryption and public access blocked."

## Resources

- Terraform documentation: https://www.terraform.io/docs/
- AWS CloudFormation guide: https://docs.aws.amazon.com/cloudformation/
- Pulumi documentation: https://www.pulumi.com/docs/
- Azure ARM templates: https://docs.microsoft.com/azure/azure-resource-manager/
- IaC best practices guide in {baseDir}/docs/iac-standards.md
