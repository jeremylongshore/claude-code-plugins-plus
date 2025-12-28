---
name: validating-authentication-implementations
description: Validate authentication mechanisms for security weaknesses and compliance. Use when reviewing login systems or auth flows. Trigger with 'validate authentication', 'check auth security', or 'review login'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Authentication Validator

This skill provides automated assistance for authentication validator tasks.

## Overview

This skill allows Claude to assess the security of authentication mechanisms in a system or application. It provides a detailed report highlighting potential vulnerabilities and offering recommendations for improvement based on established security principles.

## How It Works

1. **Initiate Validation**: Upon receiving a trigger phrase, the skill activates the `authentication-validator` plugin.
2. **Analyze Authentication Methods**: The plugin examines the implemented authentication methods, such as JWT, OAuth, session-based, or API keys.
3. **Generate Security Report**: The plugin generates a comprehensive report outlining potential vulnerabilities and recommended fixes related to password security, session management, token security (JWT), multi-factor authentication, and account security.

## When to Use This Skill

This skill activates when you need to:
- Assess the security of an application's authentication implementation.
- Identify vulnerabilities in password policies and session management.
- Evaluate the security of JWT tokens and MFA implementation.
- Ensure compliance with security best practices and industry standards.

## Examples

### Example 1: Assessing JWT Security

User request: "validate authentication for jwt implementation"

The skill will:
1. Activate the `authentication-validator` plugin.
2. Analyze the JWT implementation, checking for strong signing algorithms, proper expiration claims, and audience/issuer validation.
3. Generate a report highlighting any vulnerabilities and recommending best practices for JWT security.

### Example 2: Checking Session Security

User request: "authcheck session cookies"

The skill will:
1. Activate the `authentication-validator` plugin.
2. Analyze the session cookie settings, including HttpOnly, Secure, and SameSite attributes.
3. Generate a report outlining any potential session fixation or CSRF vulnerabilities and recommending appropriate countermeasures.

## Best Practices

- **Password Hashing**: Always use strong hashing algorithms like bcrypt or Argon2 with appropriate salt generation.
- **Token Expiration**: Implement short-lived access tokens and refresh token rotation for enhanced security.
- **Multi-Factor Authentication**: Encourage or enforce MFA to mitigate the risk of password compromise.

## Integration

This skill can be used in conjunction with other security-related plugins to provide a comprehensive security assessment of an application. For example, it can be used alongside a code analysis plugin to identify potential code-level vulnerabilities related to authentication.

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
