---
name: intercom-install-auth
description: |
  Install and configure Intercom API authentication with access tokens or OAuth.
  Use when setting up a new Intercom integration, configuring API credentials,
  or initializing the intercom-client SDK in your project.
  Trigger with phrases like "install intercom", "setup intercom",
  "intercom auth", "configure intercom API key", "intercom access token".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Install & Auth

## Overview

Set up the official `intercom-client` TypeScript SDK and configure authentication via access tokens (private apps) or OAuth (public apps).

## Prerequisites

- Node.js 18+
- npm, pnpm, or yarn
- Intercom workspace with Developer Hub access
- Access token from Configure > Authentication in your app settings

## Instructions

### Step 1: Install the SDK

```bash
npm install intercom-client
```

The package exports `IntercomClient` and all TypeScript types under the `Intercom` namespace.

### Step 2: Configure Access Token Authentication

Access tokens authenticate private apps that access your own Intercom workspace.

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});
```

Store the token securely:

```bash
# .env (add to .gitignore)
INTERCOM_ACCESS_TOKEN=dG9rOmFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6

# Verify .gitignore includes .env
echo '.env' >> .gitignore
```

### Step 3: Verify Connection

```typescript
async function verifyConnection() {
  try {
    // List admins to verify the token works
    const admins = await client.admins.list();
    console.log("Connected! Admins:", admins.admins.length);
    for (const admin of admins.admins) {
      console.log(`  - ${admin.name} (${admin.email})`);
    }
  } catch (error) {
    if (error instanceof Error) {
      console.error("Connection failed:", error.message);
    }
  }
}

verifyConnection();
```

### Step 4: OAuth Setup (Public Apps)

For apps that access other workspaces, configure OAuth:

```typescript
// Step 1: Redirect user to Intercom authorization
const authUrl = `https://app.intercom.com/oauth?client_id=${CLIENT_ID}&state=${STATE}`;

// Step 2: Exchange code for token at your callback endpoint
async function handleOAuthCallback(code: string): Promise<string> {
  const response = await fetch("https://api.intercom.io/auth/eagle/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: process.env.INTERCOM_CLIENT_ID,
      client_secret: process.env.INTERCOM_CLIENT_SECRET,
      code,
    }),
  });

  const data = await response.json();
  return data.token; // Use this token for API calls
}

// Step 3: Initialize client with OAuth token
const client = new IntercomClient({ token: oauthToken });
```

## API Versioning

Specify the API version header to pin behavior:

```typescript
const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// All requests use Bearer token in Authorization header:
// Authorization: Bearer <token>
// Intercom-Version: 2.11
```

The current stable API version is **2.11**. The SDK handles this automatically.

## OAuth Scopes Reference

| Scope | Access Granted |
|-------|---------------|
| Read admins | List workspace admins |
| Read/write contacts | Create, update, search contacts |
| Read/write conversations | Manage conversations and replies |
| Read/write messages | Send outbound messages |
| Read/write articles | Manage Help Center content |
| Read/write tags | Tag contacts, companies, conversations |
| Read/write events | Submit and read data events |
| Read/write companies | Manage company records |

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `unauthorized` | 401 | Invalid or expired token | Regenerate in Developer Hub |
| `forbidden` | 403 | Missing OAuth scope | Add required scope in app config |
| `token_revoked` | 401 | Token was revoked | Generate new access token |
| `invalid_grant` | 400 | OAuth code expired | Restart OAuth flow |

```typescript
import { IntercomError } from "intercom-client";

try {
  await client.contacts.list();
} catch (error) {
  if (error instanceof IntercomError) {
    console.error(`Intercom error: ${error.statusCode} - ${error.message}`);
    if (error.statusCode === 401) {
      console.error("Token invalid. Regenerate at app.intercom.com > Developer Hub");
    }
  }
}
```

## Resources

- [Authentication Guide](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [OAuth Scopes](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/oauth-scopes)
- [Setting up OAuth](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/setting-up-oauth)
- [intercom-client npm](https://www.npmjs.com/package/intercom-client)

## Next Steps

After successful auth, proceed to `intercom-hello-world` for your first API call.
