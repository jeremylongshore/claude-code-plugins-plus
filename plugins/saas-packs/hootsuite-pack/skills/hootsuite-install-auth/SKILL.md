---
name: hootsuite-install-auth
description: |
  Install and configure Hootsuite SDK/CLI authentication.
  Use when setting up a new Hootsuite integration, configuring API keys,
  or initializing Hootsuite in your project.
  Trigger with phrases like "install hootsuite", "setup hootsuite",
  "hootsuite auth", "configure hootsuite API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Install & Auth

## Overview

Configure Hootsuite REST API OAuth 2.0 authentication. Hootsuite uses OAuth 2.0 with Bearer tokens. You register an app in the Hootsuite Developer Portal, get client credentials, and exchange authorization codes for access tokens.

## Prerequisites

- Hootsuite account (Business plan or higher for API access)
- Registered app at https://developer.hootsuite.com
- Client ID and Client Secret from your app

## Instructions

### Step 1: Register Your App

1. Go to https://developer.hootsuite.com
2. Create a new app
3. Note your Client ID and Client Secret
4. Set redirect URI to `https://your-app.com/callback`

### Step 2: Configure Environment

```bash
# .env (NEVER commit)
HOOTSUITE_CLIENT_ID=your_client_id
HOOTSUITE_CLIENT_SECRET=your_client_secret
HOOTSUITE_REDIRECT_URI=https://your-app.com/callback
HOOTSUITE_ACCESS_TOKEN=  # Populated after OAuth flow

# .gitignore
.env
.env.local
```

### Step 3: OAuth 2.0 Authorization Flow

```typescript
// auth.ts — OAuth 2.0 authorization code flow
import 'dotenv/config';

const { HOOTSUITE_CLIENT_ID, HOOTSUITE_CLIENT_SECRET, HOOTSUITE_REDIRECT_URI } = process.env;

// Step 1: Redirect user to authorize
function getAuthUrl(): string {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: HOOTSUITE_CLIENT_ID!,
    redirect_uri: HOOTSUITE_REDIRECT_URI!,
    scope: 'offline',
  });
  return `https://platform.hootsuite.com/oauth2/auth?${params}`;
}

// Step 2: Exchange authorization code for tokens
async function exchangeCode(code: string) {
  const response = await fetch('https://platform.hootsuite.com/oauth2/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': `Basic ${Buffer.from(`${HOOTSUITE_CLIENT_ID}:${HOOTSUITE_CLIENT_SECRET}`).toString('base64')}`,
    },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: HOOTSUITE_REDIRECT_URI!,
    }),
  });

  const tokens = await response.json();
  console.log('Access Token:', tokens.access_token);
  console.log('Refresh Token:', tokens.refresh_token);
  console.log('Expires In:', tokens.expires_in, 'seconds');
  return tokens;
}

// Step 3: Refresh expired token
async function refreshToken(refreshToken: string) {
  const response = await fetch('https://platform.hootsuite.com/oauth2/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': `Basic ${Buffer.from(`${HOOTSUITE_CLIENT_ID}:${HOOTSUITE_CLIENT_SECRET}`).toString('base64')}`,
    },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
    }),
  });
  return response.json();
}
```

### Step 4: Verify Connection

```typescript
async function verifyConnection(accessToken: string) {
  const response = await fetch('https://platform.hootsuite.com/v1/me', {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  const user = await response.json();
  console.log('Connected as:', user.data.fullName);
  console.log('Organization:', user.data.organizationName);
  return user;
}
```

## Output

- OAuth 2.0 app credentials configured
- Access token obtained via authorization code flow
- Token refresh mechanism for long-lived access
- Connection verified with user profile

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Refresh token or re-authorize |
| `invalid_client` | Wrong client ID/secret | Check app credentials |
| `invalid_grant` | Authorization code expired | Codes expire in 30s; re-authorize |
| `redirect_uri_mismatch` | URI doesn't match | Must exactly match app registration |

## Resources

- [Hootsuite Developer Portal](https://developer.hootsuite.com)
- [OAuth 2.0 Guide](https://developer.hootsuite.com/docs/using-rest-apis)
- [API Overview](https://developer.hootsuite.com/docs/api-overview)

## Next Steps

After auth, proceed to `hootsuite-hello-world` for your first API call.
