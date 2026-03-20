---
name: linear-security-basics
description: |
  Secure API key management and OAuth best practices for Linear.
  Use when setting up authentication securely, implementing OAuth flows,
  or hardening Linear integrations.
  Trigger with phrases like "linear security", "linear API key security",
  "linear OAuth", "secure linear integration", "linear secrets management".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Security Basics

## Overview
Implement secure authentication and API key management for Linear integrations.

## Prerequisites
- Linear account with API access
- Understanding of environment variables
- Familiarity with OAuth 2.0 concepts

## Instructions

### Step 1: Secure API Key Storage

**Never hardcode API keys:**
```typescript
// BAD - Never do this!
const client = new LinearClient({
  apiKey: "lin_api_xxxxxxxxxxxx"  // Exposed in source code
});

// GOOD - Use environment variables
const client = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY!
});
```

**Environment Setup:**
```bash
# .env (never commit this file)
LINEAR_API_KEY=lin_api_xxxxxxxxxxxx

# .gitignore (commit this)
.env
.env.*
!.env.example

# .env.example (commit this for documentation)
LINEAR_API_KEY=lin_api_your_key_here
```

**Validate on Startup:**
```typescript
// config/linear.ts
function validateConfig(): void {
  const apiKey = process.env.LINEAR_API_KEY;

  if (!apiKey) {
    throw new Error("LINEAR_API_KEY environment variable is required");
  }

  if (!apiKey.startsWith("lin_api_")) {
    throw new Error("LINEAR_API_KEY has invalid format");
  }

  if (apiKey.length < 30) {
    throw new Error("LINEAR_API_KEY appears too short");
  }
}

validateConfig();
```

### Step 2: Implement OAuth 2.0 Flow

```typescript
// For user-facing applications
import express from "express";
import crypto from "crypto";

const app = express();

// OAuth configuration
const OAUTH_CONFIG = {
  clientId: process.env.LINEAR_CLIENT_ID!,
  clientSecret: process.env.LINEAR_CLIENT_SECRET!,
  redirectUri: process.env.LINEAR_REDIRECT_URI!,
  scope: ["read", "write", "issues:create"],
};

// Step 1: Initiate OAuth
app.get("/auth/linear", (req, res) => {
  const state = crypto.randomBytes(16).toString("hex");
  req.session!.oauthState = state;

  const authUrl = new URL("https://linear.app/oauth/authorize");
  authUrl.searchParams.set("client_id", OAUTH_CONFIG.clientId);
  authUrl.searchParams.set("redirect_uri", OAUTH_CONFIG.redirectUri);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("scope", OAUTH_CONFIG.scope.join(","));
  authUrl.searchParams.set("state", state);

  res.redirect(authUrl.toString());
});

// Step 2: Handle callback
app.get("/auth/linear/callback", async (req, res) => {
  const { code, state } = req.query;

  // Verify state to prevent CSRF
  if (state !== req.session!.oauthState) {
    return res.status(400).json({ error: "Invalid state parameter" });  # HTTP 400 Bad Request
  }

  // Exchange code for tokens
  const response = await fetch("https://api.linear.app/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: code as string,
      client_id: OAUTH_CONFIG.clientId,
      client_secret: OAUTH_CONFIG.clientSecret,
      redirect_uri: OAUTH_CONFIG.redirectUri,
    }),
  });

  const tokens = await response.json();

  // Store tokens securely (encrypted in database)
  await storeTokens(req.user!.id, {
    accessToken: encrypt(tokens.access_token),
    refreshToken: encrypt(tokens.refresh_token),
    expiresAt: new Date(Date.now() + tokens.expires_in * 1000),  # 1000: 1 second in ms
  });

  res.redirect("/dashboard");
});
```

