---
name: shopify-local-dev-loop
description: |
  Configure Shopify local development with Shopify CLI, hot reload, and ngrok tunneling.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Shopify.
  Trigger with phrases like "shopify dev setup", "shopify local development",
  "shopify dev environment", "develop with shopify", "shopify CLI dev".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Bash(shopify:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow using Shopify CLI, ngrok tunneling for webhooks, and Vitest for testing against the Shopify API.

## Prerequisites

- Completed `shopify-install-auth` setup
- Node.js 18+ with npm/pnpm
- Shopify CLI 3.x (`npm install -g @shopify/cli`)
- A Shopify Partner account and development store

## Instructions

### Step 1: Scaffold with Shopify CLI

```bash
# Create a new Remix-based Shopify app (recommended)
shopify app init

# Or scaffold manually
mkdir my-shopify-app && cd my-shopify-app
npm init -y
npm install @shopify/shopify-api @shopify/shopify-app-remix \
  @shopify/app-bridge-react @remix-run/node @remix-run/react
```

### Step 2: Project Structure

```
my-shopify-app/
├── app/
│   ├── routes/
│   │   ├── app._index.tsx      # Main app page
│   │   ├── app.products.tsx    # Products management
│   │   ├── auth.$.tsx          # OAuth callback
│   │   └── webhooks.tsx        # Webhook handler
│   ├── shopify.server.ts       # Shopify API client setup
│   └── root.tsx
├── extensions/                  # Theme app extensions
├── shopify.app.toml             # App configuration
├── .env                         # Local secrets (git-ignored)
├── .env.example                 # Template for team
└── package.json
```

### Step 3: Configure shopify.app.toml

Central app configuration with scopes, auth redirects, and mandatory GDPR webhook subscriptions.

See [App TOML Config](references/app-toml-config.md) for the complete configuration file.

### Step 4: Start Dev Server with Tunnel

```bash
# Shopify CLI handles ngrok tunnel + OAuth automatically
shopify app dev

# This will:
# 1. Start your app on localhost:3000
# 2. Create an ngrok tunnel
# 3. Update your app URLs in Partner Dashboard
# 4. Open your app in the dev store admin
# 5. Hot reload on file changes
```

### Step 5: Set Up Testing

Vitest setup with mocked Shopify API client and recommended package.json scripts for the dev workflow.

See [Vitest Shopify Mock](references/vitest-shopify-mock.md) for the complete test setup.

### Step 6: GraphQL Explorer for Development

```bash
# Open the Shopify GraphiQL explorer for your store
# Navigate to: https://your-store.myshopify.com/admin/api/2025-04/graphql.json
# Use the Shopify Admin GraphiQL app (install from admin)

# Or use curl to test queries directly:
curl -X POST \
  "https://your-store.myshopify.com/admin/api/${SHOPIFY_API_VERSION:-2025-04}/graphql.json" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Access-Token: shpat_xxx" \
  -d '{"query": "{ shop { name } }"}'
```

## Output

- Shopify CLI dev server running with hot reload
- Ngrok tunnel forwarding to localhost
- Test suite with mocked Shopify API calls
- GraphQL explorer available for API exploration

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Could not find a Shopify partner organization` | CLI not logged in | Run `shopify auth login` |
| `Port 3000 already in use` | Another process on port | Kill process or use `--port 3001` |
| `Tunnel connection failed` | ngrok issues | Check ngrok status or use `--tunnel-url` |
| `App not installed on store` | First time setup | Open the URL CLI provides, accept install |
| `SHOPIFY_API_KEY not set` | Missing .env | Copy from `.env.example` and fill in values |

## Examples

### Debug with Request Logging

```typescript
// Enable verbose request logging in development
import { LogSeverity } from "@shopify/shopify-api";

const shopify = shopifyApi({
  // ... other config
  logger: {
    level: LogSeverity.Debug, // Logs all requests/responses
    httpRequests: true,
    timestamps: true,
  },
});
```

### Seed Test Data

```typescript
// scripts/seed-dev-store.ts — create test products
async function seedStore(client: any) {
  const products = [
    { title: "Test Widget", productType: "Widget", vendor: "Dev" },
    { title: "Test Gadget", productType: "Gadget", vendor: "Dev" },
  ];

  for (const product of products) {
    await client.request(`
      mutation { productCreate(product: {
        title: "${product.title}",
        productType: "${product.productType}",
        vendor: "${product.vendor}"
      }) {
        product { id title }
        userErrors { field message }
      }}
    `);
  }
}
```

## Resources

- [Shopify CLI Documentation](https://shopify.dev/docs/apps/build/cli-for-apps)
- [Shopify App Remix Template](https://github.com/Shopify/shopify-app-template-remix)
- [Vitest Documentation](https://vitest.dev/)
- [Shopify GraphiQL Explorer](https://shopify.dev/docs/apps/build/graphql)
