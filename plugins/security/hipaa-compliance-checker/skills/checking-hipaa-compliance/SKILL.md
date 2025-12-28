---
name: checking-hipaa-compliance
description: Check HIPAA compliance for healthcare data security requirements. Use when auditing healthcare applications. Trigger with 'check HIPAA compliance', 'validate health data security', or 'audit PHI protection'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Hipaa Compliance Checker

This skill provides automated assistance for hipaa compliance checker tasks.

## Overview

This skill automates the process of identifying potential HIPAA compliance issues within a software project. By using the hipaa-compliance-checker plugin, it helps developers and security professionals proactively address vulnerabilities and ensure adherence to HIPAA guidelines.

## How It Works

1. **Analyze Request**: Claude identifies the user's intent to check for HIPAA compliance.
2. **Initiate Plugin**: Claude activates the hipaa-compliance-checker plugin.
3. **Execute Checks**: The plugin scans the specified codebase, configuration files, or documentation for potential HIPAA violations.
4. **Generate Report**: The plugin generates a detailed report outlining identified issues and their potential impact on HIPAA compliance.

## When to Use This Skill

This skill activates when you need to:
- Evaluate a codebase for HIPAA compliance before deployment.
- Identify potential HIPAA violations in existing systems.
- Assess the HIPAA readiness of infrastructure configurations.
- Verify that documentation adheres to HIPAA guidelines.

## Examples

### Example 1: Checking a codebase for HIPAA compliance

User request: "Check HIPAA compliance of the patient data API codebase."

The skill will:
1. Activate the hipaa-compliance-checker plugin.
2. Scan the specified API codebase for potential HIPAA violations.
3. Generate a report listing any identified issues, such as insecure data storage or insufficient access controls.

### Example 2: Assessing infrastructure configuration for HIPAA readiness

User request: "Assess the HIPAA readiness of our AWS infrastructure configuration."

The skill will:
1. Activate the hipaa-compliance-checker plugin.
2. Analyze the AWS infrastructure configuration files for potential HIPAA violations, such as misconfigured security groups or inadequate encryption.
3. Generate a report outlining any identified issues and recommendations for remediation.

## Best Practices

- **Specify Target**: Always clearly specify the target (e.g., codebase, configuration file, documentation) for the HIPAA compliance check.
- **Review Reports**: Carefully review the generated reports to understand the identified issues and their potential impact.
- **Prioritize Remediation**: Prioritize the remediation of identified issues based on their severity and potential impact on HIPAA compliance.

## Integration

This skill can be integrated with other security and compliance tools to provide a comprehensive view of a system's security posture. The generated reports can be used as input for vulnerability management systems and security information and event management (SIEM) platforms.

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
