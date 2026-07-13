---
name: hubspot-auth
description: Authenticate production HubSpot integrations and survive the auth-side
  failures — 30-min token expiry storms, 500K daily rate-limit burnout, scope drift,
  token leakage in commits, multi-portal credential routing, OAuth refresh-token decay.
  Use when hardening token caching, rotating private app credentials, building a multi-portal
  credential router, or recovering from 429/403 auth cascades. Trigger with "hubspot
  auth", "hubspot token cache", "hubspot rate limit", "hubspot scope drift", "hubspot
  multi-portal", "hubspot OAuth refresh".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(openssl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - oauth2
  - authentication
  - token-management
  - rate-limits
  - multi-portal
---

# HubSpot Auth

## Overview

Authenticate a service to HubSpot and operate the auth layer in production. This is not a setup walkthrough — it is the auth code your integration runs at 3am when an OAuth token expires mid-batch, when a portal admin removes a scope, when an agency credential router sends a request to the wrong portal, and when on-call needs to rotate a leaked private-app token without dropping in-flight requests.

The six production failures this skill prevents:

1. **Token expiry storms** — OAuth access tokens expire in 1800 seconds. Every concurrent request notices expiry simultaneously, races to refresh, the token endpoint rate-limits at 10 auth calls/10s, the integration cascades to red.
2. **Daily rate-limit burnout** — retry storms on auth failures burn through the 500K daily API call quota before noon. Exponential backoff with jitter is non-optional.
3. **Scope drift** — a portal admin edits the private app's scopes or a connected OAuth app loses authorization. Cached tokens start returning `403`. Retrying does not help.
4. **Token leakage in commits** — `pat-na1-*` private-app tokens are wide-scope and not auto-expiring. A single leaked commit exposes the entire portal.
5. **Multi-portal credential routing** — agencies managing 50+ portals cannot use a single `HUBSPOT_ACCESS_TOKEN`. Requests sent to the wrong portal silently operate on the wrong data.
6. **OAuth refresh-token decay** — HubSpot refresh tokens expire after one year of non-use. Integrations that go idle (seasonal products, paused automations) silently lose access and require user reconnection.

## Prerequisites

- Node.js 18+ (examples) or Python 3.10+
- HubSpot account with a private app **or** a connected OAuth public app
- For private apps: token from Settings → Integrations → Private Apps → your app → Auth tab
- For OAuth: client ID + secret from developer portal, redirect URI registered
- A secret store the runtime can read at startup and on rotation signal (env var, AWS Secrets Manager, GCP Secret Manager, or equivalent)

## Instructions

Build in this order. Each section neutralizes one production failure mode.

### 1. Token-cache pattern (neutralizes expiry storms)

Reactive refresh on `401` is wrong. It doubles latency on the failing request and creates a thundering herd when all concurrent requests notice expiry at the same millisecond. Cache the token in-process and refresh **proactively** at 80% of TTL, behind a single-flight gate so concurrent callers serialize on one refresh.

This pattern applies to **OAuth access tokens only** — private-app tokens do not expire.

```typescript
type Cached = { value: string; expiresAt: number };
let cached: Cached | null = null;
let inflight: Promise<string> | null = null;

export async function getToken(): Promise<string> {
  // Refresh at 80% of TTL (1800s → refresh at 1440s elapsed, i.e. 360s before expiry)
  if (cached && Date.now() < cached.expiresAt - 360_000) return cached.value;
  if (inflight) return inflight;

  inflight = (async () => {
    const res = await fetch("https://api.hubapi.com/oauth/v1/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: process.env.HUBSPOT_CLIENT_ID!,
        client_secret: process.env.HUBSPOT_CLIENT_SECRET!,
        redirect_uri: process.env.HUBSPOT_REDIRECT_URI!,
        refresh_token: await loadRefreshToken(), // read from secret store
      }),
    });
    if (!res.ok) throw new HubSpotAuthError(res.status, await res.text());
    const { access_token, expires_in } = await res.json();
    cached = {
      value: access_token,
      expiresAt: Date.now() + expires_in * 1000,
    };
    return access_token;
  })().finally(() => { inflight = null; });

  return inflight;
}

class HubSpotAuthError extends Error {
  constructor(public status: number, public body: string) {
    super(`HubSpot auth failed ${status}: ${body}`);
  }
}
```

