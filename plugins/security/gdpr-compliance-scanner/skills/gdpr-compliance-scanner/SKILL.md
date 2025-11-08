---
name: scanning-for-gdpr-compliance
description: |
  This skill enables Claude to scan applications and data systems for GDPR compliance issues. It identifies potential violations related to data protection, privacy rights, consent management, and other regulatory requirements. Use this skill when the user asks to "scan for GDPR compliance", check "GDPR compliance", or audit for "data privacy". The skill leverages the `gdpr-compliance-scanner` plugin to perform a comprehensive assessment and generate a detailed report.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

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