---
name: customerio-install-auth
description: |
  Install and configure Customer.io SDK/CLI authentication.
  Use when setting up a new Customer.io integration, configuring API keys,
  or initializing Customer.io in your project.
  Trigger: "install customer.io", "setup customer.io", "customer.io auth",
  "configure customer.io API key", "customer.io credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, api, authentication, setup]

---
# Customer.io Install & Auth

## Overview

Set up the `customerio-node` SDK and configure authentication for Customer.io's two API surfaces: the **Track API** (identify users, track events) and the **App API** (transactional messages, broadcasts, data queries).

## Prerequisites

- Node.js 18+ with npm/pnpm
- Customer.io account at https://fly.customer.io
- **Site ID** + **Track API Key** from Settings > Workspace Settings > API & Webhook Credentials
- **App API Key** (bearer token) from the same page — needed for transactional messages and broadcasts

## Two API Keys, Two Clients

| Client | Auth Method | Key Source | Use For |
|--------|-------------|-----------|---------|
| `TrackClient` | Basic Auth (Site ID + API Key) | Track API credentials | `identify()`, `track()`, `trackAnonymous()`, `suppress()`, `destroy()` |
| `APIClient` | Bearer Token (App API Key) | App API credentials | `sendEmail()`, `sendPush()`, `triggerBroadcast()` |

## Instructions

### Step 1: Install the SDK

```bash
npm install customerio-node
```

The package exports `TrackClient`, `APIClient`, `RegionUS`, `RegionEU`, `SendEmailRequest`, and `SendPushRequest`.

### Step 2: Configure Environment Variables

```bash
# .env — NEVER commit this file
CUSTOMERIO_SITE_ID=your-site-id-here
CUSTOMERIO_TRACK_API_KEY=your-track-api-key-here
CUSTOMERIO_APP_API_KEY=your-app-api-key-here
CUSTOMERIO_REGION=us          # "us" or "eu"
```

Add `.env` to `.gitignore` if not already there.

### Step 3: Create the Track Client

```typescript
// lib/customerio.ts
import { TrackClient, RegionUS, RegionEU } from "customerio-node";

function getRegion() {
  return process.env.CUSTOMERIO_REGION === "eu" ? RegionEU : RegionUS;
}

// Singleton — reuse across your app
let trackClient: TrackClient | null = null;

export function getTrackClient(): TrackClient {
  if (!trackClient) {
    const siteId = process.env.CUSTOMERIO_SITE_ID;
    const apiKey = process.env.CUSTOMERIO_TRACK_API_KEY;
    if (!siteId || !apiKey) {
      throw new Error(
        "Missing CUSTOMERIO_SITE_ID or CUSTOMERIO_TRACK_API_KEY"
      );
    }
    trackClient = new TrackClient(siteId, apiKey, { region: getRegion() });
  }
  return trackClient;
}
```

### Step 4: Create the App API Client

```typescript
// lib/customerio-app.ts
import { APIClient, RegionUS, RegionEU } from "customerio-node";

let appClient: APIClient | null = null;

export function getAppClient(): APIClient {
  if (!appClient) {
    const appKey = process.env.CUSTOMERIO_APP_API_KEY;
    if (!appKey) {
      throw new Error("Missing CUSTOMERIO_APP_API_KEY");
    }
    const region =
      process.env.CUSTOMERIO_REGION === "eu" ? RegionEU : RegionUS;
    appClient = new APIClient(appKey, { region });
  }
  return appClient;
}
```

### Step 5: Verify Connection

```typescript
// scripts/verify-customerio.ts
import { getTrackClient } from "../lib/customerio";

async function verify() {
  const cio = getTrackClient();
  try {
    // Identify a test user — if credentials are wrong, this throws
    await cio.identify("test-verify-user", {
      email: "verify@example.com",
      created_at: Math.floor(Date.now() / 1000),
    });
    console.log("Customer.io connection verified successfully");
    // Clean up: suppress the test user
    await cio.suppress("test-verify-user");
    console.log("Test user suppressed");
  } catch (err: any) {
    console.error("Connection failed:", err.statusCode, err.message);
    process.exit(1);
  }
}

verify();
```

Run with: `npx tsx scripts/verify-customerio.ts`

## Region Configuration

| Region | Track API Base URL | App API Base URL | SDK Constant |
|--------|--------------------|------------------|--------------|
| US | `https://track.customer.io` | `https://api.customer.io` | `RegionUS` |
| EU | `https://track-eu.customer.io` | `https://api-eu.customer.io` | `RegionEU` |

Your region is set when you create your Customer.io account. Check Settings > Workspace Settings to confirm. EU accounts **must** specify `RegionEU` or all API calls will fail with 401.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Wrong Site ID or Track API Key | Verify both values in Customer.io Settings > API & Webhook Credentials |
| `401` on App API | Wrong App API Key or using Track key | App API uses a different bearer token — check the App API key |
| `Region mismatch` | EU account using US endpoint | Set `CUSTOMERIO_REGION=eu` and use `RegionEU` |
| `ENOTFOUND` | DNS resolution failure | Check network, proxy, or firewall blocking `track.customer.io` |
| `MODULE_NOT_FOUND` | SDK not installed | Run `npm install customerio-node` |

## Security Notes

- Store credentials in a secrets manager (GCP Secret Manager, AWS SSM, Vault) for production
- Track API Key can identify/track users but cannot send messages — lower risk
- App API Key can send messages and access data — treat as highly sensitive
- Rotate keys every 90 days via Settings > API & Webhook Credentials > Regenerate

## Resources

- [Managing API Credentials](https://docs.customer.io/accounts-and-workspaces/managing-credentials/)
- [Account Regions (US and EU)](https://docs.customer.io/accounts-and-workspaces/data-centers/)
- [Track API Reference](https://docs.customer.io/integrations/api/track/)
- [App API Reference](https://docs.customer.io/integrations/api/app/)
- [customerio-node on GitHub](https://github.com/customerio/customerio-node)

## Next Steps

After successful auth, proceed to `customerio-hello-world` for your first identify + track call.
