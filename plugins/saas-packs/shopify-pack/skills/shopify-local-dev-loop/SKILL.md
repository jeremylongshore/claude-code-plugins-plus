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

```toml
# shopify.app.toml — central app configuration
name = "My App"
client_id = "your_api_key_here"

[access_scopes]
scopes = "read_products,write_products,read_orders"

[auth]
redirect_urls = [
  "https://localhost/auth/callback",
  "https://localhost/auth/shopify/callback",
]

[webhooks]
api_version = "2024-10"

  [webhooks.subscriptions]
  # Mandatory GDPR webhooks
  [[webhooks.subscriptions]]
  topics = ["customers/data_request"]
  uri = "/webhooks"

  [[webhooks.subscriptions]]
  topics = ["customers/redact"]
  uri = "/webhooks"

  [[webhooks.subscriptions]]
  topics = ["shop/redact"]
  uri = "/webhooks"
```

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

```typescript
// tests/shopify-client.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the Shopify API client
vi.mock("@shopify/shopify-api", () => ({
  shopifyApi: vi.fn(() => ({
    clients: {
      Graphql: vi.fn().mockImplementation(() => ({
        request: vi.fn().mockResolvedValue({
          data: {
            products: {
              edges: [
                { node: { id: "gid://shopify/Product/1", title: "Test Product" } },
              ],
            },
          },
        }),
      })),
    },
    session: {
      customAppSession: vi.fn(() => ({ shop: "test.myshopify.com" })),
    },
  })),
}));

describe("Shopify Integration", () => {
  it("should fetch products", async () => {
    // Test your product-fetching logic here
  });

  it("should handle GraphQL errors", async () => {
    // Test error handling
  });
});
```

```json
{
  "scripts": {
    "dev": "shopify app dev",
    "build": "remix vite:build",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "lint": "eslint app/",
    "shopify": "shopify",
    "deploy": "shopify app deploy"
  }
}
```

### Step 6: GraphQL Explorer for Development

```bash
# Open the Shopify GraphiQL explorer for your store
# Navigate to: https://your-store.myshopify.com/admin/api/2024-10/graphql.json
# Use the Shopify Admin GraphiQL app (install from admin)

# Or use curl to test queries directly:
curl -X POST \
  "https://your-store.myshopify.com/admin/api/2024-10/graphql.json" \
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

## Next Steps

See `shopify-sdk-patterns` for production-ready code patterns.
