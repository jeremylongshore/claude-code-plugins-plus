---
name: linear-install-auth
description: |
  Install and configure Linear SDK/CLI authentication.
  Use when setting up a new Linear integration, configuring API keys,
  OAuth2 flows, or initializing LinearClient in your project.
  Trigger: "install linear", "setup linear", "linear auth",
  "configure linear API key", "linear SDK setup", "linear OAuth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, authentication]

---
# Linear Install & Auth

## Overview
Install the `@linear/sdk` TypeScript SDK and configure authentication for the Linear GraphQL API at `https://api.linear.app/graphql`. Supports personal API keys for scripts and OAuth 2.0 (with PKCE) for user-facing apps.

## Prerequisites
- Node.js 18+ (SDK is TypeScript-first, works in any JS environment)
- Package manager (npm, pnpm, or yarn)
- Linear account with workspace access
- For API key: Settings > Account > API > Personal API keys
- For OAuth: Create app at Settings > Account > API > OAuth applications

## Instructions

### Step 1: Install the SDK
```bash
set -euo pipefail
npm install @linear/sdk
# or: pnpm add @linear/sdk
# or: yarn add @linear/sdk
```

The SDK exposes `LinearClient`, typed models for every entity (Issue, Project, Cycle, Team), and error classes (`LinearError`, `InvalidInputLinearError`).

### Step 2: API Key Authentication (Scripts & Server-Side)
Generate a Personal API key at Linear Settings > Account > API > Personal API keys. Keys start with `lin_api_` and are shown only once.

```typescript
import { LinearClient } from "@linear/sdk";

// Environment variable (recommended)
const client = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY,
});

// Verify connection
const me = await client.viewer;
console.log(`Authenticated as: ${me.name} (${me.email})`);
```

**Environment setup:**
```bash
# .env (never commit)
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# .gitignore
echo '.env' >> .gitignore
```

### Step 3: OAuth 2.0 Authentication (User-Facing Apps)
Linear supports the standard Authorization Code flow with optional PKCE. As of October 2025, newly created OAuth apps issue refresh tokens by default.

```typescript
import crypto from "crypto";

// 1. Build authorization URL
const SCOPES = ["read", "write", "issues:create"];
const state = crypto.randomBytes(16).toString("hex");

const authUrl = new URL("https://linear.app/oauth/authorize");
authUrl.searchParams.set("client_id", process.env.LINEAR_CLIENT_ID!);
authUrl.searchParams.set("redirect_uri", process.env.LINEAR_REDIRECT_URI!);
authUrl.searchParams.set("response_type", "code");
authUrl.searchParams.set("scope", SCOPES.join(","));
authUrl.searchParams.set("state", state);
// Optional PKCE:
// authUrl.searchParams.set("code_challenge", challenge);
// authUrl.searchParams.set("code_challenge_method", "S256");

// 2. Exchange authorization code for tokens
const tokenResponse = await fetch("https://api.linear.app/oauth/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({
    grant_type: "authorization_code",
    code: authorizationCode,
    client_id: process.env.LINEAR_CLIENT_ID!,
    client_secret: process.env.LINEAR_CLIENT_SECRET!,
    redirect_uri: process.env.LINEAR_REDIRECT_URI!,
  }),
});

const { access_token, refresh_token, expires_in } = await tokenResponse.json();

// 3. Create client with OAuth token
const client = new LinearClient({ accessToken: access_token });
```

**Available OAuth scopes:** `read`, `write`, `issues:create`, `admin`, `initiative:read`, `initiative:write`, `customer:read`, `customer:write`.

### Step 4: Token Refresh (OAuth)
```typescript
async function refreshAccessToken(refreshToken: string): Promise<string> {
  const response = await fetch("https://api.linear.app/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
      client_id: process.env.LINEAR_CLIENT_ID!,
      client_secret: process.env.LINEAR_CLIENT_SECRET!,
    }),
  });

  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.status}`);
  }

  const tokens = await response.json();
  // Store new refresh_token — Linear rotates it on each refresh
  await saveTokens(tokens.access_token, tokens.refresh_token);
  return tokens.access_token;
}
```

### Step 5: Validate Configuration on Startup
```typescript
function validateLinearConfig(): void {
  const key = process.env.LINEAR_API_KEY;
  if (!key) throw new Error("LINEAR_API_KEY environment variable is required");
  if (!key.startsWith("lin_api_")) throw new Error("LINEAR_API_KEY must start with lin_api_");
  if (key.length < 30) throw new Error("LINEAR_API_KEY appears truncated");
}

// Call before creating client
validateLinearConfig();
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Authentication required` | Invalid, expired, or missing API key | Regenerate at Settings > Account > API |
| `Invalid API key format` | Key doesn't start with `lin_api_` | Copy full key from Linear (shown once) |
| `Forbidden` | Token lacks required OAuth scope | Re-authorize with correct scopes |
| `invalid_grant` on token exchange | Code expired or PKCE verifier mismatch | Restart OAuth flow; codes expire quickly |
| `Module not found: @linear/sdk` | SDK not installed | Run `npm install @linear/sdk` |
| `ENOTFOUND api.linear.app` | DNS/firewall issue | Ensure outbound HTTPS to `api.linear.app` |

## Examples

### Raw GraphQL Without SDK
```typescript
const response = await fetch("https://api.linear.app/graphql", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": process.env.LINEAR_API_KEY!,
  },
  body: JSON.stringify({
    query: `{ viewer { id name email } }`,
  }),
});

const { data, errors } = await response.json();
if (errors) console.error("GraphQL errors:", errors);
else console.log("Viewer:", data.viewer);
```

### Server-to-Server (Client Credentials)
```typescript
// For apps without user interaction — uses client_credentials grant
const response = await fetch("https://api.linear.app/oauth/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({
    grant_type: "client_credentials",
    client_id: process.env.LINEAR_CLIENT_ID!,
    client_secret: process.env.LINEAR_CLIENT_SECRET!,
    scope: "read,write",
  }),
});

const { access_token } = await response.json();
const client = new LinearClient({ accessToken: access_token });
```

## Resources
- [Linear SDK Getting Started](https://linear.app/developers/sdk)
- [OAuth 2.0 Authentication](https://linear.app/developers/oauth-2-0-authentication)
- [GraphQL API Endpoint](https://linear.app/developers/graphql)
- [Apollo Studio Schema Explorer](https://studio.apollographql.com/public/Linear-API/variant/current/schema/reference)
