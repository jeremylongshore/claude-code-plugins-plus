---
name: clickup-security-basics
description: |
  Secure ClickUp API tokens, implement least-privilege access, and audit usage.
  Use when securing API keys, rotating tokens, configuring per-environment
  credentials, or auditing ClickUp API access patterns.
  Trigger: "clickup security", "clickup secrets", "secure clickup token",
  "clickup API key rotation", "clickup access audit".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Security Basics

## Overview

Secure ClickUp API credentials and access patterns. ClickUp personal tokens never expire, making rotation discipline critical. OAuth tokens also do not expire but can be revoked.

## Token Types and Risk

| Token Type | Prefix | Expires | Scope | Risk Level |
|------------|--------|---------|-------|------------|
| Personal API Token | `pk_` | Never | Full user access | High -- treat like password |
| OAuth Access Token | Varies | Never | Per-authorized workspace | Medium -- per-user |
| OAuth Client Secret | N/A | Never | App-level | Critical -- server-side only |

## Secure Storage

```bash
# .env (NEVER commit)
CLICKUP_API_TOKEN=pk_12345678_ABCDEFGHIJKLMNOPQRSTUVWXYZ

# .gitignore (mandatory)
.env
.env.local
.env.*.local
*.pem
```

```bash
# Git pre-commit hook to catch leaked tokens
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached --diff-filter=ACM | grep -qE "pk_[a-zA-Z0-9_]{30,}"; then
  echo "ERROR: ClickUp API token detected in staged files!"
  echo "Remove the token and use environment variables instead."
  exit 1
fi
```

## Token Rotation Procedure

```bash
# 1. Generate new token: ClickUp > Settings > Apps > Regenerate
# 2. Update environment
export CLICKUP_API_TOKEN="pk_NEW_TOKEN_HERE"

# 3. Verify new token works
curl -sf https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.user.username'

# 4. Update secrets in deployment platform
gh secret set CLICKUP_API_TOKEN --body "$CLICKUP_API_TOKEN"
# or: vault kv put secret/clickup/api-token value="$CLICKUP_API_TOKEN"
# or: aws secretsmanager update-secret --secret-id clickup-api-token --secret-string "$CLICKUP_API_TOKEN"

# 5. Old token is automatically invalidated when you regenerate
```

## Least Privilege with OAuth Scopes

When building OAuth apps, request only needed access. ClickUp OAuth grants workspace-level access per authorized workspace.

```typescript
// OAuth: only request the workspaces you need
function getAuthUrl(workspaceId?: string): string {
  const params = new URLSearchParams({
    client_id: process.env.CLICKUP_CLIENT_ID!,
    redirect_uri: process.env.CLICKUP_REDIRECT_URI!,
  });
  return `https://app.clickup.com/api?${params}`;
}
```

## Environment-Specific Tokens

```typescript
function getClickUpToken(): string {
  const env = process.env.NODE_ENV ?? 'development';
  const tokenKey = {
    development: 'CLICKUP_API_TOKEN_DEV',
    staging: 'CLICKUP_API_TOKEN_STAGING',
    production: 'CLICKUP_API_TOKEN_PROD',
  }[env] ?? 'CLICKUP_API_TOKEN';

  const token = process.env[tokenKey];
  if (!token) throw new Error(`Missing ${tokenKey} for environment: ${env}`);
  return token;
}
```

## Audit Logging

```typescript
interface ClickUpAuditEntry {
  timestamp: string;
  method: string;
  endpoint: string;
  statusCode: number;
  rateLimitRemaining: number;
  userId?: string;
}

function logApiCall(entry: ClickUpAuditEntry): void {
  // Structured log for SIEM/audit systems
  console.log(JSON.stringify({
    level: 'audit',
    service: 'clickup',
    ...entry,
  }));
}

// Wrap all API calls
async function auditedRequest(path: string, options: RequestInit = {}) {
  const response = await fetch(`https://api.clickup.com/api/v2${path}`, {
    ...options,
    headers: { 'Authorization': getClickUpToken(), ...options.headers },
  });

  logApiCall({
    timestamp: new Date().toISOString(),
    method: options.method ?? 'GET',
    endpoint: path,
    statusCode: response.status,
    rateLimitRemaining: parseInt(
      response.headers.get('X-RateLimit-Remaining') ?? '-1'
    ),
  });

  return response;
}
```

## Security Checklist

- [ ] API tokens stored in environment variables, never in code
- [ ] `.env` files listed in `.gitignore`
- [ ] Pre-commit hook scanning for token patterns (`pk_*`)
- [ ] Separate tokens for dev/staging/production
- [ ] Token rotation procedure documented and tested
- [ ] Audit logging on all API calls
- [ ] OAuth client secret server-side only (never in frontend)
- [ ] Webhook endpoints use HTTPS only

## Error Handling

| Issue | Detection | Mitigation |
|-------|-----------|------------|
| Token in git history | `git log -p --all -S 'pk_'` | Rotate token immediately; use BFG Repo-Cleaner |
| Token in client bundle | Build output grep | Move to server-side only |
| Stale token after rotation | 401 errors spike | Update all deployments |

## Resources

- [ClickUp Authentication](https://developer.clickup.com/docs/authentication)
- [ClickUp Common Errors](https://developer.clickup.com/docs/common_errors)

## Next Steps

For production deployment, see `clickup-prod-checklist`.
