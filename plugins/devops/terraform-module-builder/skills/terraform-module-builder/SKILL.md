---
name: building-terraform-modules
description: |
  This skill empowers AI assistant to build reusable terraform modules based on user specifications. it leverages the terraform-module-builder plugin to generate production-ready, well-documented terraform module code, incorporating best practices for sec... Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Overview

This skill allows Claude to efficiently generate Terraform modules, streamlining infrastructure-as-code development. By utilizing the terraform-module-builder plugin, it ensures modules are production-ready, well-documented, and incorporate best practices.

## How It Works

1. **Receiving User Request**: Claude receives a request to create a Terraform module, including details about the module's purpose and desired features.
2. **Generating Module Structure**: Claude invokes the terraform-module-builder plugin to create the basic file structure and configuration files for the module.
3. **Customizing Module Content**: Claude uses the user's specifications to populate the module with variables, outputs, and resource definitions, ensuring best practices are followed.

## When to Use This Skill

This skill activates when you need to:
- Create a new Terraform module from scratch.
- Generate production-ready Terraform configuration files.
- Implement infrastructure as code using Terraform modules.

## Examples

### Example 1: Creating a VPC Module

User request: "Create a Terraform module for a VPC with public and private subnets, a NAT gateway, and appropriate security groups."

The skill will:
1. Invoke the terraform-module-builder plugin to generate a basic VPC module structure.
2. Populate the module with Terraform code to define the VPC, subnets, NAT gateway, and security groups based on best practices.

### Example 2: Generating an S3 Bucket Module

User request: "Generate a Terraform module for an S3 bucket with versioning enabled, encryption at rest, and a lifecycle policy for deleting objects after 30 days."

The skill will:
1. Invoke the terraform-module-builder plugin to create a basic S3 bucket module structure.
2. Populate the module with Terraform code to define the S3 bucket with the requested features (versioning, encryption, lifecycle policy).

## Best Practices

- **Documentation**: Ensure the generated Terraform module includes comprehensive documentation, explaining the module's purpose, inputs, and outputs.
- **Security**: Implement security best practices, such as using least privilege principles and encrypting sensitive data.
- **Modularity**: Design the Terraform module to be reusable and configurable, allowing it to be easily adapted to different environments.

## Integration

This skill integrates seamlessly with other Claude Code plugins by providing a foundation for infrastructure provisioning. The generated Terraform modules can be used by other plugins to deploy and manage resources in various cloud environments.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Resources

- Project documentation
- Related skills and commands