---
name: grammarly-install-auth
description: |
  Install and configure Grammarly SDK/CLI authentication.
  Use when setting up a new Grammarly integration, configuring API keys,
  or initializing Grammarly in your project.
  Trigger with phrases like "install grammarly", "setup grammarly",
  "grammarly auth", "configure grammarly API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Install & Auth

## Overview

Configure Grammarly API authentication using OAuth 2.0 Bearer tokens. Grammarly provides three main APIs: Writing Score API, AI Detection API, and Plagiarism Detection API. All use the same auth pattern via `api.grammarly.com`.

## Prerequisites

- Grammarly Enterprise account with API access
- OAuth credentials from Grammarly admin portal
- Required scopes: `scores-api:read`, `scores-api:write`

## Instructions

### Step 1: Configure Environment

```bash
# .env (NEVER commit)
GRAMMARLY_CLIENT_ID=your_client_id
GRAMMARLY_CLIENT_SECRET=your_client_secret
GRAMMARLY_ACCESS_TOKEN=  # Populated after OAuth
```

### Step 2: Obtain Access Token

```typescript
// auth.ts
import 'dotenv/config';

async function getAccessToken(): Promise<string> {
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.GRAMMARLY_CLIENT_ID!,
      client_secret: process.env.GRAMMARLY_CLIENT_SECRET!,
    }),
  });
  const { access_token, expires_in } = await response.json();
  console.log(`Token obtained, expires in ${expires_in}s`);
  return access_token;
}
```

### Step 3: Verify Connection

```typescript
async function verify(token: string) {
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v2/scores', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: 'This is a test sentence for verification.' }),
  });
  if (response.ok) console.log('Grammarly API connection verified');
  else console.error('Verification failed:', response.status);
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Re-authenticate |
| `403 Forbidden` | Missing API scopes | Check enterprise admin settings |
| `invalid_client` | Wrong credentials | Verify client ID and secret |

## Resources

- [Grammarly Developer Portal](https://developer.grammarly.com/)
- [Your First API Request](https://developer.grammarly.com/your-first-api-request.html)
- [API Support](https://developer.grammarly.com/docs/support)

## Next Steps

After auth, proceed to `grammarly-hello-world`.
