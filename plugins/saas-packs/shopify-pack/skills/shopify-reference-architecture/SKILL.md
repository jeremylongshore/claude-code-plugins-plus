---
name: shopify-reference-architecture
description: |
  Implement Shopify app reference architecture with Remix, Prisma session storage,
  and the official app template patterns.
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
│   │   ├── blocks/
│   │   │   └── product-rating.liquid
│   │   └── locales/
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

```typescript
// app/shopify.server.ts — the heart of the app
import "@shopify/shopify-app-remix/adapters/node";
import { AppDistribution, shopifyApp } from "@shopify/shopify-app-remix/server";
import { PrismaSessionStorage } from "@shopify/shopify-app-session-storage-prisma";
import prisma from "./db.server";

const shopify = shopifyApp({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  appUrl: process.env.SHOPIFY_APP_URL!,
  scopes: process.env.SHOPIFY_SCOPES?.split(","),
  apiVersion: "2024-10",
  distribution: AppDistribution.AppStore, // or SingleMerchant
  sessionStorage: new PrismaSessionStorage(prisma),
  webhooks: {
    APP_UNINSTALLED: {
      deliveryMethod: "http",
      callbackUrl: "/webhooks",
    },
    PRODUCTS_UPDATE: {
      deliveryMethod: "http",
      callbackUrl: "/webhooks",
    },
  },
  hooks: {
    afterAuth: async ({ session }) => {
      // Register webhooks after successful auth
      shopify.registerWebhooks({ session });
    },
  },
  future: {
    unstable_newEmbeddedAuthStrategy: true,
  },
});

export default shopify;
export const apiVersion = "2024-10";
export const addDocumentResponseHeaders = shopify.addDocumentResponseHeaders;
export const authenticate = shopify.authenticate;
export const unauthenticated = shopify.unauthenticated;
export const login = shopify.login;
export const registerWebhooks = shopify.registerWebhooks;
export const sessionStorage = shopify.sessionStorage;
```

### Step 3: Session Storage with Prisma

```prisma
// prisma/schema.prisma
datasource db {
  provider = "sqlite"  // or "postgresql" for production
  url      = env("DATABASE_URL")
}

model Session {
  id            String    @id
  shop          String
  state         String
  isOnline      Boolean   @default(false)
  scope         String?
  expires       DateTime?
  accessToken   String
  userId        BigInt?
  firstName     String?
  lastName      String?
  email         String?
  accountOwner  Boolean   @default(false)
  locale        String?
  collaborator  Boolean?  @default(false)
  emailVerified Boolean?  @default(false)
}

// Your app's custom models
model ProductSync {
  id          String   @id @default(cuid())
  shop        String
  productId   String
  lastSynced  DateTime @default(now())
  status      String   @default("pending")
  @@unique([shop, productId])
}
```

### Step 4: Route Pattern — Authenticated Admin Page

```typescript
// app/routes/app.products.tsx
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { authenticate } from "../shopify.server";
import { Page, Layout, Card, DataTable } from "@shopify/polaris";

export async function loader({ request }: LoaderFunctionArgs) {
  const { admin } = await authenticate.admin(request);

  // admin.graphql is a pre-authenticated GraphQL client
  const response = await admin.graphql(`{
    products(first: 25, sortKey: UPDATED_AT, reverse: true) {
      edges {
        node {
          id
          title
          status
          totalInventory
          priceRangeV2 {
            minVariantPrice { amount currencyCode }
          }
        }
      }
    }
  }`);

  const data = await response.json();
  return json({ products: data.data.products.edges.map((e: any) => e.node) });
}

export default function Products() {
  const { products } = useLoaderData<typeof loader>();

  return (
    <Page title="Products">
      <Layout>
        <Layout.Section>
          <Card>
            <DataTable
              columnContentTypes={["text", "text", "numeric", "text"]}
              headings={["Title", "Status", "Inventory", "Price"]}
              rows={products.map((p: any) => [
                p.title,
                p.status,
                p.totalInventory,
                `$${p.priceRangeV2.minVariantPrice.amount}`,
              ])}
            />
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
```

### Step 5: Theme App Extension

```liquid
{% comment %} extensions/theme-app-extension/blocks/product-rating.liquid {% endcomment %}

{% schema %}
{
  "name": "Product Rating",
  "target": "section",
  "settings": [
    {
      "type": "range",
      "id": "max_stars",
      "label": "Maximum Stars",
      "min": 1,
      "max": 5,
      "default": 5
    },
    {
      "type": "color",
      "id": "star_color",
      "label": "Star Color",
      "default": "#FFD700"
    }
  ]
}
{% endschema %}

<div class="product-rating" style="--star-color: {{ block.settings.star_color }}">
  {% assign rating = product.metafields.custom.rating.value | default: 0 %}
  {% for i in (1..block.settings.max_stars) %}
    <span class="star {% if i <= rating %}filled{% endif %}">&#9733;</span>
  {% endfor %}
  <span class="rating-text">{{ rating }}/{{ block.settings.max_stars }}</span>
</div>

<style>
  .product-rating .star { color: #ccc; font-size: 1.2em; }
  .product-rating .star.filled { color: var(--star-color); }
</style>
```

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

## Next Steps

For multi-environment setup, see `shopify-multi-env-setup`.