### 2. Exponential backoff with jitter (neutralizes rate-limit burnout)

HubSpot enforces 10 auth calls/10s on the token endpoint and 100 API calls/10s per private app. Naive retry on failure burns both budgets instantly.

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 4,
  baseDelayMs = 500,
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      const isRetryable =
        err.status === 429 ||
        (err.status >= 500 && err.status < 600);

      if (!isRetryable || attempt === maxAttempts) throw err;

      // Full jitter: random delay in [0, min(cap, base * 2^attempt)]
      const cap = 30_000;
      const expDelay = Math.min(cap, baseDelayMs * 2 ** attempt);
      const jittered = Math.random() * expDelay;

      // Respect Retry-After if present
      const retryAfterMs = err.retryAfterSeconds
        ? err.retryAfterSeconds * 1000
        : jittered;

      await new Promise((r) => setTimeout(r, retryAfterMs));
    }
  }
  throw new Error("unreachable");
}

// Usage
const token = await withRetry(() => getToken());
```

### 3. Scope validation on refresh (neutralizes scope drift)

When a portal admin edits scopes, your next token refresh silently returns a token with the new (reduced) scope set. Requests fail with `403` and no retry will help. Validate scopes immediately after each refresh:

```typescript
const REQUIRED_SCOPES = new Set([
  "crm.objects.contacts.read",
  "crm.objects.contacts.write",
  "crm.objects.deals.read",
]);

function validateScopes(tokenBody: any): void {
  const granted = new Set((tokenBody.scope as string).split(" "));
  const missing = [...REQUIRED_SCOPES].filter((s) => !granted.has(s));
  if (missing.length > 0) {
    throw new Error(`Scope drift detected — missing: ${missing.join(", ")}. ` +
      "A portal admin must re-grant these scopes in Private Apps settings.");
  }
}

// Call inside the token refresh:
const body = await res.json();
validateScopes(body);
cached = { value: body.access_token, expiresAt: Date.now() + body.expires_in * 1000 };
```

### 4. Secret management and leak prevention (neutralizes token leakage)

Private-app tokens (`pat-na1-*`) are wide-scope and do not auto-expire. A leaked token can read and write the entire portal until manually rotated.

**Never put tokens in source code, `.env` files committed to git, or log output.**

```bash
# .gitignore — add these if not present
.env
.env.local
.env.*.local
*.pat
hubspot-credentials.json

