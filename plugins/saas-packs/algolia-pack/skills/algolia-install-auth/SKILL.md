---
name: algolia-install-auth
description: |
  Install and configure the Algolia JavaScript v5 client with proper API key management.
  Use when setting up a new Algolia integration, configuring Application ID and API keys,
  or initializing the algoliasearch client in a Node.js/TypeScript project.
  Trigger: "install algolia", "setup algolia", "algolia auth", "configure algolia keys".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Install & Auth

## Overview

Set up the `algoliasearch` v5 JavaScript client with Application ID and API key authentication. Algolia uses a two-key system: an **Application ID** (identifies your app) and an **API key** (controls permissions). Every Algolia account has three default keys: Search-Only, Admin, and Monitoring.

## Prerequisites

- Node.js 18+ with npm, pnpm, or yarn
- Algolia account at [dashboard.algolia.com](https://dashboard.algolia.com)
- Application ID and API key from dashboard > Settings > API Keys

## Instructions

### Step 1: Install the Client

```bash
# Full client (Search + Analytics + Recommend + A/B Testing + Personalization)
npm install algoliasearch

# Or search-only (lighter bundle, frontend use)
npm install algoliasearch  # then import { liteClient } from 'algoliasearch/lite'

# Or individual API clients if you only need one
npm install @algolia/client-search
npm install @algolia/client-analytics
npm install @algolia/recommend
```

### Step 2: Configure Environment Variables

```bash
# .env (NEVER commit — add to .gitignore)
ALGOLIA_APP_ID=YourApplicationID
ALGOLIA_ADMIN_KEY=your_admin_api_key
ALGOLIA_SEARCH_KEY=your_search_only_api_key

# .gitignore
.env
.env.local
.env.*.local
```

**Key types and when to use them:**

| Key Type | ACL Permissions | Use In |
|----------|----------------|--------|
| Search-Only | `search` | Frontend, mobile apps |
| Admin | All operations | Backend only, never expose |
| Monitoring | `GET /1/status` | Health checks |
| Custom | You define ACL | Scoped backend services |

### Step 3: Initialize the Client

```typescript
// src/algolia/client.ts
import { algoliasearch } from 'algoliasearch';

// Backend — Admin client for indexing operations
const client = algoliasearch(
  process.env.ALGOLIA_APP_ID!,
  process.env.ALGOLIA_ADMIN_KEY!
);

// Frontend — Search-only client (safe to expose)
import { liteClient } from 'algoliasearch/lite';

const searchClient = liteClient(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID!,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_KEY!
);
```

### Step 4: Verify Connection

```typescript
// Quick verification: list indices
async function verifyAlgoliaConnection() {
  try {
    const { items } = await client.listIndices();
    console.log(`Connected. Found ${items.length} indices.`);
    return true;
  } catch (error) {
    console.error('Algolia connection failed:', error);
    return false;
  }
}

await verifyAlgoliaConnection();
```

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `Invalid Application-ID or API key` | 403 | Wrong App ID or key | Copy fresh values from dashboard > Settings > API Keys |
| `Index does not exist` | 404 | Querying non-existent index | Create index first with `saveObjects` |
| `Method not allowed` | 405 | Search-only key used for write op | Use Admin key for indexing operations |
| `RetryError: Unreachable hosts` | N/A | Network/DNS issue | Check firewall allows `*.algolia.net` and `*.algolianet.com` |
| `Record quota exceeded` | 429 | Plan limit hit | Upgrade plan or delete unused records |

## Examples

### Singleton Pattern (Recommended)

```typescript
// src/algolia/client.ts
import { algoliasearch, type Algoliasearch } from 'algoliasearch';

let _client: Algoliasearch | null = null;

export function getAlgoliaClient(): Algoliasearch {
  if (!_client) {
    const appId = process.env.ALGOLIA_APP_ID;
    const apiKey = process.env.ALGOLIA_ADMIN_KEY;
    if (!appId || !apiKey) {
      throw new Error('Missing ALGOLIA_APP_ID or ALGOLIA_ADMIN_KEY env vars');
    }
    _client = algoliasearch(appId, apiKey);
  }
  return _client;
}
```

### Generate Scoped API Key (Secured API Key)

```typescript
import { algoliasearch } from 'algoliasearch';

// Generate a secured API key that restricts search to specific filters
const client = algoliasearch(appId, adminKey);

const securedKey = client.generateSecuredApiKey({
  parentApiKey: searchOnlyKey,
  restrictions: {
    filters: 'tenant_id:acme_corp',
    validUntil: Math.floor(Date.now() / 1000) + 3600, // 1 hour
    restrictIndices: ['products_acme'],
  },
});
```

## Resources

- [Algolia JavaScript v5 Client](https://www.algolia.com/doc/libraries/javascript/v5/methods/search/)
- [API Keys Guide](https://www.algolia.com/doc/guides/security/api-keys/)
- [Secured API Keys](https://www.algolia.com/doc/guides/security/api-keys/in-depth/secured-api-keys/)
- [Algolia Dashboard](https://dashboard.algolia.com)

## Next Steps

After successful auth, proceed to `algolia-hello-world` for your first index and search.
