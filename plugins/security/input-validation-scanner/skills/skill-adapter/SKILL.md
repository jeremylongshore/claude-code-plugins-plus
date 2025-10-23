---
name: scanning-input-validation-practices
description: |
  This skill enables Claude to automatically scan source code for potential input validation vulnerabilities. It identifies areas where user-supplied data is not properly sanitized or validated before being used in operations, which could lead to security exploits like SQL injection, cross-site scripting (XSS), or command injection. Use this skill when the user asks to "scan for input validation issues", "check input sanitization", "find potential XSS vulnerabilities", or similar requests related to securing user input. It is particularly useful during code reviews, security audits, and when hardening applications against common web vulnerabilities. The skill leverages the input-validation-scanner plugin to perform the analysis.
---

## Overview

This skill automates the process of identifying potential input validation flaws within a codebase. By analyzing how user-provided data is handled, it helps developers proactively address security vulnerabilities before they can be exploited. This skill streamlines security audits and improves the overall security posture of applications.

## How It Works

1. **Initiate Scan**: The user requests an input validation scan, triggering the skill.
2. **Code Analysis**: The skill uses the input-validation-scanner plugin to analyze the specified codebase or file.
3. **Vulnerability Identification**: The plugin identifies instances where input validation may be missing or insufficient.
4. **Report Generation**: The skill presents a report highlighting potential vulnerabilities and their locations in the code.

## When to Use This Skill

This skill activates when you need to:
- Audit a codebase for input validation vulnerabilities.
- Review newly written code for potential XSS or SQL injection flaws.
- Harden an application against common web security exploits.
- Ensure compliance with security best practices related to input handling.

## Examples

### Example 1: Identifying XSS Vulnerabilities

User request: "Scan the user profile module for potential XSS vulnerabilities."

The skill will:
1. Activate the input-validation-scanner plugin on the specified module.
2. Generate a report highlighting areas where user input is directly rendered without proper sanitization, indicating potential XSS vulnerabilities.

### Example 2: Checking for SQL Injection Risks

User request: "Check the database access layer for potential SQL injection risks."

The skill will:
1. Use the input-validation-scanner plugin to examine the database access code.
2. Identify instances where user input is used directly in SQL queries without proper parameterization or escaping, indicating potential SQL injection vulnerabilities.

## Best Practices

- **Regular Scanning**: Integrate input validation scanning into your regular development workflow.
- **Contextual Analysis**: Always review the identified vulnerabilities in context to determine their actual impact and severity.
- **Comprehensive Validation**: Ensure that all user-supplied data is validated, including data from forms, APIs, and external sources.

## Integration

This skill can be used in conjunction with other security-related skills to provide a more comprehensive security assessment. For example, it can be combined with a static analysis skill to identify other types of vulnerabilities or with a dependency scanning skill to identify vulnerable third-party libraries.