---
name: linear-security-basics
description: |
  Secure API key management, OAuth best practices, and webhook
  verification for Linear integrations.
  Trigger: "linear security", "linear API key security",
  "linear OAuth", "secure linear", "linear webhook verification",
  "linear secrets management", "linear token refresh".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, security, authentication]

---
# Linear Security Basics

## Overview
Secure authentication patterns for Linear integrations: API key management, OAuth 2.0 with PKCE, token refresh (mandatory for new apps after Oct 2025), webhook HMAC-SHA256 signature verification, and secret rotation.

## Prerequisites
- Linear account with API access
- Understanding of environment variables and secret management
- Familiarity with OAuth 2.0 and HMAC concepts

## Instructions

### Step 1: Secure API Key Storage
```typescript
// NEVER hardcode keys
// BAD:
// const client = new LinearClient({ apiKey: "lin_api_xxxx" });

// GOOD: environment variable
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY!,
});
```

**Environment setup:**
```bash
# .env (never commit)
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
LINEAR_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx

# .gitignore
.env
.env.*
!.env.example

# .env.example (commit for documentation)
LINEAR_API_KEY=lin_api_your_key_here
LINEAR_WEBHOOK_SECRET=your_webhook_secret_here
```

**Startup validation:**
```typescript
function validateConfig(): void {
  const key = process.env.LINEAR_API_KEY;
  if (!key) throw new Error("LINEAR_API_KEY is required");
  if (!key.startsWith("lin_api_")) throw new Error("LINEAR_API_KEY has invalid format");
  if (key.length < 30) throw new Error("LINEAR_API_KEY appears truncated");
}
validateConfig();
```

### Step 2: OAuth 2.0 with PKCE
```typescript
import express from "express";
import crypto from "crypto";

const app = express();

const OAUTH = {
  clientId: process.env.LINEAR_CLIENT_ID!,
  clientSecret: process.env.LINEAR_CLIENT_SECRET!,
  redirectUri: process.env.LINEAR_REDIRECT_URI!,
  scopes: ["read", "write", "issues:create"],
};

// Generate PKCE verifier and challenge
function generatePKCE() {
  const verifier = crypto.randomBytes(32).toString("base64url");
  const challenge = crypto.createHash("sha256").update(verifier).digest("base64url");
  return { verifier, challenge };
}

// Step 1: Redirect to Linear authorization
app.get("/auth/linear", (req, res) => {
  const state = crypto.randomBytes(16).toString("hex");
  const { verifier, challenge } = generatePKCE();

  // Store state + verifier in session
  req.session!.oauthState = state;
  req.session!.codeVerifier = verifier;

  const url = new URL("https://linear.app/oauth/authorize");
  url.searchParams.set("client_id", OAUTH.clientId);
  url.searchParams.set("redirect_uri", OAUTH.redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", OAUTH.scopes.join(","));
  url.searchParams.set("state", state);
  url.searchParams.set("code_challenge", challenge);
  url.searchParams.set("code_challenge_method", "S256");

  res.redirect(url.toString());
});

// Step 2: Handle callback — exchange code for tokens
app.get("/auth/linear/callback", async (req, res) => {
  const { code, state } = req.query;

  // CSRF check
  if (state !== req.session!.oauthState) {
    return res.status(400).json({ error: "Invalid state parameter" });
  }

  const response = await fetch("https://api.linear.app/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: code as string,
      client_id: OAUTH.clientId,
      client_secret: OAUTH.clientSecret,
      redirect_uri: OAUTH.redirectUri,
      code_verifier: req.session!.codeVerifier,
    }),
  });

  const tokens = await response.json();

  // Store tokens securely (encrypt at rest)
  await storeTokens(req.user!.id, {
    accessToken: encrypt(tokens.access_token),
    refreshToken: encrypt(tokens.refresh_token),
    expiresAt: new Date(Date.now() + tokens.expires_in * 1000),
  });

  res.redirect("/dashboard");
});
```

### Step 3: Token Refresh
As of Oct 2025, all new Linear OAuth apps issue refresh tokens. Existing apps must migrate by April 2026.

