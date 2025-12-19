---
description: This skill enables claude to conduct a security-focused code review using
  the security-agent plugin. it analyzes code for potential vulnerabilities like sql
  injection, xss, authentication flaws, and insecure dependencies. claude uses this
  skill wh...
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash
name: performing-security-code-review
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
version: 1.0.0
---
## Overview

This skill empowers Claude to act as a security expert, identifying and explaining potential vulnerabilities within code. It leverages the security-agent plugin to provide detailed security analysis, helping developers improve the security posture of their applications.

## How It Works

1. **Receiving Request**: Claude identifies a user's request for a security review or audit of code.
2. **Activating Security Agent**: Claude invokes the security-agent plugin to analyze the provided code.
3. **Generating Security Report**: The security-agent produces a structured report detailing identified vulnerabilities, their severity, affected code locations, and recommended remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Review code for security vulnerabilities.
- Perform a security audit of a codebase.
- Identify potential security risks in a software application.

## Examples

### Example 1: Identifying SQL Injection Vulnerability

User request: "Please review this database query code for SQL injection vulnerabilities."

The skill will:
1. Activate the security-agent plugin to analyze the database query code.
2. Generate a report identifying potential SQL injection vulnerabilities, including the vulnerable code snippet, its severity, and suggested remediation, such as using parameterized queries.

### Example 2: Checking for Insecure Dependencies

User request: "Can you check this project's dependencies for known security vulnerabilities?"

The skill will:
1. Utilize the security-agent plugin to scan the project's dependencies against known vulnerability databases.
2. Produce a report listing any vulnerable dependencies, their Common Vulnerabilities and Exposures (CVE) identifiers, and recommendations for updating to secure versions.

## Best Practices

- **Specificity**: Provide the exact code or project you want reviewed.
- **Context**: Clearly state the security concerns you have regarding the code.
- **Iteration**: Use the findings to address vulnerabilities and request further reviews.

## Integration

This skill integrates with Claude's code understanding capabilities and leverages the security-agent plugin to provide specialized security analysis. It can be used in conjunction with other code analysis tools to provide a comprehensive assessment of code quality and security.