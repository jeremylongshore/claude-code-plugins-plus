---
name: shopify-architecture-variants
description: |
  Choose between Shopify app architectures: embedded Remix app, headless storefront with
  Hydrogen, standalone integration, or theme app extension.
  Trigger with phrases like "shopify architecture decision", "shopify embedded vs headless",
  "shopify Hydrogen", "shopify app types", "which shopify architecture".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Architecture Variants

## Overview

Four validated architecture patterns for building on Shopify. Choose based on your use case: embedded admin app, headless storefront, backend integration, or theme extension.

## Prerequisites

- Clear understanding of what you're building
- Knowledge of your target merchants
- Understanding of Shopify's app ecosystem

## Instructions

### Variant A: Embedded Admin App (Remix)

**Best for:** Admin panel apps, merchant tools, dashboards, order management

**When to use:** You need to add functionality to the Shopify admin for merchants.

```
my-shopify-app/
├── app/
│   ├── routes/
│   │   ├── app._index.tsx         # Dashboard (inside Shopify admin)
│   │   ├── app.products.tsx       # Feature pages
│   │   ├── auth.$.tsx             # OAuth handler
│   │   └── webhooks.tsx           # Webhook receiver
│   ├── shopify.server.ts          # @shopify/shopify-app-remix
│   └── root.tsx
├── extensions/                     # Optional extensions
├── prisma/schema.prisma           # Session + app data
├── shopify.app.toml
└── package.json
```

**Key packages:** `@shopify/shopify-app-remix`, `@shopify/polaris`, `@shopify/app-bridge-react`

**API used:** Admin GraphQL API (server-side via `authenticate.admin()`)

**Auth:** OAuth with session token exchange (handled by the Remix adapter)

```typescript
// Authenticated loader — runs server-side inside Shopify admin
export async function loader({ request }: LoaderFunctionArgs) {
  const { admin } = await authenticate.admin(request);
  const response = await admin.graphql(`{ shop { name plan { displayName } } }`);
  return json(await response.json());
}
```

---

### Variant B: Headless Storefront (Hydrogen)

**Best for:** Custom storefronts, unique shopping experiences, PWAs

**When to use:** You're building a custom frontend that replaces the Shopify Online Store.

```
my-hydrogen-store/
├── app/
│   ├── routes/
│   │   ├── ($locale)._index.tsx           # Homepage
│   │   ├── ($locale).products.$handle.tsx # Product page
│   │   ├── ($locale).collections._index.tsx
│   │   ├── ($locale).cart.tsx             # Cart page
│   │   └── ($locale).account.tsx          # Customer account
│   ├── components/
│   │   ├── ProductCard.tsx
│   │   ├── Cart.tsx
│   │   └── Header.tsx
│   ├── lib/
│   │   └── shopify.ts                     # Storefront API client
│   └── root.tsx
├── public/
└── hydrogen.config.ts
```

**Key packages:** `@shopify/hydrogen`, `@shopify/hydrogen-react`, `@shopify/remix-oxygen`

**API used:** Storefront GraphQL API (public, no admin tokens needed)

**Hosting:** Shopify Oxygen (recommended) or any edge platform

```typescript
// Hydrogen product page — uses Storefront API
export async function loader({ params, context }: LoaderFunctionArgs) {
  const { storefront } = context;
  const { product } = await storefront.query(PRODUCT_QUERY, {
    variables: { handle: params.handle },
  });
  return json({ product });
}
```

---

### Variant C: Backend Integration (Standalone)

**Best for:** ERP sync, warehouse management, analytics, multi-channel integration

**When to use:** You're connecting Shopify to other systems — no merchant-facing UI needed.

```
shopify-integration/
├── src/
│   ├── shopify/
│   │   ├── client.ts              # @shopify/shopify-api client
│   │   ├── webhooks.ts            # Webhook handlers
│   │   └── sync.ts                # Data sync logic
│   ├── services/
│   │   ├── erp-sync.ts            # Sync orders to ERP
│   │   ├── inventory-sync.ts      # Bi-directional inventory
│   │   └── customer-export.ts     # Customer data pipeline
│   ├── jobs/
│   │   ├── daily-sync.ts          # Scheduled sync job
│   │   └── webhook-processor.ts   # Queue-based webhook processing
│   └── index.ts
├── .env
└── package.json
```

