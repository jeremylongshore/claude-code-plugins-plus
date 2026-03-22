---
name: figma-install-auth
description: |
  Set up Figma REST API authentication with personal access tokens or OAuth 2.0.
  Use when connecting to the Figma API, generating tokens, configuring scopes,
  or setting up OAuth flows for Figma integrations.
  Trigger with phrases like "install figma", "setup figma API",
  "figma auth", "figma personal access token", "figma OAuth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Install & Auth

## Overview
Configure authentication for the Figma REST API. Figma supports two auth methods: Personal Access Tokens (PATs) for scripts and server-side tools, and OAuth 2.0 for apps that act on behalf of users. All requests go to `https://api.figma.com`.

## Prerequisites
- Figma account (Free, Professional, or Enterprise)
- Node.js 18+ (for JS/TS integrations)
- A Figma file key (the string after `/design/` in a Figma URL)

## Instructions

### Step 1: Generate a Personal Access Token
1. Open Figma > Settings > Account > Personal access tokens
2. Click **Generate new token**
3. Name the token and assign scopes:

| Scope | Access | Use Case |
|-------|--------|----------|
| `file_content:read` | Read file JSON | Inspecting layers, extracting design tokens |
| `file_content:write` | Modify files | Programmatic design updates |
| `file_comments:read` | Read comments | Review tooling |
| `file_comments:write` | Post comments | Automated feedback |
| `file_dev_resources:read` | Dev resources | Dev mode integrations |
| `file_variables:read` | Read variables | Design token sync |
| `file_variables:write` | Write variables | Token pipeline |
| `webhooks:write` | Manage webhooks | Event-driven automation |

3. Copy the token immediately -- it is shown only once
4. PATs expire after a maximum of 90 days

### Step 2: Store Credentials Securely
```bash
# .env (NEVER commit to git)
FIGMA_PAT="figd_your-personal-access-token"
FIGMA_FILE_KEY="abc123XYZdefaultFileKey"

# .gitignore
.env
.env.local
.env.*.local
```

### Step 3: Verify Connection
```bash
# Test with curl -- should return your user profile
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me | jq '.handle, .email'
```

```typescript
// verify-figma.ts
const PAT = process.env.FIGMA_PAT!;

const res = await fetch('https://api.figma.com/v1/me', {
  headers: { 'X-Figma-Token': PAT },
});

if (!res.ok) throw new Error(`Figma auth failed: ${res.status}`);
const me = await res.json();
console.log(`Authenticated as ${me.handle} (${me.email})`);
```

### Step 4: OAuth 2.0 (For User-Facing Apps)
Use OAuth when your app needs to act on behalf of other Figma users.

```typescript
// 1. Redirect user to Figma authorization URL
const authUrl = new URL('https://www.figma.com/oauth');
authUrl.searchParams.set('client_id', process.env.FIGMA_CLIENT_ID!);
authUrl.searchParams.set('redirect_uri', 'https://yourapp.com/auth/callback');
authUrl.searchParams.set('scope', 'file_content:read,file_comments:write');
authUrl.searchParams.set('state', crypto.randomUUID());
authUrl.searchParams.set('response_type', 'code');
// Redirect: res.redirect(authUrl.toString());

// 2. Exchange code for access token (must happen within 30 seconds)
async function exchangeCode(code: string): Promise<string> {
  const res = await fetch('https://api.figma.com/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.FIGMA_CLIENT_ID!,
      client_secret: process.env.FIGMA_CLIENT_SECRET!,
      redirect_uri: 'https://yourapp.com/auth/callback',
      code,
      grant_type: 'authorization_code',
    }),
  });
  const { access_token, refresh_token, expires_in } = await res.json();
  // Store refresh_token securely for later use
  return access_token;
}

// 3. Refresh expired tokens
async function refreshToken(refreshToken: string): Promise<string> {
  const res = await fetch('https://api.figma.com/v1/oauth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.FIGMA_CLIENT_ID!,
      client_secret: process.env.FIGMA_CLIENT_SECRET!,
      refresh_token: refreshToken,
    }),
  });
  const { access_token } = await res.json();
  return access_token;
}
```

## Output
- Personal access token stored in `.env`
- Successful `GET /v1/me` returning your user handle
- (Optional) OAuth flow with token exchange working

## Error Handling
| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `403 Forbidden` | 403 | Token lacks required scope | Regenerate PAT with correct scopes |
| `Invalid token` | 403 | Expired or revoked PAT | Generate a new token (90-day max) |
| `OAuth code expired` | 400 | Code exchange took >30s | Retry auth flow; exchange immediately |
| `Invalid redirect_uri` | 400 | Redirect URL mismatch | Must match URL registered in Figma OAuth app settings |
| `Rate limited` | 429 | Too many auth attempts | Wait for `Retry-After` header value |

## Examples

### Reusable Figma Client Wrapper
```typescript
// src/figma-client.ts
export function figmaFetch(path: string, options: RequestInit = {}) {
  const token = process.env.FIGMA_PAT;
  if (!token) throw new Error('FIGMA_PAT environment variable is not set');

  return fetch(`https://api.figma.com${path}`, {
    ...options,
    headers: {
      'X-Figma-Token': token,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
}

// Usage
const file = await figmaFetch(`/v1/files/${fileKey}`).then(r => r.json());
```

## Resources
- [Figma REST API Authentication](https://developers.figma.com/docs/rest-api/authentication/)
- [Manage Personal Access Tokens](https://help.figma.com/hc/en-us/articles/8085703771159)
- [Figma API Scopes Reference](https://developers.figma.com/docs/rest-api/scopes/)

## Next Steps
After successful auth, proceed to `figma-hello-world` for your first real API call.
