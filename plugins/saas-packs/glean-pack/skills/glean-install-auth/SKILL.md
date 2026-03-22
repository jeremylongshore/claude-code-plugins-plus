---
name: glean-install-auth
description: |
  Install and configure Glean API authentication with indexing and client tokens.
  Use when setting up custom datasource indexing, configuring search API access,
  or initializing the Glean developer SDK for enterprise search.
  Trigger: "install glean", "setup glean", "glean auth", "glean API token".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Install & Auth

## Overview

Configure Glean API authentication for enterprise search and knowledge management. Glean has two APIs: the **Indexing API** (push content into search) and the **Client API** (search and retrieve). Each uses separate tokens. Base URL: `https://<domain>-be.glean.com/api`.

## Prerequisites

- Glean enterprise account with admin access
- API token from Glean Admin > API Tokens
- Your Glean deployment domain (e.g., `company-be.glean.com`)

## Instructions

### Step 1: Obtain API Tokens

Navigate to Glean Admin Console > Settings > API:

| Token Type | Purpose | Required Header |
|------------|---------|----------------|
| Indexing API token | Push documents into search index | `Authorization: Bearer <token>` |
| Client API token | Search, chat, user-scoped queries | `Authorization: Bearer <token>` + `X-Glean-Auth-Type: BEARER` |

### Step 2: Configure Environment Variables

```bash
# .env (NEVER commit)
GLEAN_DOMAIN=company-be.glean.com
GLEAN_INDEXING_TOKEN=glean_idx_...
GLEAN_CLIENT_TOKEN=glean_cli_...
GLEAN_DATASOURCE=custom_app  # Your custom datasource name
```

### Step 3: Install SDK and Verify

```bash
npm install @anthropic-ai/glean-indexing-api-client  # Or use fetch directly
```

```typescript
const GLEAN_BASE = `https://${process.env.GLEAN_DOMAIN}/api`;

// Verify indexing API access
async function verifyIndexingAccess() {
  const res = await fetch(`${GLEAN_BASE}/index/v1/getdatasourceconfig`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.GLEAN_INDEXING_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ datasource: process.env.GLEAN_DATASOURCE }),
  });
  const config = await res.json();
  console.log(`Connected. Datasource: ${config.name}`);
}

// Verify client API access
async function verifySearchAccess() {
  const res = await fetch(`${GLEAN_BASE}/client/v1/search`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.GLEAN_CLIENT_TOKEN}`,
      'X-Glean-Auth-Type': 'BEARER',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: 'test', pageSize: 1 }),
  });
  const results = await res.json();
  console.log(`Search works. Found ${results.results?.length ?? 0} results.`);
}
```

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `Unauthorized` | 401 | Invalid token | Regenerate in Admin > API Tokens |
| `Forbidden` | 403 | Token lacks scope | Use correct token type (indexing vs client) |
| `Not Found` | 404 | Wrong domain | Verify GLEAN_DOMAIN includes `-be` suffix |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API Auth](https://developers.glean.com/api-info/indexing/authentication/overview)
- [Client API Auth](https://developers.glean.com/api-info/client/authentication/overview)

## Next Steps

After auth, proceed to `glean-hello-world` for your first index and search.
