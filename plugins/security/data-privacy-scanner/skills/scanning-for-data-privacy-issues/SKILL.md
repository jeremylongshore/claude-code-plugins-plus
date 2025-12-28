---
name: scanning-for-data-privacy-issues
description: Scan for data privacy issues and sensitive information exposure. Use when reviewing data handling practices. Trigger with 'scan privacy issues', 'check sensitive data', or 'validate data protection'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Data Privacy Scanner

This skill provides automated assistance for data privacy scanner tasks.

## Overview

This skill automates the process of identifying data privacy risks within a codebase. By leveraging the data-privacy-scanner plugin, Claude can quickly pinpoint potential vulnerabilities, helping developers proactively address compliance requirements and protect sensitive user data.

## How It Works

1. **Initiate Scan**: Upon detecting a privacy-related trigger phrase, Claude activates the data-privacy-scanner plugin.
2. **Analyze Codebase**: The plugin analyzes the specified files or the entire project for potential data privacy violations.
3. **Report Findings**: The plugin generates a detailed report outlining identified risks, including the location of the vulnerability and a description of the potential impact.

## When to Use This Skill

This skill activates when you need to:
- Identify potential data privacy vulnerabilities in a codebase.
- Ensure compliance with data privacy regulations such as GDPR, CCPA, or HIPAA.
- Perform a privacy audit of a project involving sensitive user data.

## Examples

### Example 1: Identifying PII Leaks

User request: "Scan this project for PII leaks."

The skill will:
1. Activate the data-privacy-scanner plugin to analyze the project.
2. Generate a report highlighting potential Personally Identifiable Information (PII) leaks, such as exposed email addresses or phone numbers.

### Example 2: Checking GDPR Compliance

User request: "Check this configuration file for GDPR compliance issues."

The skill will:
1. Activate the data-privacy-scanner plugin to analyze the specified configuration file.
2. Generate a report identifying potential GDPR violations, such as insufficient data anonymization or improper consent management.

## Best Practices

- **Scope**: Specify the relevant files or directories to narrow the scope of the scan and improve performance.
- **Context**: Provide context about the type of data being processed to help the plugin identify relevant privacy risks.
- **Review**: Carefully review the generated report to understand the identified vulnerabilities and implement appropriate remediation measures.

## Integration

This skill can be integrated with other security and compliance tools to provide a comprehensive approach to data privacy. For example, it can be combined with vulnerability scanning tools to identify related security risks or with reporting tools to track progress on remediation efforts.

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
