---
name: evernote-security-basics
description: |
  Implement security best practices for Evernote integrations.
  Use when securing API credentials, implementing OAuth securely,
  or hardening Evernote integrations.
  Trigger with phrases like "evernote security", "secure evernote",
  "evernote credentials", "evernote oauth security".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Security Basics

## Overview
Security best practices for Evernote API integrations, covering credential management, OAuth hardening, token storage, data protection, and secure logging patterns.

## Prerequisites
- Evernote SDK setup
- Understanding of OAuth 1.0a
- Basic cryptography concepts (AES encryption, hashing)

## Instructions

### Step 1: Credential Management

Store `consumerKey`, `consumerSecret`, and access tokens in environment variables or a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault). Never commit credentials to source control. Add `.env` to `.gitignore`.

```javascript
// Load from environment, fail fast if missing
const requiredVars = ['EVERNOTE_CONSUMER_KEY', 'EVERNOTE_CONSUMER_SECRET'];
for (const v of requiredVars) {
  if (!process.env[v]) throw new Error(`Missing required env var: ${v}`);
}
```

### Step 2: Secure OAuth Flow

Add CSRF protection with a state parameter stored in the session. Validate the callback URL matches your registered domain. Use HTTPS-only for all OAuth endpoints. Set secure cookie flags for session tokens.

```javascript
// Generate CSRF token for OAuth state
const csrfToken = crypto.randomBytes(32).toString('hex');
req.session.oauthCsrf = csrfToken;

// Verify on callback
if (req.query.state !== req.session.oauthCsrf) {
  return res.status(403).send('CSRF validation failed');
}
```

### Step 3: Encrypted Token Storage

Encrypt access tokens at rest using AES-256-GCM before storing in your database. Decrypt only when making API calls. Store the encryption key separately from the database.

### Step 4: Input Validation

Sanitize all user input before embedding in ENML. Validate note titles (max 255 chars), tag names (max 100 chars, no commas), and notebook names (max 100 chars). Strip forbidden HTML elements and attributes.

### Step 5: Secure Logging

Redact access tokens, consumer secrets, and user email addresses from log output. Log only the first 8 characters of tokens for debugging correlation.

```javascript
function redactToken(token) {
  if (!token || token.length < 12) return '***';
  return token.slice(0, 8) + '...[REDACTED]';
}
```

### Step 6: Token Lifecycle Management

Track token expiration (`edam_expires`), implement proactive refresh before expiry, and handle `AUTH_EXPIRED` errors gracefully. Tokens default to 1-year validity but users can set shorter durations.

For the complete security implementation including encrypted storage, CSRF-protected OAuth, input validation, and audit logging, see [Implementation Guide](references/implementation-guide.md).

## Output
- Environment-based credential management with validation
- CSRF-protected OAuth 1.0a flow
- AES-256-GCM encrypted token storage
- Input sanitization for ENML content and metadata
- Redacted logging utility
- Token expiration tracking and refresh

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_AUTH` | Token revoked or invalid | Re-authenticate via OAuth; check token not corrupted during encryption |
| `AUTH_EXPIRED` | Token past expiration date | Implement proactive refresh before `edam_expires` |
| `PERMISSION_DENIED` | API key lacks required scope | Request appropriate permissions from Evernote |
| CSRF mismatch | Session expired or attack attempt | Regenerate CSRF token and restart OAuth flow |

## Resources
- [OAuth Documentation](https://dev.evernote.com/doc/articles/authentication.php)
- [API Key Permissions](https://dev.evernote.com/doc/articles/permissions.php)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)
- [Node.js Crypto (AES)](https://nodejs.org/api/crypto.html)

## Next Steps
For production deployment checklist, see `evernote-prod-checklist`.

## Examples

**Secure credential setup**: Store credentials in AWS Secrets Manager, load at startup, validate all required values are present, and fail fast on missing configuration.

**Token rotation**: Monitor `edam_expires` for all stored tokens, send re-authentication emails 30 days before expiry, and gracefully degrade to read-only mode when tokens expire.
