---
name: Validating CSRF Protection
description: |
  This skill helps to identify Cross-Site Request Forgery (CSRF) vulnerabilities in web applications. It validates the implementation of CSRF protection mechanisms, such as synchronizer tokens, double-submit cookies, SameSite attributes, and origin validation. Use this skill when you need to analyze your application's security posture against CSRF attacks or when asked to "validate csrf", "check for csrf vulnerabilities", or "test csrf protection".
---

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