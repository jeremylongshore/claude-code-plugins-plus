---
name: shopify-architecture-variants
description: |
  Choose between Shopify app architectures: embedded Remix app, headless storefront with
  Hydrogen, standalone integration, or theme app extension.
  Use when starting a new Shopify project and deciding which architecture pattern to follow.
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

Admin panel apps, merchant tools, dashboards. Uses `@shopify/shopify-app-remix` with OAuth and Polaris UI inside the Shopify admin.

See [Embedded Remix App](references/embedded-remix-app.md) for the project structure and authenticated loader pattern.

### Variant B: Headless Storefront (Hydrogen)

Custom storefronts and unique shopping experiences. Uses the Storefront GraphQL API, hosted on Shopify Oxygen or any edge platform.

See [Hydrogen Storefront](references/hydrogen-storefront.md) for the project structure and Storefront API loader.

### Variant C: Backend Integration (Standalone)

ERP sync, warehouse management, analytics. Uses `@shopify/shopify-api` with a custom app access token -- no OAuth or merchant UI needed.

See [Backend Integration](references/backend-integration.md) for the project structure and client setup.

### Variant D: Theme App Extension Only

Storefront widgets, product reviews, badges. Runs entirely in the merchant's storefront using Liquid templates -- no server needed.

See [Theme App Extension](references/theme-app-extension.md) for the project structure and Liquid block example.

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
