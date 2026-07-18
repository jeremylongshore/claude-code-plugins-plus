---
name: klaviyo-install-auth
description: 'Install and configure Klaviyo Node.js SDK with API key authentication.

  Use when setting up a new Klaviyo integration, configuring API keys,

  or initializing the klaviyo-api package in your project.

  Trigger with phrases like "install klaviyo", "setup klaviyo",

  "klaviyo auth", "configure klaviyo API key", "klaviyo SDK setup".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(pip:*), Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Install & Auth

## Overview

Set up the official `klaviyo-api` Node.js SDK and configure private API key authentication against Klaviyo's REST API (revision `2024-10-15`). The workflow below is the high-level path; the verbatim code for every step lives in [the full implementation walkthrough](references/implementation.md), and copy-paste sequences live in [worked examples](references/examples.md).

## Prerequisites

- Node.js 18+ (or Python 3.10+ for Python SDK)
- Klaviyo account at https://www.klaviyo.com/
- Private API key from **Settings > API Keys** in Klaviyo dashboard
- Public API key (for client-side only -- never use in server code)

## Instructions

The full sequence is five steps. The essentials are below; drill into
[references/implementation.md](references/implementation.md) for the complete
code of each step (verify script, revision header, Python setup, scope table).

### Step 1: Install the Official SDK

```bash
# Node.js (official SDK -- NOT @klaviyo/sdk, that's deprecated)
npm install klaviyo-api
```

> **Important:** The npm package is `klaviyo-api`, not `@klaviyo/sdk`. The SDK exports per-resource API classes (ProfilesApi, EventsApi, etc.) that each take an `ApiKeySession`.

### Step 2: Configure Authentication

Store the private key in `.env` and confirm it is gitignored. Klaviyo uses two key types:

| Key Type | Prefix | Use Case | Header |
|----------|--------|----------|--------|
| Private API Key | `pk_` | Server-side REST API | `Authorization: Klaviyo-API-Key pk_***` |
| Public API Key | 6-char | Client-side Track/Identify | Query param `company_id` |

### Step 3: Initialize the SDK

```typescript
// src/klaviyo/client.ts
import { ApiKeySession, ProfilesApi, EventsApi, ListsApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

export const profilesApi = new ProfilesApi(session);
export const eventsApi = new EventsApi(session);
export const listsApi = new ListsApi(session);
```

### Steps 4-5: Verify & set the revision header

Run a one-time verification against `AccountsApi.getAccounts()` to prove the key
works, and remember every request needs a `revision: 2024-10-15` header (the SDK
adds it automatically; raw HTTP does not). Full verify script + cURL smoke test:
[references/implementation.md](references/implementation.md).

## Output

- `klaviyo-api` package installed in `node_modules`
- `.env` file with `KLAVIYO_PRIVATE_KEY` set
- Verified API connection with account name printed
- Per-resource API clients ready for import

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `Authentication failed` | 401 | Invalid or expired private key | Regenerate key at Settings > API Keys |
| `Forbidden` | 403 | Key missing required scopes | Create key with appropriate scopes (e.g., `profiles:read`) |
| `Rate limited` | 429 | Exceeded 75 req/s burst or 700 req/min steady | Honor `Retry-After` header; see `klaviyo-rate-limits` |
| `MODULE_NOT_FOUND` | N/A | Wrong package name | Use `klaviyo-api`, not `@klaviyo/sdk` |
| `ENOTFOUND a.klaviyo.com` | N/A | DNS/network failure | Check internet connectivity, firewall rules |

## Examples

Four copy-paste sequences (fresh Node project, key verification, Python with
retry tuning, raw-HTTP smoke test) are in
[references/examples.md](references/examples.md). The fastest sanity check —
confirm a key from a shell before writing any code:

```bash
curl -X GET "https://a.klaviyo.com/api/profiles/" \
  -H "Authorization: Klaviyo-API-Key pk_***" \
  -H "revision: 2024-10-15" \
  -H "Accept: application/vnd.api+json"
```

A `200` with a JSON `data` array means the key and revision header are valid; a
`401` means the key is wrong; a `403` means it lacks the `profiles:read` scope.

## Resources

- [Full implementation walkthrough](references/implementation.md) — verbatim code for all 5 steps, Python setup, and the API scopes table
- [Worked examples](references/examples.md) — four end-to-end copy-paste sequences
- [Klaviyo API Reference](https://developers.klaviyo.com/en/reference/api_overview)
- [Authentication Guide](https://developers.klaviyo.com/en/docs/authenticate_)
- [klaviyo-api npm](https://www.npmjs.com/package/klaviyo-api)
- [klaviyo-api-node GitHub](https://github.com/klaviyo/klaviyo-api-node)
- [Klaviyo Status](https://status.klaviyo.com)

## Next Steps

After successful auth, proceed to the `klaviyo-hello-world` skill for your first
profile + event API call, then `klaviyo-rate-limits` to harden request handling
against the 75 req/s burst ceiling.
