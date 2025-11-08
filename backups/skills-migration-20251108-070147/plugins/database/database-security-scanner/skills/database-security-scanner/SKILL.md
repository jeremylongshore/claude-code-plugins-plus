---
name: scanning-database-security
description: |
  This skill enables Claude to perform comprehensive database security scans using the database-security-scanner plugin. It is triggered when the user requests a security assessment of a database, including identifying vulnerabilities like weak passwords, SQL injection risks, and insecure configurations. The skill leverages OWASP guidelines to ensure thorough coverage and provides remediation suggestions. Use this skill when the user asks to "scan database security", "check database for vulnerabilities", "perform OWASP compliance check on database", or "assess database security posture". The plugin supports PostgreSQL and MySQL.
---

## Overview

This skill empowers Claude to automatically assess the security of databases by utilizing the database-security-scanner plugin. It identifies vulnerabilities, provides OWASP compliance reports, and suggests remediation steps to improve the database's security posture.

## How It Works

1. **Initiate Scan**: The user's request triggers the database-security-scanner plugin.
2. **Vulnerability Assessment**: The plugin scans the specified database for common vulnerabilities, including weak passwords, SQL injection risks, and insecure configurations.
3. **Report Generation**: The plugin generates a detailed report outlining identified vulnerabilities and OWASP compliance status.
4. **Remediation Suggestions**: The plugin provides actionable recommendations and, where possible, automated remediation scripts to address identified vulnerabilities.

## When to Use This Skill

This skill activates when you need to:
- Assess the security posture of a database.
- Identify potential vulnerabilities in a database configuration.
- Ensure a database complies with OWASP security guidelines.

## Examples

### Example 1: Assessing PostgreSQL Security

User request: "Scan the PostgreSQL database for security vulnerabilities and generate a report."

The skill will:
1. Activate the database-security-scanner plugin.
2. Scan the PostgreSQL database for vulnerabilities.
3. Generate a report detailing the findings and remediation recommendations.

### Example 2: Checking MySQL for OWASP Compliance

User request: "Perform an OWASP compliance check on the MySQL database."

The skill will:
1. Activate the database-security-scanner plugin.
2. Scan the MySQL database for OWASP compliance.
3. Generate a report outlining any compliance violations and suggested fixes.

## Best Practices

- **Database Access**: Ensure Claude has the necessary credentials and permissions to access the database being scanned.
- **Regular Scans**: Schedule regular security scans to continuously monitor the database for new vulnerabilities.
- **Remediation**: Implement the suggested remediation steps to address identified vulnerabilities promptly.

## Integration

This skill can be used in conjunction with other database management and security plugins to create a comprehensive database security workflow. For instance, it can be integrated with a plugin that automatically applies security patches based on the scanner's recommendations.