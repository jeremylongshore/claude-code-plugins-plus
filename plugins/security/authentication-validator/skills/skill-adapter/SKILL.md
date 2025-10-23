---
name: validating-authentication-implementations
description: |
  This skill enables Claude to validate authentication implementations against security best practices and industry standards. It analyzes various authentication methods, including JWT, OAuth, session-based authentication, and API keys. Use this skill when you need to perform an authentication security check, assess password policies, evaluate MFA implementation, or analyze session security. Trigger this skill with phrases like "validate authentication," "authentication check," or "authcheck."
---

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