---
name: salesloft-install-auth
description: |
  Set up SalesLoft API authentication with OAuth 2.0 or API key.
  Use when configuring a new SalesLoft integration, setting up OAuth flows,
  or initializing API access to the SalesLoft REST API v2.
  Trigger: "install salesloft", "setup salesloft", "salesloft auth", "salesloft API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Install & Auth

## Overview

Configure access to the SalesLoft REST API v2. SalesLoft supports two OAuth 2.0 flows (authorization code and client credentials) plus API key auth. All requests require `Authorization: Bearer <token>` header. Base URL: `https://api.salesloft.com/v2/`.

## Prerequisites

- SalesLoft account with API access enabled
- App registered at [developers.salesloft.com](https://developers.salesloft.com) for OAuth
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Install HTTP Client

```bash
# Node.js — no official SDK, use axios or fetch
npm install axios dotenv

# Python
pip install requests python-dotenv
```

### Step 2: Register OAuth Application

1. Go to [developers.salesloft.com](https://developers.salesloft.com) > Your Applications
2. Click "Create Application"
3. Set redirect URI (e.g., `http://localhost:3000/callback`)
4. Copy `client_id` and `client_secret`

### Step 3: Configure Environment

```bash
# .env
SALESLOFT_CLIENT_ID=your-client-id
SALESLOFT_CLIENT_SECRET=your-client-secret
SALESLOFT_REDIRECT_URI=http://localhost:3000/callback
SALESLOFT_API_KEY=your-api-key  # If using API key auth
```

### Step 4: Implement OAuth Authorization Code Flow

```typescript
import axios from 'axios';

// Step 1: Redirect user to authorize
const authUrl = `https://accounts.salesloft.com/oauth/authorize?` +
  `client_id=${process.env.SALESLOFT_CLIENT_ID}` +
  `&redirect_uri=${encodeURIComponent(process.env.SALESLOFT_REDIRECT_URI!)}` +
  `&response_type=code`;

// Step 2: Exchange code for token (in callback handler)
async function exchangeCode(code: string) {
  const { data } = await axios.post('https://accounts.salesloft.com/oauth/token', {
    client_id: process.env.SALESLOFT_CLIENT_ID,
    client_secret: process.env.SALESLOFT_CLIENT_SECRET,
    code,
    grant_type: 'authorization_code',
    redirect_uri: process.env.SALESLOFT_REDIRECT_URI,
  });
  // data.access_token, data.refresh_token, data.expires_in
  return data;
}
```

### Step 5: Client Credentials Flow (Server-to-Server)

```typescript
// No user interaction — recommended for background tasks
async function getServiceToken() {
  const { data } = await axios.post('https://accounts.salesloft.com/oauth/token', {
    client_id: process.env.SALESLOFT_CLIENT_ID,
    client_secret: process.env.SALESLOFT_CLIENT_SECRET,
    grant_type: 'client_credentials',
  });
  return data.access_token;
}
```

### Step 6: Verify Connection

```typescript
const token = await getServiceToken();
const { data } = await axios.get('https://api.salesloft.com/v2/me.json', {
  headers: { Authorization: `Bearer ${token}` },
});
console.log(`Authenticated as: ${data.data.name} (${data.data.email})`);
```

## Output

```
Authenticated as: Jane Smith (jane@company.com)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Expired or invalid token | Refresh token or re-authorize |
| `403 Forbidden` | Insufficient OAuth scopes | Check app permissions in developer portal |
| `invalid_grant` | Authorization code already used | Codes are single-use; restart OAuth flow |
| `invalid_client` | Wrong client_id/secret | Verify credentials in developer portal |

## Token Refresh

```typescript
async function refreshAccessToken(refreshToken: string) {
  const { data } = await axios.post('https://accounts.salesloft.com/oauth/token', {
    client_id: process.env.SALESLOFT_CLIENT_ID,
    client_secret: process.env.SALESLOFT_CLIENT_SECRET,
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
  });
  return data; // { access_token, refresh_token, expires_in }
}
```

## Resources

- [SalesLoft API Basics](https://developers.salesloft.com/docs/platform/api-basics/)
- [OAuth Authorization Code](https://developers.salesloft.com/docs/platform/api-basics/oauth-authentication/)
- [OAuth Client Credentials](https://developers.salesloft.com/docs/platform/api-basics/client-creds/)
- [API Reference (Swagger)](https://api.salesloft.com/swagger/index.html)

## Next Steps

After successful auth, proceed to `salesloft-hello-world` for your first API call.
