---
name: validating-pci-dss-compliance
description: Validate PCI-DSS compliance for payment card data security. Use when auditing payment systems. Trigger with 'validate PCI-DSS', 'check payment security', or 'audit card data'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Pci Dss Validator

This skill provides automated assistance for pci dss validator tasks.

## Overview

This skill streamlines PCI DSS compliance checks by automatically analyzing code and configurations. It flags potential issues, allowing for proactive remediation and improved security posture. It is particularly useful for developers, security engineers, and compliance officers.

## How It Works

1. **Analyze the Target**: The skill identifies the codebase, configuration files, or infrastructure resources to be evaluated.
2. **Run PCI DSS Validation**: The pci-dss-validator plugin scans the target for potential PCI DSS violations.
3. **Generate Report**: The skill compiles a report detailing any identified vulnerabilities or non-compliant configurations, along with remediation recommendations.

## When to Use This Skill

This skill activates when you need to:
- Evaluate a new application or system for PCI DSS compliance before deployment.
- Periodically assess existing systems to maintain PCI DSS compliance.
- Investigate potential security vulnerabilities related to PCI DSS.

## Examples

### Example 1: Validating a Web Application

User request: "Validate PCI compliance for my e-commerce web application."

The skill will:
1. Identify the source code repository for the web application.
2. Run the pci-dss-validator plugin against the codebase.
3. Generate a report highlighting any PCI DSS violations found in the code.

### Example 2: Checking Infrastructure Configuration

User request: "Check PCI DSS compliance of my AWS infrastructure."

The skill will:
1. Access the AWS configuration files (e.g., Terraform, CloudFormation).
2. Execute the pci-dss-validator plugin against the infrastructure configuration.
3. Produce a report outlining any non-compliant configurations in the AWS environment.

## Best Practices

- **Scope Definition**: Clearly define the scope of the PCI DSS assessment to ensure accurate and relevant results.
- **Regular Assessments**: Conduct regular PCI DSS assessments to maintain continuous compliance.
- **Remediation Tracking**: Track and document all remediation efforts to demonstrate ongoing commitment to security.

## Integration

This skill can be integrated with other security tools and plugins to provide a comprehensive security assessment. For example, it can be used in conjunction with static analysis tools to identify vulnerabilities in code before it is deployed. It can also be integrated with infrastructure-as-code tools to ensure that infrastructure is compliant with PCI DSS from the start.

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