```typescript
async function getValidToken(userId: string): Promise<string> {
  const stored = await getStoredTokens(userId);

  // Refresh if expired or expiring within 5 minutes
  if (stored.expiresAt.getTime() - Date.now() < 5 * 60 * 1000) {
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

    if (!response.ok) throw new Error(`Token refresh failed: ${response.status}`);
    const tokens = await response.json();

    // Linear rotates refresh tokens — always store the new one
    await storeTokens(userId, {
      accessToken: encrypt(tokens.access_token),
      refreshToken: encrypt(tokens.refresh_token),
      expiresAt: new Date(Date.now() + tokens.expires_in * 1000),
    });

    return tokens.access_token;
  }

  return decrypt(stored.accessToken);
}
```

### Step 4: Webhook Signature Verification
Linear signs every webhook with HMAC-SHA256 using the webhook's signing secret. The signature is in the `Linear-Signature` header.

```typescript
import crypto from "crypto";

function verifyWebhookSignature(
  rawBody: string,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("hex");

  // Timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false; // Length mismatch
  }
}

// Express middleware — must use raw body parser
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const signature = req.headers["linear-signature"] as string;
  const rawBody = req.body.toString();

  if (!verifyWebhookSignature(rawBody, signature, process.env.LINEAR_WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  // Verify webhook timestamp (guard against replay attacks)
  const event = JSON.parse(rawBody);
  const age = Date.now() - event.webhookTimestamp;
  if (age > 60000) {
    return res.status(400).json({ error: "Webhook too old" });
  }

  processEvent(event).catch(console.error);
  res.json({ received: true });
});
```

### Step 5: Secret Rotation
```typescript
// Support multiple keys during rotation period
const apiKeys = [
  process.env.LINEAR_API_KEY_NEW,
  process.env.LINEAR_API_KEY_OLD,
].filter(Boolean) as string[];

async function getWorkingClient(): Promise<LinearClient> {
  for (const apiKey of apiKeys) {
    try {
      const client = new LinearClient({ apiKey });
      await client.viewer; // Verify key works
      return client;
    } catch {
      continue;
    }
  }
  throw new Error("No valid Linear API key found");
}
```

## Security Checklist
- [ ] API keys in environment variables only (never in code)
- [ ] `.env` files in `.gitignore`
- [ ] OAuth state parameter validated (CSRF protection)
- [ ] PKCE used for public/mobile clients
- [ ] Tokens encrypted at rest in database
- [ ] Token refresh implemented (mandatory for new apps)
- [ ] Webhook signatures verified with `crypto.timingSafeEqual`
- [ ] Webhook timestamp checked (< 60s age)
- [ ] HTTPS enforced on all endpoints
- [ ] Minimal OAuth scopes requested
- [ ] API keys rotated quarterly

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid signature` | Webhook secret mismatch | Verify `LINEAR_WEBHOOK_SECRET` in Linear Settings > API > Webhooks |
| `invalid_grant` | Refresh token expired/revoked | Re-initiate full OAuth flow |
| `Invalid scope` | App not authorized for scope | Request only scopes your app needs |
| `Authentication required` | Token expired, refresh failed | Trigger re-authentication |

## Examples

### Test Webhook Signature Locally
```typescript
import crypto from "crypto";

const secret = "test-signing-secret";
const payload = JSON.stringify({
  action: "create",
  type: "Issue",
  data: { id: "test", title: "Test" },
  webhookTimestamp: Date.now(),
});
const sig = crypto.createHmac("sha256", secret).update(payload).digest("hex");
console.log(`Signature: ${sig}`);
console.log(`Valid: ${verifyWebhookSignature(payload, sig, secret)}`);
```

## Resources
- [OAuth 2.0 Authentication](https://linear.app/developers/oauth-2-0-authentication)
- [OAuth Actor Authorization](https://linear.app/developers/oauth-actor-authorization)
- [Webhooks Documentation](https://linear.app/developers/webhooks)
- [API Settings](https://linear.app/settings/api)