### Step 3: Token Refresh Flow
```typescript
async function getValidAccessToken(userId: string): Promise<string> {
  const stored = await getStoredTokens(userId);

  // Check if token is expired or expiring soon (5 min buffer)
  if (stored.expiresAt.getTime() - Date.now() < 5 * 60 * 1000) {  # 1000: 1 second in ms
    const response = await fetch("https://api.linear.app/oauth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        refresh_token: decrypt(stored.refreshToken),
        client_id: process.env.LINEAR_CLIENT_ID!,
        client_secret: process.env.LINEAR_CLIENT_SECRET!,
      }),
    });

    const tokens = await response.json();

    await storeTokens(userId, {
      accessToken: encrypt(tokens.access_token),
      refreshToken: encrypt(tokens.refresh_token),
      expiresAt: new Date(Date.now() + tokens.expires_in * 1000),  # 1 second in ms
    });

    return tokens.access_token;
  }

  return decrypt(stored.accessToken);
}
```

### Step 4: Webhook Signature Verification
```typescript
import crypto from "crypto";

function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expectedSignature = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  // Use timing-safe comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

// Express middleware
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const signature = req.headers["linear-signature"] as string;
  const payload = req.body.toString();

  if (!verifyWebhookSignature(payload, signature, process.env.LINEAR_WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: "Invalid signature" });  # HTTP 401 Unauthorized
  }

  const event = JSON.parse(payload);
  // Process verified webhook...
  res.status(200).json({ received: true });  # HTTP 200 OK
});
```

### Step 5: Secret Rotation
```typescript
// Support multiple API keys during rotation
const apiKeys = [
  process.env.LINEAR_API_KEY_NEW,
  process.env.LINEAR_API_KEY_OLD,
].filter(Boolean);

async function getWorkingClient(): Promise<LinearClient> {
  for (const apiKey of apiKeys) {
    try {
      const client = new LinearClient({ apiKey: apiKey! });
      await client.viewer; // Test the key
      return client;
    } catch {
      continue;
    }
  }
  throw new Error("No valid Linear API key found");
}
```

## Security Checklist
- [ ] API keys stored in environment variables only
- [ ] .env files in .gitignore
- [ ] OAuth state parameter validated
- [ ] Tokens encrypted at rest
- [ ] Token refresh implemented
- [ ] Webhook signatures verified
- [ ] HTTPS enforced for all endpoints
- [ ] API keys rotated periodically
- [ ] Minimal OAuth scopes requested

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid signature` | Webhook secret mismatch | Verify secret matches Linear settings |
| `Token expired` | Refresh token expired | Re-authorize user |
| `Invalid scope` | Missing permission | Request additional scopes |

## Resources
- [Linear OAuth Documentation](https://developers.linear.app/docs/oauth)
- [Webhook Security](https://developers.linear.app/docs/graphql/webhooks)
- [API Authentication](https://developers.linear.app/docs/graphql/authentication)

## Next Steps
Prepare for production with `linear-prod-checklist`.

## Output
- API key validation on startup catching invalid or missing keys
- OAuth 2.0 authorization flow with CSRF-safe state parameter
- Token refresh logic with encrypted storage
- HMAC-SHA256 webhook signature verification middleware
- Secret rotation support with multi-key fallback

## Examples

### Minimal Secure Setup
```typescript
// Quickest path to a secure Linear client
import { LinearClient } from "@linear/sdk";

if (!process.env.LINEAR_API_KEY?.startsWith("lin_api_")) {
  throw new Error("Set LINEAR_API_KEY (starts with lin_api_)");
}

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });
const me = await client.viewer;
console.log(`Connected as ${me.name}`);
```

### Test Webhook Signature Locally
```typescript
import crypto from "crypto";

const secret = "test-secret";
const payload = JSON.stringify({ action: "create", type: "Issue", data: {} });
const sig = crypto.createHmac("sha256", secret).update(payload).digest("hex");
console.log(`Signature: ${sig}`);
// Use this to test your verifyWebhookSignature function
console.log(`Valid: ${verifyWebhookSignature(payload, sig, secret)}`);
```