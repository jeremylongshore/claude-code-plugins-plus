---
name: shopify-hello-world
description: |
  Create a minimal working Shopify app that queries products via GraphQL Admin API.
  Use when starting a new Shopify integration, testing your setup,
  or learning basic Shopify API patterns.
  Trigger with phrases like "shopify hello world", "shopify example",
  "shopify quick start", "simple shopify app", "first shopify API call".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Hello World

## Overview

Minimal working example: query your store's products using the Shopify GraphQL Admin API. Uses `@shopify/shopify-api` with a custom app access token for zero-friction setup.

## Prerequisites

- Completed `shopify-install-auth` setup
- A Shopify development store
- An Admin API access token (`shpat_xxx`) from Settings > Apps > Develop apps

## Instructions

### Step 1: Create Project

```bash
mkdir shopify-hello-world && cd shopify-hello-world
npm init -y
npm install @shopify/shopify-api dotenv
```

### Step 2: Configure Environment

```bash
# .env
SHOPIFY_STORE=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
```

### Step 3: Write the Hello World Script

Initialize the Shopify API client with `LATEST_API_VERSION` (imported from `@shopify/shopify-api`), create a custom app session, then query shop info and products via GraphQL.

See [Hello World Script](references/hello-world-script.md) for the complete implementation.

### Step 4: Run It

```bash
npx tsx hello-shopify.ts
# Or compile first:
npx tsc hello-shopify.ts && node hello-shopify.js
```

## Output

Expected console output:

```
Store: My Dev Store
Currency: USD

Products:
  - Classic T-Shirt (ACTIVE, 150 in stock)
      Variant: Small — $29.99 (SKU: TSH-SM)
      Variant: Medium — $29.99 (SKU: TSH-MD)
      Variant: Large — $29.99 (SKU: TSH-LG)
  - Coffee Mug (ACTIVE, 42 in stock)
      Variant: Default Title — $14.99 (SKU: MUG-01)

Success! Your Shopify connection is working.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `HttpResponseError: 401 Unauthorized` | Invalid or revoked access token | Regenerate token in Shopify admin > Settings > Apps |
| `HttpResponseError: 403 Forbidden` | Token lacks required scopes | Enable `read_products` scope in app config |
| `HttpResponseError: 404 Not Found` | Wrong store domain or API version | Verify store URL is `*.myshopify.com` |
| `ENOTFOUND your-store.myshopify.com` | Store domain typo or DNS issue | Double-check `SHOPIFY_STORE` value |
| `GraphqlQueryError` with `userErrors` | Invalid query syntax | Check field names against API version docs |
| `MODULE_NOT_FOUND @shopify/shopify-api` | Package not installed | Run `npm install @shopify/shopify-api` |

## Examples

### Create a Product and Query via REST

See [GraphQL Mutation and REST Examples](references/graphql-mutation-and-rest-examples.md) for a `productCreate` mutation and legacy REST API usage.

## Resources

- [Shopify GraphQL Admin API Reference](https://shopify.dev/docs/api/admin-graphql/latest)
- [Getting Started with GraphQL](https://shopify.dev/docs/apps/build/graphql/basics/queries)
- [REST Admin API Reference](https://shopify.dev/docs/api/admin-rest)
- [Shopify API Versioning](https://shopify.dev/docs/api/usage/versioning)
