---
name: clickup-install-auth
description: |
  Set up ClickUp API v2 authentication with personal tokens or OAuth 2.0.
  Use when configuring a new ClickUp integration, setting up API access,
  or initializing OAuth flows for multi-user apps.
  Trigger: "install clickup", "setup clickup auth", "clickup API token",
  "clickup OAuth", "configure clickup credentials".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Install & Auth

## Overview

Configure ClickUp API v2 authentication. ClickUp supports two auth methods: **Personal API Tokens** (for personal/server-side use) and **OAuth 2.0** (for multi-user apps). There is no official SDK -- use direct HTTP calls to `https://api.clickup.com/api/v2/`.

## Prerequisites

- ClickUp account (any plan: Free Forever, Unlimited, Business, Business Plus, Enterprise)
- Node.js 18+ or Python 3.10+
- For OAuth 2.0: registered app in ClickUp's integrations dashboard

## Authentication Methods

### Method 1: Personal API Token (Recommended for Server-Side)

Generate at: **ClickUp Settings > Apps > API Token**

Personal tokens never expire and are tied to your ClickUp user account.

```bash
# Store token securely
echo 'CLICKUP_API_TOKEN=pk_12345678_ABCDEFGHIJKLMNOPQRSTUVWXYZ' >> .env
echo '.env' >> .gitignore
```

```typescript
// src/clickup/client.ts
const CLICKUP_BASE = 'https://api.clickup.com/api/v2';

async function clickupRequest(path: string, options: RequestInit = {}) {
  const response = await fetch(`${CLICKUP_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': process.env.CLICKUP_API_TOKEN!,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ClickUpError(response.status, error.err ?? error.ECODE ?? 'Unknown error');
  }

  return response.json();
}
```

### Method 2: OAuth 2.0 (For Multi-User Apps)

OAuth 2.0 uses the Authorization Code grant type. Access tokens currently do not expire.

```typescript
// Step 1: Redirect user to ClickUp authorization
const CLIENT_ID = process.env.CLICKUP_CLIENT_ID!;
const REDIRECT_URI = 'https://yourapp.com/auth/clickup/callback';

function getAuthUrl(): string {
  return `https://app.clickup.com/api?client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;
}

// Step 2: Exchange authorization code for access token
async function exchangeCodeForToken(code: string): Promise<string> {
  const response = await fetch('https://api.clickup.com/api/v2/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: process.env.CLICKUP_CLIENT_ID,
      client_secret: process.env.CLICKUP_CLIENT_SECRET,
      code,
    }),
  });

  const data = await response.json();
  // Response: { "access_token": "12345678_abcdefghijklmnopqrstuvwxyz" }
  return data.access_token;
}
```

## Verify Connection

```bash
# Quick test with personal token
curl -s https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.user.username'

# Verify authorized workspaces (API v2 calls Workspaces "teams")
curl -s https://api.clickup.com/api/v2/team \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.teams[].name'
```

```typescript
// Programmatic verification
async function verifyAuth(): Promise<{ user: string; workspaces: string[] }> {
  const user = await clickupRequest('/user');
  const teams = await clickupRequest('/team');

  return {
    user: user.user.username,
    workspaces: teams.teams.map((t: any) => t.name),
  };
}
```

## Error Handling

| HTTP Status | Error Code | Cause | Solution |
|-------------|------------|-------|----------|
| 401 | OAUTH_017 | Token missing or malformed | Include `Authorization` header with valid token |
| 401 | OAUTH_023 | Workspace not authorized for this token | Re-authorize the workspace via OAuth flow |
| 401 | OAUTH_027 | Token revoked or invalid | Generate a new personal token or re-authenticate |
| 429 | Rate limited | Exceeded requests/minute | Check `X-RateLimit-Reset` header; see `clickup-rate-limits` |

```typescript
class ClickUpError extends Error {
  constructor(public status: number, public code: string) {
    super(`ClickUp API error ${status}: ${code}`);
  }
}
```

## Environment Variables

```bash
# .env (NEVER commit)
CLICKUP_API_TOKEN=pk_12345678_ABCDEFGHIJKLMNOPQRSTUVWXYZ

# OAuth 2.0 (for multi-user apps)
CLICKUP_CLIENT_ID=your_client_id
CLICKUP_CLIENT_SECRET=your_client_secret
```

## Resources

- [ClickUp Authentication Docs](https://developer.clickup.com/docs/authentication)
- [ClickUp API Getting Started](https://developer.clickup.com/docs/Getting%20Started)
- [ClickUp Developer Portal](https://developer.clickup.com/)

## Next Steps

After auth setup, proceed to `clickup-hello-world` for your first API call.
