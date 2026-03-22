---
name: apify-install-auth
description: |
  Install and configure Apify SDK, CLI, and API client authentication.
  Use when setting up a new Apify project, configuring API tokens,
  or initializing apify-client / Apify SDK in your codebase.
  Trigger: "install apify", "setup apify", "apify auth", "configure apify token".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(apify:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Install & Auth

## Overview

Set up the Apify ecosystem: the `apify-client` JS library (for calling Actors remotely), the `apify` SDK (for building Actors), the Apify CLI (for deploying), and Crawlee (for crawling). Each package serves a different purpose.

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

```bash
# Option A: Environment variable (recommended for apps)
export APIFY_TOKEN="apify_api_YOUR_TOKEN_HERE"

# Option B: .env file (add .env to .gitignore)
echo 'APIFY_TOKEN=apify_api_YOUR_TOKEN_HERE' >> .env

# Option C: CLI login (for interactive development)
apify login
# Paste your token when prompted
```

### Step 3: Verify Connection

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({
  token: process.env.APIFY_TOKEN,
});

// List your Actors to confirm auth works
const { items } = await client.actors().list();
console.log(`Authenticated. You have ${items.length} Actors.`);
```

### Step 4: Verify CLI (if installed)

```bash
apify login --token YOUR_TOKEN
apify info  # Shows your account info
```

## Auth Token Details

- Token format: `apify_api_` prefix followed by alphanumeric string
- Pass via `Authorization: Bearer <token>` header (REST API)
- Pass via `token` constructor option (JS client)
- The `APIFY_TOKEN` env var is auto-detected by both `apify-client` and `apify` SDK

## Environment Variable Reference

| Variable | Purpose |
|----------|---------|
| `APIFY_TOKEN` | API authentication (primary) |
| `APIFY_PROXY_PASSWORD` | Proxy access (auto-set on platform) |
| `APIFY_IS_AT_HOME` | `true` when running on Apify platform |
| `APIFY_DEFAULT_DATASET_ID` | Default dataset for current run |
| `APIFY_DEFAULT_KEY_VALUE_STORE_ID` | Default KV store for current run |
| `APIFY_DEFAULT_REQUEST_QUEUE_ID` | Default request queue for current run |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Regenerate token in Console > Settings > Integrations |
| `Cannot find module 'apify-client'` | Package not installed | `npm install apify-client` |
| `APIFY_TOKEN is not set` | Missing env var | Export `APIFY_TOKEN` or pass `token` to constructor |
| `apify: command not found` | CLI not installed globally | `npm install -g apify-cli` |

## Examples

### TypeScript Project Setup

```typescript
// src/apify/client.ts
import { ApifyClient } from 'apify-client';
import 'dotenv/config'; // npm install dotenv

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

### .env.example Template

```bash
# Apify — get your token at https://console.apify.com/account/integrations
APIFY_TOKEN=apify_api_REPLACE_ME
```

## Resources

- [Apify Console — API Tokens](https://console.apify.com/account/integrations)
- [JS Client Quick Start](https://docs.apify.com/api/client/js/docs/introduction/quick-start)
- [Apify CLI Reference](https://docs.apify.com/cli/docs/reference)
- [SDK for JavaScript](https://docs.apify.com/sdk/js)

## Next Steps

Proceed to `apify-hello-world` for your first Actor call.
