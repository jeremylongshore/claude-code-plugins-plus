---
name: Checking OWASP Compliance
description: |
  This skill uses the owasp-compliance-checker plugin to automatically identify potential security vulnerabilities based on the OWASP Top 10 (2021) list. It helps ensure your application adheres to industry-standard security practices by providing a detailed analysis of compliance gaps and offering remediation guidance. Use this skill when you need to audit your code for OWASP compliance, identify and fix vulnerabilities, or generate a compliance report. Trigger this skill by asking to "check OWASP compliance", "scan for OWASP vulnerabilities", or using the `/owasp` shortcut.
---

## Overview

This skill empowers Claude to assess your project's adherence to the OWASP Top 10 (2021) security guidelines. It automates the process of identifying potential vulnerabilities related to common web application security risks, providing actionable insights to improve your application's security posture.

## How It Works

1. **Initiate Scan**: The skill activates the owasp-compliance-checker plugin upon request.
2. **Analyze Codebase**: The plugin scans the codebase for potential vulnerabilities related to each OWASP Top 10 category.
3. **Generate Report**: A detailed report is generated, highlighting compliance gaps and providing specific remediation guidance for each identified issue.

## When to Use This Skill

This skill activates when you need to:
- Evaluate your application's security posture against the OWASP Top 10 (2021).
- Identify potential vulnerabilities related to common web application security risks.
- Obtain actionable remediation guidance to address identified vulnerabilities.
- Generate a compliance report for auditing or reporting purposes.

## Examples

### Example 1: Identifying SQL Injection Vulnerabilities

User request: "Check OWASP compliance for SQL injection vulnerabilities."

The skill will:
1. Activate the owasp-compliance-checker plugin.
2. Scan the codebase for potential SQL injection vulnerabilities.
3. Generate a report highlighting any identified SQL injection vulnerabilities and providing remediation guidance.

### Example 2: Assessing Overall OWASP Compliance

User request: "/owasp"

The skill will:
1. Activate the owasp-compliance-checker plugin.
2. Scan the entire codebase for vulnerabilities across all OWASP Top 10 categories.
3. Generate a comprehensive report detailing compliance gaps and remediation steps for each category.

## Best Practices

- **Regular Scanning**: Integrate OWASP compliance checks into your development workflow for continuous security monitoring.
- **Prioritize Remediation**: Address identified vulnerabilities based on their severity and potential impact.
- **Stay Updated**: Keep your OWASP compliance checker plugin updated to benefit from the latest vulnerability detection rules and remediation guidance.

## Integration

This skill can be integrated with other plugins to automate vulnerability remediation or generate comprehensive security reports. For example, it can be used in conjunction with a code modification plugin to automatically apply recommended fixes for identified vulnerabilities.