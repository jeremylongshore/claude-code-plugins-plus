---
name: checking-infrastructure-compliance
description: |
  Execute use when you need to work with compliance checking.
  This skill provides compliance monitoring and validation with comprehensive guidance and automation.
  Trigger with phrases like "check compliance", "validate policies",
  or "audit compliance".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Checking Infrastructure Compliance

## Overview

Audit infrastructure configurations against compliance frameworks (CIS Benchmarks, SOC 2, HIPAA, PCI-DSS, GDPR) using policy-as-code tools like Open Policy Agent (OPA), Checkov, and tfsec. Generate compliance reports, identify violations, and produce remediation plans for Terraform, Kubernetes, and cloud provider configurations.

## Prerequisites

- Policy-as-code tool installed: `checkov`, `tfsec`, `opa`, or `kube-bench`
- Infrastructure-as-code files (Terraform, CloudFormation, Kubernetes manifests) in the project
- Cloud provider CLI authenticated with read access to resources
- Compliance framework requirements documented (CIS, SOC 2, HIPAA, PCI-DSS)
- `jq` for parsing JSON policy outputs

## Instructions

1. Identify the applicable compliance framework(s) based on industry and data classification
2. Scan Terraform files with `checkov -d .` or `tfsec .` to detect misconfigurations
3. Scan Kubernetes manifests for security issues: missing resource limits, privileged containers, missing network policies
4. Validate IAM policies for least-privilege violations using cloud-native tools (`aws iam access-analyzer`)
5. Check encryption at rest and in transit: verify S3 bucket encryption, database TLS, and EBS volume encryption
6. Audit logging configurations: confirm CloudTrail/Cloud Audit Logs are enabled and sent to immutable storage
7. Generate a compliance report mapping each finding to the relevant control (e.g., CIS AWS 2.1.1)
8. Produce remediation Terraform/YAML patches for each violation with severity ranking (Critical, High, Medium, Low)
9. Set up CI/CD integration so compliance checks block merges on Critical/High violations

## Output

- Compliance scan results in JSON/SARIF format for CI integration
- Markdown compliance report with control mappings and pass/fail status
- Remediation code patches (Terraform diffs, Kubernetes manifest updates)
- OPA/Rego policy files for custom organizational rules
- CI/CD pipeline step configuration for automated compliance gating

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `checkov: no Terraform files found` | Scanner run from wrong directory | Specify path explicitly with `-d path/to/terraform/` |
| `tfsec: failed to parse HCL` | Syntax error in Terraform files | Run `terraform validate` first to fix HCL syntax before compliance scan |
| `False positive on compliance check` | Rule too broad for the specific use case | Add inline skip comments (`#checkov:skip=CKV_AWS_18:Reason`) or create a `.checkov.yml` skip list |
| `OPA policy evaluation error` | Rego syntax error or missing input data | Test policies with `opa eval -d policy.rego -i input.json` and validate Rego syntax |
| `Scan timeout on large codebase` | Too many files or complex module references | Use `--compact` mode, scan directories individually, or increase timeout limits |

## Examples

- "Run a CIS Benchmark compliance check against all Terraform files and generate a report with remediation steps for Critical findings."
- "Create OPA policies that enforce: all S3 buckets must have encryption, all EC2 instances must have IMDSv2, and all security groups must not allow 0.0.0.0/0 ingress."
- "Scan Kubernetes manifests for PCI-DSS compliance: verify no privileged containers, all pods have resource limits, and network policies exist for every namespace."

## Resources

- Checkov: https://www.checkov.io/
- tfsec: https://aquasecurity.github.io/tfsec/
- Open Policy Agent: https://www.openpolicyagent.org/docs/latest/
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks
- kube-bench (CIS for Kubernetes): https://github.com/aquasecurity/kube-bench
