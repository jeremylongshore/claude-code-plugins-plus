---
name: detecting-infrastructure-drift
description: |
  Execute use when detecting infrastructure drift from desired state. Trigger with phrases like "check for drift", "infrastructure drift detection", "compare actual vs desired state", or "detect configuration changes". Identifies discrepancies between current infrastructure and IaC definitions using terraform plan, cloudformation drift detection, or manual comparison.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(terraform:*), Bash(aws:*), Bash(gcloud:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Detecting Infrastructure Drift

## Current State
!`ls *.tf Dockerfile docker-compose.yml 2>/dev/null || echo 'No IaC files found'`
!`terraform version 2>/dev/null || echo 'Terraform not installed'`

## Overview

Detect discrepancies between actual cloud infrastructure state and the desired state defined in IaC (Terraform, CloudFormation, Pulumi). Run drift detection commands, analyze modified/added/deleted resources, generate drift reports with affected resources, and provide remediation steps to bring infrastructure back into compliance.

## Prerequisites

- IaC configuration files up to date in the project directory
- Cloud provider CLI installed and authenticated with read access to all managed resources
- IaC tool installed: Terraform 1.0+, AWS CLI (for CloudFormation drift), or Pulumi
- Remote state storage accessible and current (S3 backend, Terraform Cloud, Pulumi Cloud)
- Read-only IAM permissions for all resource types managed by IaC

## Instructions

1. Identify the IaC tool in use by scanning for `.tf` files, `template.yaml`, or `Pulumi.yaml`
2. Initialize the IaC tool if needed: `terraform init` to download providers and configure backend
3. Run drift detection: `terraform plan -detailed-exitcode` (exit code 2 = drift detected), `aws cloudformation detect-stack-drift`, or `pulumi preview`
4. Parse the output to identify resources with drift: added (exists in cloud but not in IaC), modified (attributes changed), or deleted (in IaC but missing from cloud)
5. For each drifted resource, determine if the drift is intentional (manual hotfix) or unintentional (configuration error, unauthorized change)
6. Generate a structured drift report with resource identifiers, attribute differences, and severity classification
7. Provide remediation options per resource: `terraform apply` to enforce desired state, `terraform import` to adopt changes, or update IaC to match reality
8. Schedule recurring drift detection: configure a cron job or CI pipeline to run daily and alert on drift
9. Investigate the root cause: determine who made the manual change and implement guardrails (SCPs, IAM restrictions) to prevent recurrence

## Output

- Drift detection report with resource-level detail: resource type, ID, drifted attributes, expected vs. actual values
- Remediation commands: `terraform apply`, `terraform import`, or IaC code updates
- CI/CD pipeline step for automated drift detection on a schedule
- Alert configuration for drift detection results (Slack, email, PagerDuty)
- Prevention recommendations: IAM policy restrictions, SCP guardrails, automated enforcement

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Error acquiring state lock` | Another Terraform process is running or stale lock | Wait for the other process; use `terraform force-unlock <ID>` if the lock is stale |
| `Unable to authenticate to cloud provider` | Expired or missing credentials | Refresh with `aws configure`, `gcloud auth login`, or `az login` |
| `No state file found` | Backend not initialized or state file deleted | Run `terraform init` to configure the backend; restore state from backup if deleted |
| `Access denied reading resource` | IAM policy missing read permissions for some resource types | Grant read-only access for all resource types managed by IaC (`ReadOnlyAccess` or specific policies) |
| `State file version mismatch` | Terraform version newer than state format | Upgrade Terraform to match the state version or use `terraform state replace-provider` |

## Examples

- "Run drift detection against all Terraform-managed infrastructure and generate a report of resources that have changed since last apply."
- "Set up a daily GitHub Actions workflow that runs `terraform plan` and posts drift results to Slack if any resources are out of sync."
- "Detect CloudFormation stack drift for the production VPC stack and provide remediation steps for any MODIFIED resources."

## Resources

- Terraform drift detection: https://developer.hashicorp.com/terraform/tutorials/state/resource-drift
- CloudFormation drift detection: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/detect-drift-stack.html
- Pulumi drift detection: https://www.pulumi.com/docs/using-pulumi/pulumi-packages/guides/drift-detection/
- Preventing drift: https://developer.hashicorp.com/terraform/tutorials/state/refresh