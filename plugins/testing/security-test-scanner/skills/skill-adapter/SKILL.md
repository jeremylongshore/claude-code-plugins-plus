---
name: Performing Security Testing
description: |
  This skill automates security vulnerability testing. It is triggered when the user requests security assessments, penetration tests, or vulnerability scans. The skill covers OWASP Top 10 vulnerabilities, SQL injection, XSS, CSRF, authentication issues, and authorization flaws. Use this skill when the user mentions "security test", "vulnerability scan", "OWASP", "SQL injection", "XSS", "CSRF", "authentication", or "authorization" in the context of application or API testing.
---

## Overview

This skill enables Claude to automatically perform security vulnerability testing on applications and APIs. It leverages the security-test-scanner plugin to identify potential weaknesses and generate comprehensive reports.

## How It Works

1. **Initiate Scan**: The plugin is activated when security testing is requested.
2. **Execute Tests**: The plugin automatically runs a suite of security tests covering OWASP Top 10, injection flaws, XSS, CSRF, and authentication/authorization issues.
3. **Generate Report**: The plugin compiles the test results into a detailed report, highlighting vulnerabilities, severity ratings, and remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Perform a security vulnerability scan of an application.
- Test for OWASP Top 10 vulnerabilities.
- Identify SQL injection or XSS vulnerabilities.
- Assess authentication and authorization security.

## Examples

### Example 1: OWASP Top 10 Vulnerability Scan

User request: "Perform a security test focusing on OWASP Top 10 vulnerabilities for the /api/ endpoint."

The skill will:
1. Activate the security-test-scanner plugin.
2. Execute OWASP Top 10 tests against the specified endpoint.
3. Generate a report detailing any identified vulnerabilities and their severity.

### Example 2: SQL Injection Testing

User request: "Test the API for SQL injection vulnerabilities."

The skill will:
1. Activate the security-test-scanner plugin.
2. Run SQL injection tests against the API.
3. Report any successful injection attempts.

## Best Practices

- **Scope Definition**: Clearly define the scope of the security test (e.g., specific endpoints, modules).
- **Authentication**: Provide necessary authentication credentials for testing protected resources.
- **Regular Testing**: Schedule regular security tests to identify newly introduced vulnerabilities.

## Integration

This skill can be integrated with other plugins to automatically trigger security tests as part of a CI/CD pipeline or after code changes. It also integrates with reporting tools for centralized vulnerability management.