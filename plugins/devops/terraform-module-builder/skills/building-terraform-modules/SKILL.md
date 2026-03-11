---
name: building-terraform-modules
description: |
  Execute this skill empowers AI assistant to build reusable terraform modules based on user specifications. it leverages the terraform-module-builder plugin to generate production-ready, well-documented terraform module code, incorporating best practices for sec... Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Building Terraform Modules

## Overview

Build reusable, production-ready Terraform modules with proper variable definitions, outputs, validation rules, documentation, and examples. Generate modules following HashiCorp's standard module structure for AWS, GCP, and Azure resources with security best practices, tagging conventions, and lifecycle management.

## Prerequisites

- Terraform 1.0+ installed (`terraform version`)
- Cloud provider credentials configured for the target platform
- Understanding of the infrastructure resources the module will manage
- Familiarity with HCL syntax and Terraform module conventions
- `terraform-docs` installed for automated documentation generation (optional)

## Instructions

1. Define the module scope: determine which cloud resources the module manages and its input/output contract
2. Create the standard module file structure: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `locals.tf`
3. Write `versions.tf` with `required_version` and `required_providers` blocks pinned to stable versions
4. Define input variables in `variables.tf` with descriptions, types, defaults, and validation rules
5. Implement resources in `main.tf` using variables for all configurable values; use `locals` for computed values
6. Add meaningful outputs in `outputs.tf` for resource IDs, ARNs, endpoints, and connection strings
7. Implement security defaults: encryption enabled, public access blocked, least-privilege IAM, logging enabled
8. Create an `examples/` directory with at least one complete usage example showing module invocation
9. Generate documentation with `terraform-docs markdown table . > README.md`
10. Validate the module with `terraform init && terraform validate` and test with `terraform plan` using the example

## Output

- Module files: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `locals.tf`
- Example usage in `examples/basic/main.tf` with realistic variable values
- Auto-generated `README.md` with inputs, outputs, and usage documentation
- `.terraform-docs.yml` configuration for documentation generation
- Optional: test files using Terratest or `terraform test` (HCL-based)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `variable validation failed` | Input value does not meet validation rule | Check the `validation` block in `variables.tf`; adjust the value or the validation regex |
| `provider not found` | Missing or wrong provider source in `versions.tf` | Add the provider to `required_providers` with correct source and version constraint |
| `circular dependency` | Resources referencing each other in a loop | Refactor to break the cycle; use `depends_on` or separate into sub-modules |
| `output references undeclared resource` | Typo in resource name or resource removed | Verify resource names in `main.tf` match output references exactly |
| `module source not found` | Incorrect module path or registry reference | Verify the `source` path is relative (e.g., `./modules/vpc`) or a valid registry address |

## Examples

- "Build a Terraform module for an AWS VPC with configurable CIDR, public/private subnets across 3 AZs, NAT gateway, and flow logs."
- "Create a GCP Cloud Run module with custom domain, IAM bindings, and auto-scaling configuration as input variables."
- "Generate a Terraform module for an S3 bucket with versioning, encryption, lifecycle rules, and access logging, with all settings as optional variables with secure defaults."

## Resources

- Terraform module registry: https://registry.terraform.io/
- Module structure guide: https://developer.hashicorp.com/terraform/language/modules/develop/structure
- terraform-docs: https://terraform-docs.io/
- Module best practices: https://developer.hashicorp.com/terraform/language/modules/develop
