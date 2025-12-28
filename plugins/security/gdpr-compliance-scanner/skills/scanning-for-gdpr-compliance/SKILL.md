---
name: scanning-for-gdpr-compliance
description: Scan for GDPR compliance issues in data handling and privacy practices. Use when ensuring EU data protection compliance. Trigger with 'scan GDPR compliance', 'check data privacy', or 'validate GDPR'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Gdpr Compliance Scanner

This skill provides automated assistance for gdpr compliance scanner tasks.

## Overview

This skill allows Claude to automatically assess an application's GDPR compliance posture. It provides a comprehensive scan, identifying potential violations and offering actionable recommendations to improve compliance. The skill simplifies the complex process of GDPR auditing, making it easier to identify and address critical gaps.

## How It Works

1. **Initiate Scan**: The user requests a GDPR compliance scan using natural language.
2. **Plugin Activation**: Claude activates the `gdpr-compliance-scanner` plugin.
3. **Compliance Assessment**: The plugin scans the application or system based on GDPR requirements.
4. **Report Generation**: A detailed report is generated, highlighting compliance scores, critical gaps, and recommended actions.

## When to Use This Skill

This skill activates when you need to:
- Assess an application's GDPR compliance.
- Identify potential GDPR violations.
- Generate a report outlining compliance gaps and recommendations.
- Audit data processing activities for adherence to GDPR principles.

## Examples

### Example 1: Assess GDPR Compliance of a Web Application

User request: "Scan my web application for GDPR compliance."

The skill will:
1. Activate the `gdpr-compliance-scanner` plugin.
2. Scan the web application for GDPR compliance issues related to data collection, storage, and processing.
3. Generate a report highlighting compliance scores, critical gaps such as missing cookie consent mechanisms, and actionable recommendations like implementing a cookie consent banner.

### Example 2: Audit Data Processing Activities

User request: "Check our data processing activities for GDPR compliance."

The skill will:
1. Activate the `gdpr-compliance-scanner` plugin.
2. Analyze data processing activities, including data collection methods, storage practices, and security measures.
3. Generate a report identifying potential violations, such as inadequate data encryption or missing data processing agreements, along with recommendations for remediation.

## Best Practices

- **Specificity**: Provide as much context as possible about the application or system being scanned to improve the accuracy of the assessment.
- **Regularity**: Schedule regular GDPR compliance scans to ensure ongoing adherence to regulatory requirements.
- **Actionable Insights**: Prioritize addressing the critical gaps identified in the report to mitigate potential risks.

## Integration

This skill can be integrated with other security and compliance tools to provide a holistic view of an application's security posture. It can also be used in conjunction with code generation tools to automatically implement recommended changes and improve GDPR compliance.

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
