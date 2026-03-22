---
name: shopify-install-auth
description: |
  Install and configure Shopify app authentication with OAuth, session tokens, and the @shopify/shopify-api SDK.
  Use when setting up a new Shopify app, configuring API credentials,
  or initializing authentication for Admin or Storefront API access.
  Trigger with phrases like "install shopify", "setup shopify",
  "shopify auth", "shopify OAuth", "configure shopify API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Install & Auth

## Overview

Set up Shopify app authentication using the official `@shopify/shopify-api` library. Covers OAuth flow, session token exchange, custom app tokens, and Storefront API access.

## Prerequisites

- Node.js 18+ (the `@shopify/shopify-api` v9+ requires it)
- A Shopify Partner account at https://partners.shopify.com
- An app created in the Partner Dashboard with API credentials
- A development store for testing

## Instructions

### Step 1: Install the Shopify API Library

```bash
# Core library + Node.js runtime adapter
npm install @shopify/shopify-api @shopify/shopify-app-remix
# Or for standalone Node apps:
npm install @shopify/shopify-api @shopify/shopify-app-express

# For Remix (recommended by Shopify):
npm install @shopify/shopify-app-remix @shopify/app-bridge-react
```

### Step 2: Configure Environment Variables

Create a `.env` file (add to `.gitignore` immediately):

```bash
# .env — NEVER commit this file
SHOPIFY_API_KEY=your_app_api_key
SHOPIFY_API_SECRET=your_app_api_secret
SHOPIFY_SCOPES=read_products,write_products,read_orders,write_orders
SHOPIFY_APP_URL=https://your-app.example.com
SHOPIFY_HOST_NAME=your-app.example.com

# For custom/private apps only:
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx

# API version — use a stable quarterly release
SHOPIFY_API_VERSION=2024-10
```

```bash
# .gitignore — add these immediately
.env
.env.local
.env.*.local
```

### Step 3: Initialize the Shopify API Library

```typescript
// src/shopify.ts
import "@shopify/shopify-api/adapters/node";
import { shopifyApi, LATEST_API_VERSION, Session } from "@shopify/shopify-api";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  scopes: process.env.SHOPIFY_SCOPES!.split(","),
  hostName: process.env.SHOPIFY_HOST_NAME!,
  apiVersion: LATEST_API_VERSION, // or "2024-10"
  isEmbeddedApp: true,
});

export default shopify;
```

### Step 4: Implement OAuth Flow (Public Apps)

```typescript
// routes/auth.ts — Express example
import express from "express";
import shopify from "../shopify";

const router = express.Router();

// Step 1: Begin OAuth — redirect merchant to Shopify
router.get("/auth", async (req, res) => {
  const shop = req.query.shop as string;
  // Generates the authorization URL with HMAC validation
  const authRoute = await shopify.auth.begin({
    shop: shopify.utils.sanitizeShop(shop, true)!,
    callbackPath: "/auth/callback",
    isOnline: false, // offline = long-lived token
    rawRequest: req,
    rawResponse: res,
  });
});

// Step 2: Handle callback — exchange code for access token
router.get("/auth/callback", async (req, res) => {
  const callback = await shopify.auth.callback({
    rawRequest: req,
    rawResponse: res,
  });

  // callback.session contains the access token
  const session: Session = callback.session;
  console.log("Access token:", session.accessToken);
  console.log("Shop:", session.shop); // "store-name.myshopify.com"
  console.log("Scopes:", session.scope); // "read_products,write_products,..."

  // IMPORTANT: Persist session to your database
  await saveSession(session);

  res.redirect(`/?shop=${session.shop}&host=${req.query.host}`);
});

export default router;
```

### Step 5: Token Exchange (Embedded Apps)

For embedded apps, use session token exchange instead of traditional OAuth:

