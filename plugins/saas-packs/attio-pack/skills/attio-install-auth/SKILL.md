---
name: attio-install-auth
description: |
  Set up Attio REST API authentication with access tokens or OAuth 2.0.
  Use when configuring API keys, setting token scopes, initializing
  the Attio client, or connecting an app via OAuth.
  Trigger: "install attio", "setup attio", "attio auth", "attio API key",
  "attio OAuth", "attio access token".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Install & Auth

## Overview

Configure authentication for the Attio REST API (`https://api.attio.com/v2`). Attio offers two auth methods: **access tokens** (scoped to a single workspace) and **OAuth 2.0** (for multi-workspace integrations). There is no official first-party Node SDK -- use `fetch` or a community client like `attio-js`.

## Prerequisites

- Node.js 18+ or Python 3.10+
- Attio account at [app.attio.com](https://app.attio.com)
- API access enabled in workspace settings

## Instructions

### Step 1: Generate an Access Token

1. Open **Settings > Developers > Access tokens** in your Attio workspace
2. Click **Create token** and name it (e.g., `my-integration-dev`)
3. Configure scopes (tokens have **no scopes by default** -- you must add them):

| Scope | Grants access to |
|-------|-----------------|
| `object_configuration:read` | List/get objects and attributes |
| `record_permission:read` | Read records (people, companies, deals) |
| `record_permission:read-write` | Create/update/delete records |
| `list_entry:read` | Read list entries |
| `list_entry:read-write` | Create/update/delete list entries |
| `note:read-write` | Create and read notes |
| `task:read` / `task:read-write` | Read or manage tasks |
| `user_management:read` | Read workspace members |
| `webhook:read-write` | Manage webhooks |

4. Copy the token -- it starts with `sk_` and **never expires** (but can be revoked)

### Step 2: Configure Environment

```bash
# .env (add to .gitignore immediately)
ATTIO_API_KEY=sk_your_token_here

# .gitignore
.env
.env.local
.env.*.local
```

### Step 3: Initialize the Client

```typescript
// src/attio/client.ts
const ATTIO_BASE = "https://api.attio.com/v2";

interface AttioRequestOptions {
  method?: string;
  path: string;
  body?: Record<string, unknown>;
}

export async function attioFetch<T>({
  method = "GET",
  path,
  body,
}: AttioRequestOptions): Promise<T> {
  const res = await fetch(`${ATTIO_BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${process.env.ATTIO_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(
      `Attio ${res.status}: ${error.code} - ${error.message}`
    );
  }

  return res.json() as Promise<T>;
}
```

### Step 4: Verify Connection

```typescript
// Verify by listing workspace objects
const objects = await attioFetch<{ data: Array<{ api_slug: string }> }>({
  path: "/objects",
});

console.log(
  "Connected! Objects:",
  objects.data.map((o) => o.api_slug)
);
// Output: Connected! Objects: ["people", "companies", "deals", ...]
```

```bash
# Quick verification with curl
curl -s https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" | jq '.data[].api_slug'
```

## OAuth 2.0 Flow (Multi-Workspace)

For apps that other workspaces install, use OAuth 2.0 Authorization Code Grant (RFC 6749 section 4.1).

```typescript
// Step 1: Redirect user to authorize
const authUrl = new URL("https://app.attio.com/authorize");
authUrl.searchParams.set("client_id", process.env.ATTIO_CLIENT_ID!);
authUrl.searchParams.set("redirect_uri", "https://yourapp.com/callback");
authUrl.searchParams.set("response_type", "code");

// Step 2: Exchange code for access token
const tokenRes = await fetch("https://app.attio.com/oauth/token", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    grant_type: "authorization_code",
    client_id: process.env.ATTIO_CLIENT_ID,
    client_secret: process.env.ATTIO_CLIENT_SECRET,
    code: authorizationCode,
    redirect_uri: "https://yourapp.com/callback",
  }),
});

const { access_token } = await tokenRes.json();
// Store access_token securely per workspace
```

## Error Handling

| Error | HTTP Status | Cause | Solution |
|-------|------------|-------|----------|
| `invalid_grant` | 401 | Bad or expired auth code | Re-authorize the user |
| `insufficient_scopes` | 403 | Token missing required scope | Add scope in dashboard, regenerate |
| `invalid_request` | 400 | Malformed Authorization header | Use `Bearer <token>` format |
| `not_found` | 404 | Token revoked or workspace deleted | Generate new token |

## Attio Error Response Format

All Attio errors return JSON with a consistent structure:

```json
{
  "status_code": 403,
  "type": "authorization_error",
  "code": "insufficient_scopes",
  "message": "Token requires 'record_permission:read' scope"
}
```

## Resources

- [Attio Access Token Guide](https://attio.com/help/apps/other-apps/generating-an-api-key)
- [Attio OAuth Tutorial](https://docs.attio.com/rest-api/tutorials/connect-an-app-through-oauth)
- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Authentication](https://docs.attio.com/rest-api/guides/authentication)

## Next Steps

After verifying auth, proceed to `attio-hello-world` for your first real API call.
