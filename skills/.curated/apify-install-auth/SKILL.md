---
name: apify-install-auth
description: 'Install and configure Apify SDK, CLI, and API client authentication.

  Use when setting up a new Apify project, configuring API tokens,

  or initializing apify-client / Apify SDK in your codebase.

  Trigger with "install apify", "setup apify", "apify auth", "configure apify token".

  '
allowed-tools: Read, Write, Bash(npm:*), Bash(npx:*), Bash(apify:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Install & Auth

## Overview

Set up the Apify ecosystem: the `apify-client` JS library (for calling Actors remotely), the `apify` SDK (for building Actors), the Apify CLI (for deploying), and Crawlee (for crawling). Each package serves a different purpose — install only what the task needs, then wire up a single API token.

## Package Map

| Package | npm | Purpose |
|---------|-----|---------|
| `apify-client` | `npm i apify-client` | Call Actors, manage datasets/KV stores from external apps |
| `apify` | `npm i apify` | Build Actors (includes `Actor.init()`, `Actor.pushData()`) |
| `crawlee` | `npm i crawlee` | Crawler framework (Cheerio, Playwright, Puppeteer crawlers) |
| `apify-cli` | `npm i -g apify-cli` | CLI for `apify login`, `apify run`, `apify push` |

## Prerequisites

- Node.js 18+ (required by SDK v3+)
- Apify account at https://console.apify.com
- API token from Settings > Integrations in Apify Console

## Instructions

### Step 1: Install Packages

```bash
# For CALLING existing Actors from your app:
npm install apify-client

# For BUILDING your own Actors:
npm install apify crawlee

# For CLI deployment:
npm install -g apify-cli
```

### Step 2: Configure Authentication

Pick one. Read any existing `.env` first so you do not clobber it, then Write the token in.

```bash
# Option A: Environment variable (recommended for apps)
export APIFY_TOKEN="apify_api_YOUR_TOKEN_HERE"

# Option B: .env file (add .env to .gitignore)
echo 'APIFY_TOKEN=apify_api_YOUR_TOKEN_HERE' >> .env

# Option C: CLI login (for interactive development)
apify login
# Paste your token when prompted
```

The `APIFY_TOKEN` env var is auto-detected by both `apify-client` and the `apify` SDK. For every place a token can be supplied (constructor option, header, precedence) plus the full platform env-var list, see [authentication reference](references/authentication.md).

### Step 3: Verify Connection

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// List your Actors to confirm auth works
const { items } = await client.actors().list();
console.log(`Authenticated. You have ${items.length} Actors.`);
```

### Step 4: Verify CLI (if installed)

```bash
apify login --token YOUR_TOKEN
apify info  # Shows your account info
```

## Output

A working, authenticated Apify setup:

- The needed packages installed in `node_modules` (verify with `npm ls apify-client`).
- `APIFY_TOKEN` available to the process — via a Write to `.env`, an exported shell var, or `apify login` credentials in `~/.apify/auth.json`.
- The Step 3 snippet printing `Authenticated. You have N Actors.` — proof the token reaches the API.
- `apify info` showing your account (only when the CLI was installed in Step 1).

If the verify snippet throws instead of printing the count, jump to Error Handling below.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Regenerate token in Console > Settings > Integrations |
| `Cannot find module 'apify-client'` | Package not installed | `npm install apify-client` |
| `APIFY_TOKEN is not set` | Missing env var | Export `APIFY_TOKEN` or pass `token` to constructor |
| `apify: command not found` | CLI not installed globally | `npm install -g apify-cli` |

## Examples

The essential singleton-client skeleton:

```typescript
// src/apify/client.ts
import { ApifyClient } from 'apify-client';
import 'dotenv/config';

let client: ApifyClient | null = null;

export function getClient(): ApifyClient {
  if (!client) {
    if (!process.env.APIFY_TOKEN) {
      throw new Error('APIFY_TOKEN environment variable is required');
    }
    client = new ApifyClient({ token: process.env.APIFY_TOKEN });
  }
  return client;
}
```

For the full worked set — the `.env.example` template, the verify snippet, and CLI verification — see [worked examples](references/examples.md).

## Resources

- [Apify Console — API Tokens](https://console.apify.com/account/integrations)
- [JS Client Quick Start](https://docs.apify.com/api/client/js/docs/introduction/quick-start)
- [Apify CLI Reference](https://docs.apify.com/cli/docs/reference)
- [SDK for JavaScript](https://docs.apify.com/sdk/js)

## Next Steps

With the client authenticated, proceed to `apify-hello-world` to make your first
Actor call and push results to a dataset. If you are building your own Actor
instead of calling one, the `apify` SDK and Crawlee installed above are your
starting point — deploy with `apify push`.
