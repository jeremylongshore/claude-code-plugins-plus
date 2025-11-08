# Authentication Validator Plugin

Validate authentication implementation against security best practices and industry standards.

## Features

- **Multi-Auth Support** - JWT, OAuth, session-based, API keys
- **Password Policy Validation** - Strength, hashing, storage
- **MFA Detection** - Multi-factor authentication checks
- **Session Security** - Cookie settings, timeout, fixation
- **Token Analysis** - JWT claims, expiration, signing

## Installation

```bash
/plugin install authentication-validator@claude-code-plugins-plus
```

## Usage

```bash
/validate-auth
# Or shortcut
/authcheck
```

## Validation Areas

### 1. Password Security
- Minimum length (12+ characters)
- Complexity requirements
- Bcrypt/Argon2 hashing
- Salt generation
- Password history
- Lockout policies

### 2. Session Management
- Secure cookie flags
- HttpOnly and Secure flags
- SameSite attribute
- Session timeout
- Session fixation prevention
- CSRF protection

### 3. Token Security (JWT)
- Strong signing algorithm (RS256, ES256)
- Proper expiration (exp claim)
- Audience validation (aud claim)
- Issuer validation (iss claim)
- Token rotation
- Refresh token security

### 4. Multi-Factor Authentication
- MFA availability
- TOTP/SMS/Email options
- Backup codes
- Recovery mechanisms

### 5. Account Security
- Account lockout after failed attempts
- Rate limiting
- Brute force protection
- Password reset security
- Email verification

## Example Report

```
AUTHENTICATION SECURITY ANALYSIS
=================================
Application: Example App
Auth Method: JWT + Session
Grade: B (Good, needs improvement)

FINDINGS
--------

 CRITICAL: Weak Password Hashing
  Current: MD5
  Risk: Passwords easily crackable
  Fix: Use bcrypt with cost factor 10+

  const bcrypt = require('bcrypt');
  const hash = await bcrypt.hash(password, 10);

 HIGH: Missing MFA
  Risk: Single factor authentication only
  Recommendation: Implement TOTP-based MFA

 MEDIUM: Short JWT Expiration
  Current: exp not set
  Risk: Tokens never expire
  Fix: Set reasonable expiration

  const token = jwt.sign(payload, secret, {
      expiresIn: '15m'
  });

 Password Policy: GOOD
  - Minimum 12 characters
  - Requires uppercase, lowercase, number, symbol

 Session Cookies: GOOD
  - HttpOnly: true
  - Secure: true
  - SameSite: strict
```

## Best Practices

1. **Password Hashing**: Use bcrypt, Argon2, or PBKDF2
2. **Token Expiration**: Short-lived access tokens (15-30 min)
3. **Refresh Tokens**: Rotate on use, revocable
4. **MFA**: Optional but strongly recommended
5. **Rate Limiting**: Prevent brute force attacks

## License

MIT License - See LICENSE file for details
