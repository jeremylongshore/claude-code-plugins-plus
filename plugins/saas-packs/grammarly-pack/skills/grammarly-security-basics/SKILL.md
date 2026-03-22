---
name: grammarly-security-basics
description: |
description: |
  
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Security Basics

## Credential Management

| Credential | Scope | Storage |
|-----------|-------|--------|
| Client ID | App-level | Config |
| Client Secret | App-level | Secrets vault |
| Access Token | Session | Memory only |

## Instructions

### Step 1: Environment Security

```bash
# .env (never commit)
GRAMMARLY_CLIENT_ID=your_id
GRAMMARLY_CLIENT_SECRET=your_secret
```

### Step 2: Token Lifecycle

Tokens from client_credentials grant expire. Never persist access tokens to disk. Re-authenticate when needed.

### Step 3: Security Checklist

- [ ] Client secret in secrets vault
- [ ] Access tokens never logged
- [ ] HTTPS for all API calls
- [ ] Pre-commit hook blocks credential leaks

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For production, see `grammarly-prod-checklist`.
