---
name: canva-install-auth
description: |
  Set up Canva Connect API OAuth 2.0 PKCE authentication and project scaffolding.
  Use when creating a new Canva integration, setting up OAuth credentials,
  or initializing a Canva Connect API project.
  Trigger with phrases like "install canva", "setup canva",
  "canva auth", "configure canva API", "canva OAuth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Connect API — Install & Auth

## Overview

Set up a Canva Connect API integration with OAuth 2.0 Authorization Code flow with PKCE (SHA-256). The Canva Connect API is a REST API at `https://api.canva.com/rest/v1/*` — there is no SDK package. All calls use `fetch` or `axios` with Bearer tokens.

## Prerequisites

- Node.js 18+ (for native `crypto.subtle` and `fetch`)
- A Canva account at [canva.com](https://www.canva.com)
- An integration registered at [canva.dev](https://www.canva.dev/docs/connect/creating-integrations/)

## Instructions

### Step 1: Register Your Integration

1. Go to **Settings > Integrations** at [canva.com/developers](https://www.canva.com/developers)
2. Create a new integration — note your **Client ID** and **Client Secret**
3. Add redirect URI(s): e.g. `http://localhost:3000/auth/canva/callback`
4. Enable required scopes under **Permissions**

### Step 2: Store Credentials

```bash
# .env (NEVER commit — add to .gitignore)
CANVA_CLIENT_ID=OCAxxxxxxxxxxxxxxxx
CANVA_CLIENT_SECRET=xxxxxxxxxxxxxxxx
CANVA_REDIRECT_URI=http://localhost:3000/auth/canva/callback
```

```bash
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 3: Implement OAuth 2.0 PKCE Flow

```typescript
// src/canva/auth.ts
import crypto from 'crypto';

// 1. Generate PKCE code verifier and challenge
export function generatePKCE(): { verifier: string; challenge: string } {
  const verifier = crypto.randomBytes(64).toString('base64url'); // 43-128 chars
  const challenge = crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');
  return { verifier, challenge };
}

// 2. Build the authorization URL
export function getAuthorizationUrl(opts: {
  clientId: string;
  redirectUri: string;
  scopes: string[];
  codeChallenge: string;
  state: string;
}): string {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: opts.clientId,
    redirect_uri: opts.redirectUri,
    scope: opts.scopes.join(' '),
    code_challenge: opts.codeChallenge,
    code_challenge_method: 'S256',
    state: opts.state,
  });
  return `https://www.canva.com/api/oauth/authorize?${params}`;
}

// 3. Exchange authorization code for access token
export async function exchangeCodeForToken(opts: {
  code: string;
  codeVerifier: string;
  clientId: string;
  clientSecret: string;
  redirectUri: string;
}): Promise<{ access_token: string; refresh_token: string; expires_in: number }> {
  const basicAuth = Buffer.from(
    `${opts.clientId}:${opts.clientSecret}`
  ).toString('base64');

  const res = await fetch('https://api.canva.com/rest/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${basicAuth}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code: opts.code,
      code_verifier: opts.codeVerifier,
      redirect_uri: opts.redirectUri,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(`Token exchange failed: ${err.error} — ${err.error_description}`);
  }
  return res.json();
}

// 4. Refresh an expired access token (access tokens expire in ~4 hours)
export async function refreshAccessToken(opts: {
  refreshToken: string;
  clientId: string;
  clientSecret: string;
}): Promise<{ access_token: string; refresh_token: string; expires_in: number }> {
  const basicAuth = Buffer.from(
    `${opts.clientId}:${opts.clientSecret}`
  ).toString('base64');

  const res = await fetch('https://api.canva.com/rest/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${basicAuth}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: opts.refreshToken,
    }),
  });

  if (!res.ok) throw new Error('Token refresh failed');
  return res.json();
}
```

### Step 4: Verify Connection

```typescript
// Verify token works by calling GET /v1/users/me (no scopes required)
async function verifyConnection(accessToken: string): Promise<void> {
  const res = await fetch('https://api.canva.com/rest/v1/users/me', {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });

  if (!res.ok) throw new Error(`Verification failed: ${res.status}`);

  const { team_user } = await res.json();
  console.log(`Connected — user_id: ${team_user.user_id}, team_id: ${team_user.team_id}`);
}
```

## Available OAuth Scopes

| Scope | Description |
|-------|-------------|
| `design:content:read` | Read design contents, export designs |
| `design:content:write` | Create designs, autofill brand templates |
| `design:meta:read` | List designs, get design metadata |
| `asset:read` | View uploaded asset metadata |
| `asset:write` | Upload, update, delete assets |
| `brandtemplate:content:read` | Read brand template content |
| `brandtemplate:meta:read` | List and view brand template metadata |
| `folder:read` | View folder contents |
| `folder:write` | Create, update, delete folders |
| `folder:permission:write` | Manage folder permissions |
| `comment:read` | Read design comments |
| `comment:write` | Create comments and replies |
| `collaboration:event` | Receive webhook notifications |
| `profile:read` | Read user profile information |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong client_id or secret | Verify credentials in Canva dashboard |
| `invalid_grant` | Expired or reused auth code | Restart OAuth flow — codes are single-use |
| `invalid_scope` | Scope not enabled | Enable scope in integration settings |
| `access_denied` | User rejected consent | Prompt user again |
| Token expired (401) | Access token > 4 hours old | Call refresh token endpoint |

## Resources

- [Canva Connect API Docs](https://www.canva.dev/docs/connect/)
- [Authentication Guide](https://www.canva.dev/docs/connect/authentication/)
- [Scopes Reference](https://www.canva.dev/docs/connect/appendix/scopes/)
- [OpenAPI Spec](https://www.canva.dev/sources/connect/api/latest/api.yml)

## Next Steps

After successful auth, proceed to `canva-hello-world` for your first API call.
