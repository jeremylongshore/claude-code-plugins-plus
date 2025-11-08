---
name: scanning-for-vulnerabilities
description: |
  This skill enables comprehensive vulnerability scanning using the vulnerability-scanner plugin. It identifies security vulnerabilities in code, dependencies, and configurations, including CVE detection. Use this skill when the user asks to scan for vulnerabilities, security issues, or CVEs in their project. Trigger phrases include "scan for vulnerabilities", "find security issues", "check for CVEs", "/scan", or "/vuln". The plugin performs static analysis, dependency checking, and configuration analysis to provide a detailed vulnerability report.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to automatically scan your codebase for security vulnerabilities. It leverages the vulnerability-scanner plugin to identify potential risks, including code-level flaws, vulnerable dependencies, and insecure configurations.

## How It Works

1. **Initiate Scan**: The skill activates the vulnerability-scanner plugin based on user input.
2. **Perform Analysis**: The plugin scans the codebase, dependencies, and configurations for vulnerabilities, including CVE detection.
3. **Generate Report**: The plugin creates a detailed vulnerability report with findings, severity levels, and remediation guidance.

## When to Use This Skill

This skill activates when you need to:
- Identify security vulnerabilities in your code.
- Check your project's dependencies for known CVEs.
- Review your project's configurations for security weaknesses.

## Examples

### Example 1: Identifying SQL Injection Risks

User request: "Scan my code for SQL injection vulnerabilities."

The skill will:
1. Activate the vulnerability-scanner plugin.
2. Analyze the codebase for potential SQL injection flaws.
3. Generate a report highlighting any identified SQL injection risks and providing remediation steps.

### Example 2: Checking for Vulnerable npm Packages

User request: "Check my project's npm dependencies for known vulnerabilities."

The skill will:
1. Activate the vulnerability-scanner plugin.
2. Scan the project's `package.json` file and identify any npm packages with known CVEs.
3. Generate a report listing the vulnerable packages, their CVE identifiers, and recommended updates.

## Best Practices

- **Regular Scanning**: Run vulnerability scans regularly, especially before deployments.
- **Prioritize Remediation**: Focus on addressing critical and high-severity vulnerabilities first.
- **Validate Fixes**: After applying fixes, run another scan to ensure the vulnerabilities are resolved.

## Integration

This skill integrates with the core Claude Code environment by providing automated vulnerability scanning capabilities. It can be used in conjunction with other plugins to create a comprehensive security workflow, such as integrating with a ticketing system to automatically create tickets for identified vulnerabilities.