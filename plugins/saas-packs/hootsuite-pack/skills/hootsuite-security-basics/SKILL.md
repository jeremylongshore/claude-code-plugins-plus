---
name: hootsuite-security-basics
description: |
  Apply Hootsuite security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Hootsuite security configuration.
  Trigger with phrases like "hootsuite security", "hootsuite secrets",
  "secure hootsuite", "hootsuite API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Security Basics

## Credential Inventory

| Credential | Scope | Rotation |
|-----------|-------|----------|
| Client ID | App-level | Never (app identifier) |
| Client Secret | App-level | Rotate if compromised |
| Access Token | User session | Auto-expires (~1 hour) |
| Refresh Token | User session | Rotate on each refresh |

## Instructions

### Step 1: Secure Token Storage

```bash
# .env (never commit)
HOOTSUITE_CLIENT_ID=app_client_id
HOOTSUITE_CLIENT_SECRET=app_secret
HOOTSUITE_ACCESS_TOKEN=current_token
HOOTSUITE_REFRESH_TOKEN=refresh_token
```

### Step 2: Token Refresh Security

```typescript
// Always use HTTPS for token exchange
// Store refresh tokens encrypted at rest
// Rotate refresh tokens on each use (Hootsuite returns new ones)
async function secureRefresh(refreshToken: string) {
  const res = await fetch('https://platform.hootsuite.com/oauth2/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': `Basic ${Buffer.from(`${process.env.HOOTSUITE_CLIENT_ID}:${process.env.HOOTSUITE_CLIENT_SECRET}`).toString('base64')}`,
    },
    body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: refreshToken }),
  });
  const tokens = await res.json();
  // Store new refresh_token, discard old one
  return tokens;
}
```

### Step 3: Security Checklist

- [ ] Client secret in secrets vault, never in code
- [ ] Access tokens never logged or exposed
- [ ] Refresh tokens stored encrypted
- [ ] HTTPS for all OAuth requests
- [ ] Pre-commit hook blocks `HOOTSUITE_` credential leaks
- [ ] Separate OAuth apps for dev/staging/prod

## Resources

- [Hootsuite OAuth 2.0](https://developer.hootsuite.com/docs/using-rest-apis)

## Next Steps

For production, see `hootsuite-prod-checklist`.
