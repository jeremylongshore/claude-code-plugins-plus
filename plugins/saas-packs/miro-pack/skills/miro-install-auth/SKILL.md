---
name: miro-install-auth
description: |
  Install and configure Miro REST API v2 authentication with OAuth 2.0.
  Use when setting up a new Miro app, configuring OAuth tokens,
  or initializing the @mirohq/miro-api Node.js client.
  Trigger with phrases like "install miro", "setup miro",
  "miro auth", "miro OAuth", "configure miro API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, oauth, authentication]
compatible-with: claude-code
---

# Miro Install & Auth

## Overview

Set up the official `@mirohq/miro-api` Node.js client and configure OAuth 2.0 authentication against the Miro REST API v2 (`https://api.miro.com/v2/`).

## Prerequisites

- Node.js 18+
- A Miro account (Free, Business, or Enterprise)
- A Miro app created at https://developers.miro.com (Your apps > Create new app)
- Client ID, Client Secret, and OAuth redirect URI from the app settings

## Instructions

### Step 1: Install the Official SDK

```bash
# Official Miro Node.js client
npm install @mirohq/miro-api

# For Express-based OAuth callback server
npm install express dotenv
```

### Step 2: Configure OAuth 2.0 Credentials

```bash
# .env (NEVER commit — add to .gitignore)
MIRO_CLIENT_ID=your_client_id
MIRO_CLIENT_SECRET=your_client_secret
MIRO_REDIRECT_URI=http://localhost:3000/auth/miro/callback
MIRO_ACCESS_TOKEN=              # Filled after OAuth flow
MIRO_REFRESH_TOKEN=             # Filled after OAuth flow
```

Miro uses standard OAuth 2.0 authorization code flow. Tokens expire in 3599 seconds (approximately 1 hour). Always store and use the refresh token.

### Step 3: OAuth 2.0 Authorization Flow

```typescript
// src/auth.ts
import { Miro } from '@mirohq/miro-api';
import express from 'express';

// High-level client handles token management
const miro = new Miro({
  clientId: process.env.MIRO_CLIENT_ID!,
  clientSecret: process.env.MIRO_CLIENT_SECRET!,
  redirectUrl: process.env.MIRO_REDIRECT_URI!,
  // Storage adapter for tokens (implement for production)
  storage: {
    async get(userId: string) {
      // Return stored token for user
      return getTokenFromDB(userId);
    },
    async set(userId: string, token) {
      // Persist token
      await saveTokenToDB(userId, token);
    },
  },
});

const app = express();

// Step 1: Redirect user to Miro authorization page
app.get('/auth/miro', (req, res) => {
  const authUrl = miro.getAuthUrl();
  res.redirect(authUrl);
});

// Step 2: Handle OAuth callback
app.get('/auth/miro/callback', async (req, res) => {
  const { code } = req.query;
  if (!code || typeof code !== 'string') {
    return res.status(400).send('Missing authorization code');
  }

  try {
    // Exchange code for access_token + refresh_token
    await miro.exchangeCodeForAccessToken('default-user', code);
    res.send('Miro connected successfully!');
  } catch (err) {
    console.error('Token exchange failed:', err);
    res.status(500).send('Authentication failed');
  }
});

app.listen(3000, () => console.log('OAuth server at http://localhost:3000'));
```

### Step 4: Direct API Access (Access Token Only)

For scripts and automation where you already have an access token:

```typescript
// src/client.ts
import { MiroApi } from '@mirohq/miro-api';

// Low-level stateless client — pass token directly
const api = new MiroApi(process.env.MIRO_ACCESS_TOKEN!);

// Verify connection by listing boards
async function verifyConnection() {
  const boards = await api.getBoards();
  console.log(`Connected! Found ${boards.body.data?.length ?? 0} boards`);
  return true;
}

verifyConnection().catch(console.error);
```

### Step 5: Configure OAuth Scopes

In your Miro app settings (https://developers.miro.com), enable the scopes your app requires:

| Scope | Purpose | Required For |
|-------|---------|-------------|
| `boards:read` | Read board data, items, members | GET endpoints |
| `boards:write` | Create/update/delete boards and items | POST/PUT/PATCH/DELETE endpoints |
| `team:read` | Read team info and members | Team management |
| `team:write` | Manage team membership | Team provisioning |
| `organizations:read` | Read org structure | Enterprise features |
| `identity:read` | Read user profile | User identification |
| `auditlogs:read` | Read audit logs | Enterprise compliance |

Token response after successful exchange:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3599,
  "scope": "boards:read boards:write",
  "user_id": "1234567890",
  "team_id": "9876543210"
}
```

## Error Handling

| Error | HTTP Status | Cause | Solution |
|-------|-------------|-------|----------|
| `insufficientPermissions` | 403 | Missing OAuth scope | Add required scope in app settings and re-authorize |
| `tokenExpired` | 401 | Access token expired | Use refresh token to get new access token |
| `invalidGrant` | 400 | Auth code already used or expired | Restart OAuth flow from the beginning |
| `invalidClient` | 401 | Wrong client_id or client_secret | Verify credentials in Miro app settings |
| `ENOTFOUND api.miro.com` | N/A | DNS/network failure | Check internet and firewall rules |

## Token Refresh Pattern

```typescript
async function refreshAccessToken(): Promise<string> {
  const response = await fetch('https://api.miro.com/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: process.env.MIRO_CLIENT_ID!,
      client_secret: process.env.MIRO_CLIENT_SECRET!,
      refresh_token: process.env.MIRO_REFRESH_TOKEN!,
    }),
  });

  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.status}`);
  }

  const data = await response.json();
  // Store new tokens
  process.env.MIRO_ACCESS_TOKEN = data.access_token;
  process.env.MIRO_REFRESH_TOKEN = data.refresh_token;
  return data.access_token;
}
```

## Resources

- [Miro OAuth 2.0 Guide](https://developers.miro.com/docs/getting-started-with-oauth)
- [Permission Scopes Reference](https://developers.miro.com/reference/scopes)
- [Miro Node.js Client](https://developers.miro.com/docs/miro-nodejs-readme)
- [@mirohq/miro-api on npm](https://www.npmjs.com/package/@mirohq/miro-api)
- [Troubleshoot OAuth 2.0](https://developers.miro.com/docs/troubleshooting-oauth20)

## Next Steps

After successful auth, proceed to `miro-hello-world` for your first board and item operations.