```typescript
// Token exchange — converts session token (JWT) to API access token
import shopify from "../shopify";

async function exchangeToken(
  shop: string,
  sessionToken: string
): Promise<Session> {
  const { session } = await shopify.auth.tokenExchange({
    sessionToken,
    shop,
    requestedTokenType: RequestedTokenType.OfflineAccessToken,
  });
  return session;
}
```

### Step 6: Custom App / Private App Auth

For custom apps (installed on a single store), use a permanent access token:

```typescript
// Custom app — no OAuth needed, use Admin API access token directly
import "@shopify/shopify-api/adapters/node";
import { shopifyApi } from "@shopify/shopify-api";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: process.env.SHOPIFY_HOST_NAME!,
  apiVersion: "2024-10",
  isCustomStoreApp: true,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN!, // shpat_xxx
});

// Create a session for the custom app
const session = shopify.session.customAppSession(
  "your-store.myshopify.com"
);

// Use GraphQL client directly
const client = new shopify.clients.Graphql({ session });
```

### Step 7: Verify Auth is Working

```typescript
// Quick connectivity test
async function verifyShopifyAuth(session: Session): Promise<void> {
  const client = new shopify.clients.Graphql({ session });

  const response = await client.request(`{
    shop {
      name
      email
      plan {
        displayName
      }
      primaryDomain {
        url
      }
    }
  }`);

  console.log("Connected to:", response.data.shop.name);
  console.log("Plan:", response.data.shop.plan.displayName);
  console.log("Domain:", response.data.shop.primaryDomain.url);
}
```

## Output

- `@shopify/shopify-api` installed and configured
- OAuth flow or custom app auth operational
- Session with valid access token persisted
- Verified connection to the Shopify Admin API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `InvalidApiKeyError` | Wrong `SHOPIFY_API_KEY` | Verify in Partner Dashboard > App > API credentials |
| `InvalidHmacError` during callback | Secret mismatch or URL tampering | Check `SHOPIFY_API_SECRET` matches Partner Dashboard |
| `SessionNotFound` | Session not persisted | Implement `SessionStorage` (DB, Redis, or file) |
| `HttpResponseError: 401` | Token expired or revoked | Merchant uninstalled app — trigger re-auth |
| `InvalidScopeError` | Requested scope not approved | Only use scopes from the approved list in your app config |
| `ShopifyErrors.InvalidShop` | Malformed shop domain | Must be `*.myshopify.com` — use `sanitizeShop()` |

## Examples

### Shopify API Access Scopes Reference

| Scope | Grants Access To |
|-------|-----------------|
| `read_products` / `write_products` | Products, variants, collections, images |
| `read_orders` / `write_orders` | Orders, transactions, fulfillments |
| `read_customers` / `write_customers` | Customer data, addresses, metafields |
| `read_inventory` / `write_inventory` | Inventory levels across locations |
| `read_content` / `write_content` | Pages, blogs, articles |
| `read_themes` / `write_themes` | Theme files and assets |
| `read_shipping` / `write_shipping` | Shipping zones, carrier services |
| `read_fulfillments` / `write_fulfillments` | Fulfillment orders and services |

### Storefront API Access

```typescript
// Storefront API uses a different token — generated in admin
const storefrontClient = new shopify.clients.Storefront({
  session,
  apiVersion: "2024-10",
});

const products = await storefrontClient.request(`{
  products(first: 10) {
    edges {
      node {
        id
        title
        handle
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
        }
      }
    }
  }
}`);
```

## Resources

- [Shopify Authentication Overview](https://shopify.dev/docs/apps/build/authentication-authorization)
- [Shopify API Access Scopes](https://shopify.dev/docs/api/usage/access-scopes)
- [@shopify/shopify-api on npm](https://www.npmjs.com/package/@shopify/shopify-api)
- [Session Token Reference](https://shopify.dev/docs/apps/build/authentication-authorization/session-tokens)
- [Token Exchange](https://github.com/Shopify/shopify-api-js/blob/main/packages/shopify-api/docs/reference/auth/tokenExchange.md)

## Next Steps

After successful auth, proceed to `shopify-hello-world` for your first API call.
