---
name: validating-csrf-protection
description: Validate CSRF protection implementations for security gaps. Use when reviewing form security or state-changing operations. Trigger with 'validate CSRF', 'check CSRF protection', or 'review token security'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Csrf Protection Validator

This skill provides automated assistance for csrf protection validator tasks.

## Overview

This skill empowers Claude to analyze web applications for CSRF vulnerabilities. It assesses the effectiveness of implemented CSRF protection mechanisms, providing insights into potential weaknesses and recommendations for remediation.

## How It Works

1. **Analyze Endpoints**: The plugin examines application endpoints to identify those lacking CSRF protection.
2. **Assess Protection Mechanisms**: It validates the implementation of CSRF protection mechanisms, including token validation, double-submit cookies, SameSite attributes, and origin validation.
3. **Generate Report**: A detailed report is generated, highlighting vulnerable endpoints, potential attack scenarios, and recommended fixes.

## When to Use This Skill

This skill activates when you need to:
- Validate existing CSRF protection measures.
- Identify CSRF vulnerabilities in a web application.
- Assess the risk associated with unprotected endpoints.
- Generate a report outlining CSRF vulnerabilities and recommended fixes.

## Examples

### Example 1: Identifying Unprotected API Endpoints

User request: "validate csrf"

The skill will:
1. Analyze the application's API endpoints.
2. Identify endpoints lacking CSRF protection, such as those handling sensitive data modifications.
3. Generate a report outlining vulnerable endpoints and potential attack vectors.

### Example 2: Checking SameSite Cookie Attributes

User request: "Check for csrf vulnerabilities in my application"

The skill will:
1. Analyze the application's cookie settings.
2. Verify that SameSite attributes are properly configured to mitigate CSRF attacks.
3. Report any cookies lacking the SameSite attribute or using an insecure setting.

## Best Practices

- **Regular Validation**: Regularly validate CSRF protection mechanisms as part of the development lifecycle.
- **Comprehensive Coverage**: Ensure all state-changing operations are protected against CSRF attacks.
- **Secure Configuration**: Use secure configurations for CSRF protection mechanisms, such as strong token generation and proper SameSite attribute settings.

## Integration

This skill can be used in conjunction with other security plugins to provide a comprehensive security assessment of web applications. For example, it can be combined with a vulnerability scanner to identify other potential vulnerabilities in addition to CSRF weaknesses.

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
