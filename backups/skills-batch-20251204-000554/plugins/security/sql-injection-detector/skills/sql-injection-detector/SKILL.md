---
name: detecting-sql-injection-vulnerabilities
description: |
  This skill enables Claude to detect SQL injection vulnerabilities in code. It uses the sql-injection-detector plugin to analyze codebases, identify potential SQL injection flaws, and provide remediation guidance. Use this skill when the user asks to find SQL injection vulnerabilities, scan for SQL injection, or check code for SQL injection risks. The skill is triggered by phrases like "detect SQL injection", "scan for SQLi", or "check for SQL injection vulnerabilities".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to proactively identify and address SQL injection vulnerabilities within a codebase. By leveraging the sql-injection-detector plugin, Claude can perform comprehensive scans, pinpoint potential security flaws, and offer actionable recommendations to mitigate risks. This ensures more secure and robust applications.

## How It Works

1. **Initiate Scan**: Upon receiving a relevant request, Claude activates the sql-injection-detector plugin.
2. **Code Analysis**: The plugin analyzes the codebase, examining code patterns, input vectors, and query contexts.
3. **Vulnerability Identification**: The plugin identifies potential SQL injection vulnerabilities, categorizing them by severity.
4. **Report Generation**: A detailed report is generated, outlining the identified vulnerabilities, their locations, and recommended remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Audit a codebase for SQL injection vulnerabilities.
- Secure a web application against SQL injection attacks.
- Review code changes for potential SQL injection risks.
- Understand how SQL injection vulnerabilities occur and how to prevent them.

## Examples

### Example 1: Securing a Web Application

User request: "Scan my web application for SQL injection vulnerabilities."

The skill will:
1. Activate the sql-injection-detector plugin.
2. Scan the web application's codebase for potential SQL injection flaws.
3. Generate a report detailing any identified vulnerabilities, their severity, and remediation recommendations.

### Example 2: Reviewing Code Changes

User request: "Check these code changes for potential SQL injection risks."

The skill will:
1. Activate the sql-injection-detector plugin.
2. Analyze the provided code changes for potential SQL injection vulnerabilities.
3. Provide feedback on the security implications of the changes and suggest improvements.

## Best Practices

- **Input Validation**: Always validate and sanitize user inputs to prevent malicious data from entering the system.
- **Parameterized Queries**: Utilize parameterized queries or prepared statements to prevent SQL injection attacks.
- **Least Privilege**: Grant database users only the necessary privileges to minimize the impact of a potential SQL injection attack.

## Integration

This skill integrates seamlessly with other code analysis and security plugins within the Claude Code ecosystem. It can be used in conjunction with static analysis tools, dynamic testing frameworks, and vulnerability management systems to provide a comprehensive security solution.