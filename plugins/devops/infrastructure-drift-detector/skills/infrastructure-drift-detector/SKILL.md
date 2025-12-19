---
description: Use when detecting infrastructure drift from desired state. Trigger with phrases like "check for drift", "infrastructure drift detection", "compare actual vs desired state", or "detect configuration changes". Identifies discrepancies between current infrastructure and IaC definitions using terraform plan, cloudformation drift detection, or manual comparison.
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(terraform:*)
- Bash(aws:*)
- Bash(gcloud:*)
name: detecting-infrastructure-drift
license: MIT
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

## Prerequisites

Before using this skill, ensure:
- Infrastructure as Code (IaC) files are up to date in {baseDir}
- Cloud provider CLI is installed and authenticated
- IaC tool (Terraform/CloudFormation/Pulumi) is installed
- Remote state storage is configured and accessible
- Appropriate read permissions for infrastructure resources

## Instructions

1. **Identify IaC Tool**: Determine if using Terraform, CloudFormation, Pulumi, or ARM
2. **Fetch Current State**: Retrieve actual infrastructure state from cloud provider
3. **Load Desired State**: Read IaC configuration from {baseDir}/terraform or equivalent
4. **Compare States**: Execute drift detection command for the IaC platform
5. **Analyze Differences**: Identify added, modified, or removed resources
6. **Generate Report**: Create detailed report of drift with affected resources
7. **Suggest Remediation**: Provide commands to resolve drift (apply or import)
8. **Document Findings**: Save drift report to {baseDir}/drift-reports/

## Output

Generates drift detection reports:

**Terraform Drift Report:**
```
Drift Detection Report - 2025-12-10 10:30:00
==============================================

Resources with Drift: 3

1. aws_instance.web_server
   Status: Modified
   Drift: instance_type changed from "t3.micro" to "t3.small"
   Action: Update IaC to match or revert instance type

2. aws_s3_bucket.assets
   Status: Modified
   Drift: versioning_enabled changed from true to false
   Action: Re-enable versioning or update IaC

3. aws_iam_role.lambda_exec
   Status: Deleted
   Drift: Role no longer exists in AWS
   Action: terraform apply to recreate

Remediation Command:
terraform plan -out=drift-fix.tfplan
terraform apply drift-fix.tfplan
```

**CloudFormation Drift:**
```yaml
StackName: production-vpc
DriftStatus: DRIFTED
Resources:
  - LogicalResourceId: VPC
    ResourceType: AWS::EC2::VPC
    DriftStatus: IN_SYNC
  - LogicalResourceId: PublicSubnet
    ResourceType: AWS::EC2::Subnet
    DriftStatus: MODIFIED
    PropertyDifferences:
      - PropertyPath: /Tags
        ExpectedValue: [{Key: Env, Value: prod}]
        ActualValue: [{Key: Env, Value: production}]
```

## Error Handling

Common issues and solutions:

**State Lock Error**
- Error: "Error acquiring state lock"
- Solution: Ensure no other terraform process is running, or force-unlock if safe

**Authentication Failure**
- Error: "Unable to authenticate to cloud provider"
- Solution: Refresh credentials with `aws configure` or `gcloud auth login`

**Missing State File**
- Error: "No state file found"
- Solution: Initialize terraform with `terraform init` or specify remote backend

**Permission Denied**
- Error: "Access denied reading resource"
- Solution: Grant read-only IAM permissions to service account

**State Version Mismatch**
- Error: "State file version too new"
- Solution: Upgrade Terraform version or use compatible state version

## Resources

- Terraform drift documentation: https://www.terraform.io/docs/cli/state/
- AWS CloudFormation drift detection: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/detect-drift-stack.html
- Drift remediation best practices in {baseDir}/docs/drift-remediation.md
- Automated drift detection scripts in {baseDir}/scripts/drift-check.sh