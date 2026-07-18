---
name: intercom-install-auth
description: |
  Install and configure Intercom API authentication with access tokens or OAuth.
  Use when setting up a new Intercom integration, configuring API credentials,
  or initializing the intercom-client SDK in your project.
  Trigger with phrases like "install intercom", "setup intercom",
  "intercom auth", "configure intercom API key", "intercom access token".
allowed-tools: Write, Bash(npm:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Install & Auth

## Overview

Set up the official `intercom-client` TypeScript SDK and configure authentication via access tokens (private apps) or OAuth (public apps). This skill installs the SDK with a Bash npm command, uses Write to create the client config and `.env`, and verifies the connection.

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

Access tokens authenticate private apps that access your own Intercom workspace. Use Write to create the client module and a `.env` holding the token (add `.env` to `.gitignore`):

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});
```

See [examples.md](references/examples.md) for the full `.env` setup and secure-storage steps.

### Step 3: Verify Connection

List admins to confirm the token authenticates end-to-end:

```typescript
const admins = await client.admins.list();
console.log("Connected! Admins:", admins.admins.length);
```

The complete verification function (with error handling and expected output) is in [examples.md](references/examples.md).

### Step 4: OAuth Setup (Public Apps)

For a **public app** that accesses other workspaces, run the OAuth authorization → token-exchange flow, then initialize the client with the returned token:

```typescript
const client = new IntercomClient({ token: oauthToken });
```

Full OAuth exchange, API-version pinning, and the scope matrix are in [oauth.md](references/oauth.md).

## Output

Running this skill produces:

- `intercom-client` installed in `node_modules` and added to `package.json`.
- A configured `IntercomClient` module authenticated via access token or OAuth.
- A `.env` holding `INTERCOM_ACCESS_TOKEN` (private app) or `INTERCOM_CLIENT_ID` / `INTERCOM_CLIENT_SECRET` (OAuth), with `.env` gitignored.
- A verified connection — `client.admins.list()` returns your workspace admins, confirming the token and API version (**2.11**, applied automatically by the SDK) are correct.

## Error Handling

Common authentication failures and fixes:

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `unauthorized` | 401 | Invalid or expired token | Regenerate in Developer Hub |
| `forbidden` | 403 | Missing OAuth scope | Add required scope in app config |
| `token_revoked` | 401 | Token was revoked | Generate new access token |
| `invalid_grant` | 400 | OAuth code expired | Restart OAuth flow |

Catch `IntercomError` to branch on `statusCode` — the full typed pattern is in [error-handling.md](references/error-handling.md).

## Examples

See [examples.md](references/examples.md) for three worked setups: the access-token client (private app, the common path), a connection-verify function with expected output, and an OAuth client (public app).

Minimal working setup:

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });
const admins = await client.admins.list();
console.log("Connected! Admins:", admins.admins.length);
```

## Resources

- [OAuth, versioning & scopes](references/oauth.md) — public-app deep dive.
- [Error handling reference](references/error-handling.md) — full error matrix.
- [Worked examples](references/examples.md) — copy-paste setups.
- [Authentication Guide](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [OAuth Scopes](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/oauth-scopes)
- [Setting up OAuth](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/setting-up-oauth)
- [intercom-client npm](https://www.npmjs.com/package/intercom-client)

## Next Steps

After successful authentication, proceed to the `intercom-hello-world` skill to make your first API call — create a contact, then fetch it back to confirm read and write both work with your configured client.
