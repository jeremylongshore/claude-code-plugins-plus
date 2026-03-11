---
name: optimizing-cloud-costs
description: |
  Execute use when you need to work with cloud cost optimization.
  This skill provides cost analysis and optimization with comprehensive guidance and automation.
  Trigger with phrases like "optimize costs", "analyze spending",
  or "reduce costs".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(aws:*), Bash(gcloud:*), Bash(az:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Optimizing Cloud Costs

## Overview

Analyze cloud spending across AWS, GCP, and Azure to identify waste, recommend rightsizing, and generate cost-saving configurations. Covers reserved instances, spot/preemptible workloads, storage tiering, idle resource cleanup, and budget alerting using cloud-native cost management APIs.

## Prerequisites

- Cloud provider CLI authenticated with billing/cost-explorer read access
- AWS: `ce:GetCostAndUsage`, `ec2:DescribeInstances`, `cloudwatch:GetMetricData` permissions
- GCP: Billing Account Viewer and Compute Viewer roles
- Azure: Cost Management Reader role
- Access to current infrastructure-as-code (Terraform, CloudFormation) for rightsizing changes
- At least 30 days of billing data for meaningful analysis

## Instructions

1. Pull current cost data using cloud cost APIs (`aws ce get-cost-and-usage`, `gcloud billing budgets list`)
2. Identify the top 10 cost drivers by service, region, and resource tag
3. Detect idle resources: instances with < 5% average CPU over 14 days, unattached EBS volumes, unused Elastic IPs, orphaned snapshots
4. Recommend rightsizing: compare instance utilization against available instance types and suggest downsizing
5. Evaluate reserved instance or savings plan coverage against on-demand spend; recommend commitments for steady-state workloads
6. Identify spot/preemptible candidates: stateless, fault-tolerant workloads (batch jobs, CI runners, dev environments)
7. Review storage costs: recommend S3 Intelligent-Tiering, lifecycle policies for infrequent access, or Glacier for archives
8. Generate Terraform/IaC changes to implement approved optimizations
9. Set up budget alerts with thresholds at 50%, 80%, and 100% of monthly budget
10. Create a cost optimization report summarizing findings, savings estimates, and implementation priority

## Output

- Cost analysis report with per-service breakdown and savings recommendations
- Terraform/CloudFormation changes for rightsizing and reserved instance purchases
- S3 lifecycle policy configurations for storage tiering
- Budget alert configurations (CloudWatch, GCP Budget, Azure Cost Alerts)
- Cleanup scripts for idle resources (with dry-run mode for safety)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Access Denied on Cost Explorer API` | Missing `ce:*` IAM permissions | Attach the `AWSBillingReadOnlyAccess` managed policy to the IAM user/role |
| `No billing data available` | Account is too new or cost export not enabled | Enable Cost Explorer (takes 24h to populate) or set up CUR (Cost and Usage Report) |
| `Rightsizing recommendation breaks workload` | Instance too small for peak load | Base sizing on P95 utilization, not average; keep a 20% headroom buffer |
| `Spot instance terminated mid-job` | Spot capacity reclaimed by provider | Use spot fleet with diversified instance types and implement checkpointing |
| `Budget alert not firing` | SNS topic or notification channel misconfigured | Verify SNS subscription is confirmed and test with a low threshold |

## Examples

- "Analyze AWS costs for the last 3 months, identify the top waste areas, and generate a cleanup script for unattached EBS volumes and unused Elastic IPs."
- "Compare on-demand EC2 spend against Savings Plans pricing and recommend 1-year commitments for steady-state workloads."
- "Create S3 lifecycle policies to move objects older than 90 days to Glacier and delete after 365 days across all buckets tagged `env:production`."

## Resources

- AWS Cost Explorer: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html
- GCP Cost Management: https://cloud.google.com/billing/docs/how-to/budgets
- Azure Cost Management: https://learn.microsoft.com/en-us/azure/cost-management-billing/
- FinOps Foundation: https://www.finops.org/framework/
