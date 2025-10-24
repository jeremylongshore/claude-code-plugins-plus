---
name: generating-security-audit-reports
description: |
  This skill enables Claude to generate comprehensive security audit reports. It is designed to provide insights into an application or system's security posture, compliance status, and recommended remediation steps. Use this skill when the user requests a "security audit report", wants to "audit security", or needs a "vulnerability assessment report". The skill analyzes security data and produces a detailed report in various formats. It is best used to identify vulnerabilities, track compliance, and create remediation roadmaps. The skill can be activated via the command `/audit-report` or its shortcut `/auditreport`.
---

## Overview

This skill allows Claude to create detailed security audit reports. It analyzes existing security data, identifies vulnerabilities, assesses compliance with industry standards, and suggests remediation steps. The generated reports can be used to improve an organization's security posture and meet compliance requirements.

## How It Works

1. **Data Collection**: Claude gathers data from various security tools and sources.
2. **Analysis**: The plugin analyzes the collected data to identify vulnerabilities and compliance issues.
3. **Report Generation**: Claude compiles the findings into a comprehensive security audit report, including an executive summary, vulnerability details, compliance status, and remediation recommendations.

## When to Use This Skill

This skill activates when you need to:
- Generate a comprehensive security audit report.
- Assess the security posture of an application or system.
- Identify vulnerabilities and compliance issues.

## Examples

### Example 1: Security Posture Assessment

User request: "Create a security audit report for our web application."

The skill will:
1. Analyze the web application's security data.
2. Generate a report outlining vulnerabilities, compliance status, and remediation recommendations.

### Example 2: Compliance Audit

User request: "/auditreport for PCI-DSS compliance"

The skill will:
1. Analyze the current system configurations and security measures.
2. Generate a report focused on PCI-DSS compliance, highlighting areas of non-compliance and recommended actions.

## Best Practices

- **Clarity**: Provide specific details about the system or application you want to audit.
- **Context**: Mention any relevant compliance standards (e.g., PCI-DSS, GDPR, HIPAA) to focus the audit.
- **Review**: Always review the generated report for accuracy and completeness.

## Integration

This skill can be integrated with other security tools and plugins to enhance data collection and analysis. It provides a central point for generating security audit reports from various sources.