**Key packages:** `@shopify/shopify-api`, custom app token

**API used:** Admin GraphQL API (custom app access token, no OAuth)

**Auth:** Custom app access token (`shpat_xxx`) — no OAuth flow needed

```typescript
// Custom app — direct API access, no merchant UI
const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: "localhost",
  apiVersion: "2024-10",
  isCustomStoreApp: true,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN!,
});
```

---

### Variant D: Theme App Extension Only

**Best for:** Storefront widgets, product reviews, badges, banners

**When to use:** You only need to add UI elements to the merchant's Online Store.

```
my-theme-extension/
├── extensions/
│   └── my-widget/
│       ├── blocks/
│       │   ├── product-badge.liquid
│       │   ├── announcement-bar.liquid
│       │   └── review-stars.liquid
│       ├── assets/
│       │   ├── widget.css
│       │   └── widget.js
│       ├── locales/
│       │   └── en.default.json
│       └── snippets/
│           └── shared-styles.liquid
├── shopify.app.toml
└── package.json
```

**Key tech:** Liquid templates, JavaScript, CSS

**API used:** None directly — uses Liquid objects (`product`, `cart`, `customer`)

**No server needed:** Theme app extensions run entirely in the merchant's storefront.

```liquid
{% comment %} blocks/product-badge.liquid {% endcomment %}
{% schema %}
{
  "name": "Sale Badge",
  "target": "section",
  "settings": [
    { "type": "text", "id": "badge_text", "label": "Badge Text", "default": "SALE" },
    { "type": "color", "id": "badge_color", "label": "Color", "default": "#FF0000" }
  ]
}
{% endschema %}

{% if product.compare_at_price > product.price %}
  <span class="sale-badge" style="background: {{ block.settings.badge_color }}">
    {{ block.settings.badge_text }}
  </span>
{% endif %}
```

---

## Decision Matrix

| Factor | Embedded App | Hydrogen | Backend Integration | Theme Extension |
|--------|-------------|----------|-------------------|-----------------|
| **Use case** | Admin tools | Custom storefront | System sync | Storefront widgets |
| **Merchant UI** | Yes (in admin) | Yes (storefront) | No | Yes (in theme) |
| **API** | Admin GraphQL | Storefront GraphQL | Admin GraphQL | Liquid objects |
| **Auth** | OAuth | Storefront token | Custom app token | None |
| **Server needed** | Yes | Yes | Yes | No |
| **Complexity** | Medium | High | Low-Medium | Low |
| **App Store eligible** | Yes | N/A | Yes (custom apps) | Yes |
| **Time to build** | 2-4 weeks | 4-8 weeks | 1-2 weeks | Days |

## Output

- Architecture variant selected based on requirements
- Project structure and key packages identified
- Authentication strategy determined
- Technology stack defined

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| "Should I use Hydrogen?" | Want custom storefront | Yes if replacing Online Store, no if adding to admin |
| "Embedded vs standalone?" | Need merchant UI? | Embedded = yes. Standalone = backend-only |
| "Theme extension limits?" | Too complex for Liquid | Combine: extension for UI + embedded app for logic |
| Over-engineering | Started with microservices | Start with Variant A or C, evolve when needed |

## Examples

### Quick Start by Variant

```bash
# Variant A: Embedded Remix App
shopify app init --template remix

# Variant B: Hydrogen Storefront
npm create @shopify/hydrogen

# Variant C: Backend Integration
mkdir shopify-sync && cd shopify-sync
npm init -y && npm install @shopify/shopify-api dotenv

# Variant D: Theme Extension
shopify app init
shopify app generate extension --type theme
```

## Resources

- [Shopify App Types](https://shopify.dev/docs/apps/getting-started)
- [Hydrogen Framework](https://shopify.dev/docs/storefronts/headless/hydrogen)
- [Theme App Extensions](https://shopify.dev/docs/apps/build/online-store/theme-app-extensions)
- [Custom Apps](https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/generate-app-access-tokens-admin)

## Next Steps

For common anti-patterns, see `shopify-known-pitfalls`.
