---
name: shopify-reference-architecture
description: |
  Implement Shopify app reference architecture with Remix, Prisma session storage,
  and the official app template patterns.
  Use when setting up a new Shopify app, structuring a Remix-based project,
  or configuring Prisma session storage for production.
  Trigger with phrases like "shopify architecture", "shopify app structure",
  "shopify project layout", "shopify Remix template", "shopify app design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Reference Architecture

## Overview

Production-ready architecture based on Shopify's official Remix app template. Covers project structure, session storage with Prisma, extension architecture, and the recommended app patterns.

## Prerequisites

- Understanding of Remix framework basics
- Shopify CLI 3.x installed
- Familiarity with Prisma ORM

## Instructions

### Step 1: Official Project Structure (Remix Template)

```
my-shopify-app/
├── app/
│   ├── routes/
│   │   ├── app._index.tsx          # Main app dashboard
│   │   ├── app.products.tsx        # Product management page
│   │   ├── app.settings.tsx        # App settings
│   │   ├── auth.$.tsx              # OAuth catch-all route
│   │   ├── auth.login/
│   │   │   └── route.tsx           # Login page
│   │   └── webhooks.tsx            # Webhook handler
│   ├── shopify.server.ts           # Shopify API config (singleton)
│   ├── db.server.ts                # Database connection
│   └── root.tsx
├── extensions/
│   ├── theme-app-extension/        # Theme blocks for Online Store
│   ├── checkout-ui/                # Checkout UI extension
│   └── product-discount/           # Shopify Function
├── prisma/
│   ├── schema.prisma               # Database schema
│   └── migrations/
├── shopify.app.toml                # App configuration
├── shopify.web.toml                # Web process config
├── remix.config.js
└── package.json
```

### Step 2: Core App Configuration

The `shopify.server.ts` singleton configures the API client, session storage, webhooks, and auth hooks. It uses `LATEST_API_VERSION` from `@shopify/shopify-api` and exports all auth/session helpers.

See [Core App Configuration](references/core-app-configuration.md) for the complete implementation.

### Step 3: Session Storage with Prisma

The Prisma schema defines the required `Session` model (matching Shopify's session fields) plus your app's custom models. Use SQLite for dev and PostgreSQL for production.

See [Prisma Session Storage](references/prisma-session-storage.md) for the complete schema.

### Step 4: Route Pattern — Authenticated Admin Page

Each app route calls `authenticate.admin(request)` to get a pre-authenticated GraphQL client, then renders with Polaris components. Data flows through Remix loaders.

See [Authenticated Admin Route](references/authenticated-admin-route.md) for the complete implementation.

### Step 5: Theme App Extension

Theme app extensions add customizable blocks to the Online Store. Each block defines a Liquid template with a `{% schema %}` JSON block for merchant-facing settings.

See [Theme App Extension](references/theme-app-extension.md) for the complete implementation.

## Output

- Remix app with Shopify authentication
- Prisma session storage (production-ready)
- Authenticated admin routes with GraphQL data loading
- Theme app extension for Online Store customization

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Session not found | DB not migrated | Run `npx prisma migrate dev` |
| Auth redirect loop | Missing `APP_UNINSTALLED` handler | Implement webhook to clean sessions |
| Extension not showing | Not deployed | Run `shopify app deploy` |
| Polaris styles missing | Missing provider | Wrap app in `<AppProvider>` |

## Examples

### Quick Scaffold

```bash
# Fastest way to start — uses official template
shopify app init --template remix

# Or clone directly
npx degit Shopify/shopify-app-template-remix my-shopify-app
cd my-shopify-app
npm install
shopify app dev
```

## Resources

- [Shopify Remix App Template](https://github.com/Shopify/shopify-app-template-remix)
- [@shopify/shopify-app-remix](https://www.npmjs.com/package/@shopify/shopify-app-remix)
- [Prisma Session Storage](https://www.npmjs.com/package/@shopify/shopify-app-session-storage-prisma)
- [Polaris Components](https://polaris.shopify.com/components)
- [Theme App Extensions](https://shopify.dev/docs/apps/build/online-store/theme-app-extensions)