# Verify no token is already committed
git log --all --full-history --oneline -- .env
git grep -r "pat-na1" -- '*.ts' '*.js' '*.py' '*.json'
git grep -r "HUBSPOT_ACCESS_TOKEN\s*=" -- '*.ts' '*.js'
```

For rotation without downtime:

1. Create a **new** private app (or rotate the token in the existing app — HubSpot generates a new token, old is immediately revoked).
2. Load the new token into your secret store.
3. Signal the running process to reload (SIGHUP, env var change trigger, or restart).
4. Verify the new token with a cheap read call before declaring success.

```typescript
// Health check — cheap read to verify token is live
async function verifyToken(token: string): Promise<boolean> {
  const res = await fetch("https://api.hubapi.com/crm/v3/objects/contacts?limit=1", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.status === 200 || res.status === 204;
}
```

### 5. Multi-portal credential router (neutralizes wrong-portal routing)

Agencies and ISVs managing multiple HubSpot portals need per-portal token caches, not a single env var. Requests sent to the wrong portal silently operate on the wrong data with no error.

```typescript
// credentials.json (in secret store, NOT in git)
// { "portals": { "acme-corp": "pat-na1-...", "beta-inc": "pat-na1-..." } }

class HubSpotRouter {
  private caches = new Map<string, { value: string; expiresAt: number }>();
  private credentials: Record<string, string>;

  constructor(credentials: Record<string, string>) {
    this.credentials = credentials;
  }

  async getClient(portalSlug: string): Promise<{ token: string }> {
    const cached = this.caches.get(portalSlug);
    // Private-app tokens don't expire — still cache to avoid repeated lookups
    if (cached) return { token: cached.value };

    const token = this.credentials[portalSlug];
    if (!token) throw new Error(`No credential for portal: ${portalSlug}`);

    // Verify the token is live before caching
    const ok = await verifyToken(token);
    if (!ok) throw new Error(`Token for portal ${portalSlug} is invalid or revoked`);

    this.caches.set(portalSlug, { value: token, expiresAt: Infinity });
    return { token };
  }
}

// Load credentials from secret store at startup
const creds = JSON.parse(await readSecret("hubspot/portal-credentials"));
const router = new HubSpotRouter(creds.portals);

// Usage
const { token } = await router.getClient("acme-corp");
```

### 6. Refresh-token decay detection (neutralizes silent access loss)

HubSpot refresh tokens expire after 525,600 minutes (1 year) of non-use. Integrations with seasonal usage patterns or paused automations will silently lose access.

```typescript
// Store last-used timestamp alongside the refresh token
interface RefreshTokenRecord {
  token: string;
  lastUsed: number; // Unix ms
}

const REFRESH_TOKEN_WARN_DAYS = 300; // warn at 300d, expire at 365d

async function loadRefreshToken(): Promise<string> {
  const record: RefreshTokenRecord = JSON.parse(
    await readSecret("hubspot/refresh-token")
  );

  const ageDays = (Date.now() - record.lastUsed) / 86_400_000;
  if (ageDays > REFRESH_TOKEN_WARN_DAYS) {
    console.warn(
      `HubSpot refresh token unused for ${ageDays.toFixed(0)} days — ` +
      "reconnect the OAuth app before day 365 or access will be lost."
    );
  }

  // Update last-used timestamp
  await writeSecret("hubspot/refresh-token", JSON.stringify({
    ...record,
    lastUsed: Date.now(),
  }));

  return record.token;
}
```

## Error Handling

| HTTP Status | HubSpot Error | Root Cause | Action |
|---|---|---|---|
| `401 UNAUTHORIZED` | `INVALID_AUTHENTICATION` | Token expired, revoked, or malformed | Refresh or re-rotate token |
| `403 FORBIDDEN` | `MISSING_SCOPES` | Scope removed from private app | Portal admin re-grants scopes |
| `429 TOO_MANY_REQUESTS` | `RATE_LIMIT` | Auth or API quota exhausted | Back off with `Retry-After` header |
| `400 BAD_REQUEST` | `INVALID_CLIENT` | Wrong client ID/secret on token request | Verify credentials in dev portal |
| `400 BAD_REQUEST` | `REFRESH_TOKEN_NOT_FOUND` | Refresh token expired or revoked | User must reconnect OAuth app |

## Output

- Token-cache module with proactive refresh at 80% TTL
- Exponential backoff with jitter wired to every auth and API call
- Scope validation that fails fast on drift
- `.gitignore` verified for token leakage patterns
- Multi-portal credential router (if managing >1 portal)
- Refresh-token decay monitor logging warnings at 300-day mark

## Examples

### Minimal private-app client (TypeScript)

```typescript
import * as hubspot from "@hubspot/api-client";

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

const contacts = await client.crm.contacts.basicApi.getPage(10);
```

### Token-cache wired to an HTTP client

```typescript
// Every outbound call goes through getToken() — cache handles the rest
async function hubspotFetch(path: string, init?: RequestInit) {
  const token = await getToken();
  return fetch(`https://api.hubapi.com${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, ...init?.headers },
  });
}
```

### Verify credentials before going live

```bash
curl -s "https://api.hubapi.com/oauth/v1/access-tokens/$HUBSPOT_ACCESS_TOKEN" | jq '{hub_id, user, scopes}'
```

## Resources

- [HubSpot Private Apps Guide](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)
- [OAuth 2.0 Guide](https://developers.hubspot.com/docs/guides/apps/authentication/oauth)
- [Scopes Reference](https://developers.hubspot.com/docs/guides/apps/authentication/scopes)
- [@hubspot/api-client on npm](https://www.npmjs.com/package/@hubspot/api-client)
- [Rate Limits Reference](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [API_REFERENCE.md](references/API_REFERENCE.md) — auth endpoint shapes, scope catalog, rate limit headers
- [implementation-guide.md](references/implementation-guide.md) — Python equivalents, secret store integrations, rotation runbook
