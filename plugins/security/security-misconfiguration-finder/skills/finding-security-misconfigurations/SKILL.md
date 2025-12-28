---
name: finding-security-misconfigurations
description: |
  Identify security misconfigurations in infrastructure-as-code, application settings, and system configurations.
  Use when you need to audit Terraform/CloudFormation templates, check application config files, validate system security settings, or ensure compliance with security best practices.
  Trigger with phrases like "find security misconfigurations", "audit infrastructure security", "check config security", or "scan for misconfigured settings".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(config-scan:*), Bash(iac-check:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Security Misconfiguration Finder

This skill provides automated assistance for security misconfiguration finder tasks.

## Overview

Scans configuration and IaC sources for common security misconfigurations, prioritizes findings by severity, and recommends minimal-change remediations.

## Prerequisites

Before using this skill, ensure:
- Configuration files accessible in {baseDir}/ (Terraform, CloudFormation, YAML, JSON)
- Infrastructure-as-code files (.tf, .yaml, .json, .template)
- Application configuration files (application.yml, config.json, .env.example)
- System configuration exports available
- Write permissions for findings report in {baseDir}/security-findings/

## Instructions

1. Identify the target system/service and gather current configuration.
2. Compare settings against baseline hardening guidance.
3. Flag risky defaults, drift, and missing controls with severity.
4. Provide a minimal-change remediation plan and verification steps.

### 1. Configuration Discovery Phase

Locate configuration files to analyze:
- Infrastructure-as-code: Terraform (.tf), CloudFormation (.yaml/.json), Ansible, Kubernetes
- Application configs: application.yml, config.json, web.config, .properties
- Cloud provider configs: AWS, GCP, Azure resource definitions
- Container configs: Dockerfile, docker-compose.yml, Kubernetes manifests
- Web server configs: nginx.conf, httpd.conf, .htaccess

### 2. IaC Misconfiguration Checks

**Cloud Storage**:
- S3 buckets with public read/write access
- Storage accounts without encryption
- Publicly accessible blob containers
- Missing versioning on data stores

**Network Security**:
- Security groups allowing 0.0.0.0/0 on sensitive ports (22, 3389, 3306, 5432)
- Network ACLs with overly permissive rules
- VPCs without flow logs enabled
- Missing network segmentation

**Identity and Access**:
- IAM policies with wildcard (*) permissions
- Service accounts with admin privileges
- Missing MFA enforcement
- Overly broad role assignments
- Hardcoded credentials in code

**Compute Resources**:
- EC2 instances with public IPs unnecessarily
- Unencrypted EBS volumes
- Missing instance metadata service v2
- Outdated AMIs/images

**Database Security**:
- RDS instances publicly accessible
- Databases without encryption at rest
- Missing automated backups
- Weak password policies
- Default ports exposed

### 3. Application Configuration Checks

**Authentication/Authorization**:
- Debug mode enabled in production
- Default credentials present
- Weak session timeout values
- Missing CSRF protection
- Insecure password policies

**API Security**:
- API keys in configuration files
- CORS configured with wildcard (*)
- Missing rate limiting
- Unencrypted API endpoints
- Disabled authentication

**Data Protection**:
- Sensitive data in plain text
- Missing encryption configuration
- Insecure cookie settings (no HttpOnly, Secure flags)
- Logging sensitive information

**Dependencies**:
- Outdated library versions with CVEs
- Unmaintained packages
- Unnecessary dependencies

### 4. System Configuration Checks

**Operating System**:
- Unnecessary services enabled
- Weak SSH configurations
- Missing security updates
- Insecure file permissions
- Disabled firewalls

**Web Servers**:
- Directory listing enabled
- Server tokens exposed
- Missing security headers
- Weak TLS configurations
- Default error pages revealing information

### 5. Severity Classification

Rate findings by severity:
- **Critical**: Immediate exploitation risk (public S3, hardcoded secrets)
- **High**: Significant security impact (weak auth, missing encryption)
- **Medium**: Configuration weaknesses (overly permissive, missing logs)
- **Low**: Best practice violations (information disclosure, outdated configs)

### 6. Generate Findings Report

Document all misconfigurations with:
- Severity and category
- Specific configuration issue
- Security impact explanation
- Remediation steps with code examples
- Compliance implications (CIS, NIST, PCI-DSS)

## Output

The skill produces:

**Primary Output**: Security misconfigurations report saved to {baseDir}/security-findings/misconfig-YYYYMMDD.md

**Report Structure**:
```
# Security Misconfiguration Findings


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
Scan Date: 2024-01-15
Files Analyzed: 42
Findings: 15 (3 Critical, 5 High, 4 Medium, 3 Low)

## Critical Findings

### 1. Publicly Accessible S3 Bucket
**File**: {baseDir}/terraform/storage.tf
**Line**: 23
**Issue**: S3 bucket allows public read access
**Code**:
```hcl
resource "aws_s3_bucket" "data" {
  acl = "public-read"  # CRITICAL: Public access
}
```
**Impact**: Sensitive data exposed to internet
**Remediation**:
```hcl
resource "aws_s3_bucket" "data" {
  acl = "private"

  public_access_block {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }
}
```
**Compliance**: Violates CIS AWS 2.1.5, NIST AC-3

## High Findings

### 2. Security Group Allows SSH from Anywhere
**File**: {baseDir}/terraform/network.tf
**Line**: 45
**Issue**: Port 22 open to 0.0.0.0/0
**Impact**: Brute force attack surface
**Remediation**: Restrict to specific IP ranges or use bastion host

[Additional findings follow similar structure]

## Summary by Category
- IAM/Access Control: 4 findings
- Network Security: 6 findings
- Data Protection: 3 findings
- Logging/Monitoring: 2 findings

## Compliance Impact
- CIS Benchmarks: 8 violations
- NIST 800-53: 5 controls affected
- PCI-DSS: 3 requirements unmet
```

**Secondary Outputs**:
- JSON for CI/CD integration: {baseDir}/security-findings/misconfig-YYYYMMDD.json
- CSV for spreadsheet tracking
- SARIF format for GitHub Security tab

## Error Handling

**Common Issues and Resolutions**:

1. **Unable to Parse Configuration File**
   - Error: "Syntax error in {baseDir}/terraform/main.tf"
   - Resolution: Validate file syntax first, report parse errors separately
   - Fallback: Skip malformed files, note in report

2. **Missing Cloud Provider Context**
   - Error: "Cannot determine cloud provider from configuration"
   - Resolution: Look for provider blocks, file naming conventions
   - Fallback: Apply generic security checks only

3. **Encrypted or Binary Configuration Files**
   - Error: "Cannot read encrypted configuration"
   - Resolution: Request decrypted version or configuration export
   - Note: Document inability to audit in report

4. **Large Configuration Sets**
   - Error: "Too many files to analyze ({baseDir}/ has 500+ configs)"
   - Resolution: Prioritize by file type and location
   - Strategy: Start with IaC, then app configs, then system configs

5. **False Positives**
   - Error: "Flagged configuration is intentional (dev environment)"
   - Resolution: Allow environment-specific exceptions
   - Enhancement: Support ignore/exception rules file

## Examples

- "Scan our Terraform in {baseDir}/ for overly permissive security groups and IAM wildcards."
- "Review Kubernetes manifests for insecure defaults and propose fixes."

## Resources

**Security Benchmarks**:
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks/
- OWASP Configuration Guide: https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheatsheet.html
- Cloud Security Alliance: https://cloudsecurityalliance.org/

**IaC Security Tools**:
- tfsec (Terraform): https://github.com/aquasecurity/tfsec
- Checkov (Multi-cloud): https://www.checkov.io/
- cfn-nag (CloudFormation): https://github.com/stelligent/cfn_nag
- kube-bench (Kubernetes): https://github.com/aquasecurity/kube-bench

**Configuration Best Practices**:
- AWS Security Best Practices: https://aws.amazon.com/architecture/security-identity-compliance/
- Azure Security Baseline: https://docs.microsoft.com/en-us/security/benchmark/azure/
- GCP Security Best Practices: https://cloud.google.com/security/best-practices

**Compliance Frameworks**:
- CIS Controls: https://www.cisecurity.org/controls/
- NIST 800-53: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- PCI-DSS Requirements: https://www.pcisecuritystandards.org/

**Remediation Examples**:
- Terraform security modules: {baseDir}/templates/terraform-secure/
- CloudFormation secure templates: {baseDir}/templates/cfn-secure/
- Kubernetes security policies: {baseDir}/templates/k8s-policies/
