---
name: auditing-access-control
description: Audit access control implementations for security vulnerabilities and misconfigurations. Use when reviewing authentication and authorization. Trigger with 'audit access control', 'check permissions', or 'validate authorization'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Access Control Auditor

This skill provides automated assistance for access control auditor tasks.

## Overview

This skill leverages the access-control-auditor plugin to perform comprehensive audits of access control configurations. It helps identify potential security risks associated with overly permissive access, misconfigured permissions, and non-compliance with security policies.

## How It Works

1. **Analyze Request**: Claude identifies the user's intent to audit access control.
2. **Invoke Plugin**: The access-control-auditor plugin is activated.
3. **Execute Audit**: The plugin analyzes the specified access control configuration (e.g., IAM policies, ACLs).
4. **Report Findings**: The plugin generates a report highlighting potential vulnerabilities and misconfigurations.

## When to Use This Skill

This skill activates when you need to:
- Audit IAM policies in a cloud environment.
- Review access control lists (ACLs) for network resources.
- Assess user permissions in an application.
- Identify potential privilege escalation paths.
- Ensure compliance with access control security policies.

## Examples

### Example 1: Auditing AWS IAM Policies

User request: "Audit the AWS IAM policies in my account for overly permissive access."

The skill will:
1. Invoke the access-control-auditor plugin, specifying the AWS account and IAM policies as the target.
2. Generate a report identifying IAM policies that grant overly broad permissions or violate security best practices.

### Example 2: Reviewing Network ACLs

User request: "Review the network ACLs for my VPC to identify any potential security vulnerabilities."

The skill will:
1. Activate the access-control-auditor plugin, specifying the VPC and network ACLs as the target.
2. Produce a report highlighting ACL rules that allow unauthorized access or expose the VPC to unnecessary risks.

## Best Practices

- **Scope Definition**: Clearly define the scope of the audit (e.g., specific IAM roles, network segments, applications).
- **Contextual Information**: Provide contextual information about the environment being audited (e.g., security policies, compliance requirements).
- **Remediation Guidance**: Use the audit findings to develop and implement remediation strategies to address identified vulnerabilities.

## Integration

This skill can be integrated with other security plugins to provide a more comprehensive security assessment. For example, it can be combined with a vulnerability scanner to identify vulnerabilities that could be exploited due to access control misconfigurations. It can also be integrated with compliance tools to ensure adherence to regulatory requirements.

## Prerequisites

- Access to codebase and configuration files in {baseDir}/
- Security scanning tools installed as needed
- Understanding of security standards and best practices
- Permissions for security analysis operations

## Instructions

1. Identify security scan scope and targets
2. Configure scanning parameters and thresholds
3. Execute security analysis systematically
4. Analyze findings for vulnerabilities and compliance gaps
5. Prioritize issues by severity and impact
6. Generate detailed security report with remediation steps

## Output

- Security scan results with vulnerability details
- Compliance status reports by standard
- Prioritized list of security issues by severity
- Remediation recommendations with code examples
- Executive summary for stakeholders

## Error Handling

If security scanning fails:
- Verify tool installation and configuration
- Check file and directory permissions
- Validate scan target paths
- Review tool-specific error messages
- Ensure network access for dependency checks

## Resources

- Security standard documentation (OWASP, CWE, CVE)
- Compliance framework guidelines (GDPR, HIPAA, PCI-DSS)
- Security scanning tool documentation
- Vulnerability remediation best practices
