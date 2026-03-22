---
name: webflow-install-auth
description: |
  Install the Webflow JS SDK (webflow-api) and configure OAuth 2.0 or API token authentication.
  Use when setting up a new Webflow integration, configuring access tokens,
  or initializing the WebflowClient in your project.
  Trigger with phrases like "install webflow", "setup webflow",
  "webflow auth", "configure webflow API token", "webflow OAuth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Install & Auth

## Overview

Set up the official Webflow JS SDK (`webflow-api` on npm) and configure authentication
using either a workspace/site API token or OAuth 2.0 for Data Client Apps.

## Prerequisites

- Node.js 18+
- npm, pnpm, or yarn
- A Webflow account with a workspace
- An API token (workspace or site) from `https://developers.webflow.com`

## Instructions

### Step 1: Install the SDK

```bash
# npm
npm install webflow-api

# pnpm
pnpm add webflow-api

# yarn
yarn add webflow-api
```

The package is `webflow-api` (not `@webflow/sdk`). Current version: 3.x (Data API v2).

### Step 2: Choose Authentication Method

Webflow offers two auth methods:

| Method | Use Case | Scope |
|--------|----------|-------|
| **API Token** (workspace) | Server-side scripts, internal tools | All sites in workspace |
| **API Token** (site) | Single-site integrations | One site only |
| **OAuth 2.0** | Public apps, Webflow Marketplace apps | User-authorized scopes |

### Step 3: Token-Based Authentication

```bash
# Set environment variable (never hardcode tokens)
echo 'WEBFLOW_API_TOKEN=your-token-here' >> .env
echo '.env' >> .gitignore
```

```typescript
import { WebflowClient } from "webflow-api";

// Initialize with workspace or site token
const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});
```

### Step 4: OAuth 2.0 Flow (Data Client Apps)

For apps that need user authorization, implement the OAuth 2.0 authorization code flow:

```typescript
import express from "express";
import { WebflowClient } from "webflow-api";

const app = express();

const CLIENT_ID = process.env.WEBFLOW_CLIENT_ID!;
const CLIENT_SECRET = process.env.WEBFLOW_CLIENT_SECRET!;
const REDIRECT_URI = "https://yourapp.com/auth/webflow/callback";

// Step 1: Redirect user to Webflow authorization page
// Scopes: sites:read, sites:write, cms:read, cms:write,
//         pages:read, pages:write, forms:read, ecommerce:read,
//         ecommerce:write, custom_code:read, custom_code:write
app.get("/auth/webflow", (req, res) => {
  const scopes = "sites:read cms:read cms:write";
  const authUrl =
    `https://webflow.com/oauth/authorize` +
    `?client_id=${CLIENT_ID}` +
    `&response_type=code` +
    `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
    `&scope=${encodeURIComponent(scopes)}`;
  res.redirect(authUrl);
});

// Step 2: Exchange authorization code for access token
// The authorization code expires in 15 minutes
app.get("/auth/webflow/callback", async (req, res) => {
  const code = req.query.code as string;

  const response = await fetch("https://api.webflow.com/oauth/access_token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      code,
      grant_type: "authorization_code",
      redirect_uri: REDIRECT_URI,
    }),
  });

  const { access_token } = await response.json();

  // Store access_token securely — it does not expire but can be revoked
  const webflow = new WebflowClient({ accessToken: access_token });
  const { sites } = await webflow.sites.list();

  res.json({ authorized: true, siteCount: sites?.length });
});
```

### Step 5: Verify Connection

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

async function verify() {
  // List all sites accessible with this token
  const { sites } = await webflow.sites.list();

  if (!sites || sites.length === 0) {
    throw new Error("No sites accessible. Check token scopes.");
  }

  for (const site of sites) {
    console.log(`Site: ${site.displayName} (${site.id})`);
    console.log(`  Short name: ${site.shortName}`);
    console.log(`  Last published: ${site.lastPublished}`);
  }
}

verify().catch(console.error);
```

## Webflow API Scopes Reference

| Scope | Access |
|-------|--------|
| `sites:read` | List/get sites |
| `sites:write` | Publish sites |
| `cms:read` | Read collections and items |
| `cms:write` | Create/update/delete CMS items |
| `pages:read` | List/get pages |
| `pages:write` | Update page content |
| `forms:read` | Read form submissions |
| `ecommerce:read` | Read products, orders, inventory |
| `ecommerce:write` | Create/update products, fulfill orders |
| `custom_code:read` | Read registered custom code |
| `custom_code:write` | Register/apply custom code |

## Output

- Installed `webflow-api` package
- Environment variable with API token (`.env` file, git-ignored)
- Working `WebflowClient` instance
- Verified connection by listing accessible sites

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or revoked token | Generate new token at developers.webflow.com |
| `403 Forbidden` | Token missing required scope | Add scopes in app settings or generate new token |
| `429 Too Many Requests` | Rate limit exceeded | Wait for `Retry-After` header (60s reset) |
| `MODULE_NOT_FOUND` | Wrong package name | Use `webflow-api`, not `@webflow/sdk` |
| OAuth code expired | Authorization code > 15 min old | Re-initiate OAuth flow promptly |

## Resources

- [Webflow Developer Docs](https://developers.webflow.com)
- [SDK npm package](https://www.npmjs.com/package/webflow-api)
- [SDK GitHub repo](https://github.com/webflow/js-webflow-api)
- [OAuth Reference](https://developers.webflow.com/data/reference/oauth-app)
- [Scopes Reference](https://developers.webflow.com/data/reference/scopes)

## Next Steps

After successful auth, proceed to `webflow-hello-world` for your first API call.
