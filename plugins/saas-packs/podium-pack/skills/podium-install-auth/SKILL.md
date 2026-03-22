---
name: podium-install-auth
description: |
  Podium install auth — business messaging and communication platform integration.
  Use when working with Podium API for messaging, reviews, or payments.
  Trigger with phrases like "podium install auth", "podium-install-auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, podium, messaging, reviews, payments]
compatible-with: claude-code, codex, openclaw
---

# Podium Install Auth

## Overview
Set up Podium API authentication using OAuth2 authorization code flow. Podium requires a Developer Account, OAuth application credentials, and user authorization to access location data.

## Prerequisites
- Podium Developer Account (apply at developer.podium.com)
- OAuth Application credentials (client_id, client_secret)
- A Podium location to authorize against

## Instructions

### Step 1: Register OAuth Application
```text
1. Go to developer.podium.com
2. Create a new OAuth Application
3. Set redirect URI: http://localhost:3000/callback
4. Copy client_id and client_secret
5. Select scopes: messages.read, messages.write, contacts.read, reviews.read
```

### Step 2: Configure Environment
```bash
# .env
PODIUM_CLIENT_ID=your_client_id
PODIUM_CLIENT_SECRET=your_client_secret
PODIUM_REDIRECT_URI=http://localhost:3000/callback
```

### Step 3: OAuth2 Authorization Flow
```typescript
import express from 'express';
import axios from 'axios';

const app = express();

// Step 1: Redirect user to Podium authorization
app.get('/auth', (req, res) => {
  const authUrl = `https://api.podium.com/oauth/authorize?client_id=${process.env.PODIUM_CLIENT_ID}&redirect_uri=${encodeURIComponent(process.env.PODIUM_REDIRECT_URI!)}&response_type=code&scope=messages.read+messages.write`;
  res.redirect(authUrl);
});

// Step 2: Exchange code for access token
app.get('/callback', async (req, res) => {
  const { code } = req.query;
  const { data } = await axios.post('https://api.podium.com/oauth/token', {
    grant_type: 'authorization_code',
    code,
    client_id: process.env.PODIUM_CLIENT_ID,
    client_secret: process.env.PODIUM_CLIENT_SECRET,
    redirect_uri: process.env.PODIUM_REDIRECT_URI,
  });
  console.log(`Access token: ${data.access_token}`);
  console.log(`Refresh token: ${data.refresh_token}`);
  res.json({ status: 'authenticated' });
});

app.listen(3000);
```

### Step 4: Verify Connection
```typescript
const podium = axios.create({
  baseURL: 'https://api.podium.com/v4',
  headers: { 'Authorization': `Bearer ${accessToken}` },
});

const { data } = await podium.get('/locations');
console.log(`Connected! Locations: ${data.data.length}`);
```

## Output
- OAuth application registered with Podium
- Authorization code flow implemented
- Access and refresh tokens obtained
- API connectivity verified

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong client_id/secret | Verify credentials in developer portal |
| `invalid_grant` | Expired authorization code | Codes expire quickly — retry auth flow |
| `invalid_scope` | Scope not approved | Request scope approval from Podium |
| `401 Unauthorized` | Expired access token | Use refresh token to get new access token |

## Resources
- [Podium OAuth2 Guide](https://docs.podium.com/docs/oauth)
- [Getting Started](https://docs.podium.com/docs/getting-started)
- [Developer Portal](https://developer.podium.com/)

## Next Steps
Send your first message: `podium-hello-world`
