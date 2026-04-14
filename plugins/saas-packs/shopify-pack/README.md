# Shopify Skill Pack

> 38 production-grade Claude Code skills for building Shopify apps, integrations, and headless storefronts

## What Is Shopify?

[Shopify](https://www.shopify.com) is the leading e-commerce platform powering millions of online stores. The platform provides:

- **Admin API** (GraphQL and REST) for managing products, orders, customers, and fulfillments
- **Storefront API** (GraphQL) for building custom storefronts and headless commerce
- **Webhooks** for real-time event notifications (order created, product updated, etc.)
- **App Extensions** for embedding UI in the Shopify admin and Online Store themes
- **Hydrogen** framework for building custom React storefronts on Shopify data

This skill pack provides real, working guidance for every stage of Shopify development -- from first API call to production deployment at scale.

## Installation

```bash
/plugin install shopify-pack@claude-code-plugins-plus
```

## Skills Included

### Getting Started (S01-S04)

| Skill | Description |
|-------|-------------|
| `shopify-install-auth` | Set up OAuth, session tokens, and `@shopify/shopify-api` authentication |
| `shopify-hello-world` | First API call: query products via GraphQL Admin API |
| `shopify-local-dev-loop` | Shopify CLI dev server, ngrok tunneling, and Vitest testing |
| `shopify-sdk-patterns` | Typed GraphQL clients, cursor pagination, multi-tenant factories |

### Core Workflows (S05-S08)

| Skill | Description |
|-------|-------------|
| `shopify-core-workflow-a` | Products, variants, collections -- CRUD with real GraphQL mutations |
| `shopify-core-workflow-b` | Orders, customers, fulfillments -- query, create, and process |
| `shopify-common-errors` | Diagnose 401, 403, 422, 429, and GraphQL userErrors with real responses |
| `shopify-debug-bundle` | Collect API versions, scopes, rate limit state for support tickets |

### Operations (S09-S12)

| Skill | Description |
|-------|-------------|
| `shopify-rate-limits` | REST leaky bucket and GraphQL calculated query cost with real headers |
| `shopify-security-basics` | HMAC webhook verification, token management, access scope minimization |
| `shopify-prod-checklist` | App Store submission requirements, GDPR compliance, launch checklist |
| `shopify-upgrade-migration` | API version upgrades, REST-to-GraphQL migration, breaking change handling |

### Pro Skills (P13-P18)

| Skill | Description |
|-------|-------------|
| `shopify-ci-integration` | GitHub Actions pipeline with API version checking and Shopify CLI deploy |
| `shopify-deploy-integration` | Deploy to Vercel, Fly.io, and Cloud Run with proper secret management |
| `shopify-webhooks-events` | Register webhooks, handle GDPR mandatory topics, webhook HMAC verification |
| `shopify-performance-tuning` | Query cost reduction, bulk operations, Storefront API for high traffic |
| `shopify-cost-tuning` | Plan-based rate limits, app billing API, usage monitoring |
| `shopify-reference-architecture` | Official Remix template, Prisma sessions, Polaris UI, theme extensions |

### Flagship Skills (F19-F24)

| Skill | Description |
|-------|-------------|
| `shopify-multi-env-setup` | Separate app instances for dev/staging/prod with environment guards |
| `shopify-observability` | GraphQL query cost metrics, rate limit monitoring, webhook delivery tracking |
| `shopify-incident-runbook` | Triage with status page, decision tree, error-specific remediation |
| `shopify-data-handling` | GDPR mandatory webhooks, PII redaction, data retention policies |
| `shopify-enterprise-rbac` | Staff permissions, multi-location access, Shopify Plus Organization API |
| `shopify-migration-deep-dive` | Bulk product import with productSet, inventory migration, URL redirects |

### Flagship+ Skills (X25-X30)

| Skill | Description |
|-------|-------------|
| `shopify-advanced-troubleshooting` | Query cost debug headers, request tracing, GraphQL introspection |
| `shopify-load-scale` | k6 load testing within rate limits, BFCM preparation, capacity planning |
| `shopify-reliability-patterns` | Circuit breakers, webhook idempotency, queue-based processing |
| `shopify-policy-guardrails` | Token detection ESLint rules, query cost budgets, App Store compliance |
| `shopify-architecture-variants` | Embedded app vs Hydrogen vs backend integration vs theme extension |
| `shopify-known-pitfalls` | Top 10 Shopify API anti-patterns with real wrong/right code examples |

### v2.0 Skills (N31-N38)

| Skill | Description |
|-------|-------------|
| `shopify-metafields-metaobjects` | Custom data modeling with `metafieldDefinitionCreate`, `metafieldsSet`, and `metaobjectCreate` |
| `shopify-functions` | WASM-sandboxed checkout logic for discounts, payments, and delivery customization |
| `shopify-storefront-headless` | Headless commerce with Storefront API, Cart API, and Hydrogen framework |
| `shopify-checkout-extensions` | Checkout UI Extensions replacing checkout.liquid (deprecated Aug 2025) |
| `shopify-theme-performance` | Core Web Vitals optimization, LCP fixes, Liquid profiling, `image_url` filter |
| `shopify-graphql-cost-optimizer` | Query cost prediction, reduction strategies, and bulk operation decisions |
| `shopify-b2b-wholesale` | B2B companies, catalogs, price lists, and wholesale checkout (Shopify Plus) |
| `shopify-ai-toolkit-wrapper` | MCP integration for GraphQL validation, Liquid linting, and doc search |

## Quick Start

### 1. Install the Pack

```bash
/plugin install shopify-pack@claude-code-plugins-plus
```

### 2. Create a Development Store

Go to [partners.shopify.com](https://partners.shopify.com) and create a free development store for testing.

### 3. Set Up Your First App

```bash
# Scaffold with Shopify CLI (recommended)
npm install -g @shopify/cli
shopify app init --template remix
cd my-shopify-app
shopify app dev
```

Or set up a standalone integration:

```bash
mkdir shopify-app && cd shopify-app
npm init -y
npm install @shopify/shopify-api dotenv
```

### 4. Make Your First API Call

```typescript
import "@shopify/shopify-api/adapters/node";
import { shopifyApi, LATEST_API_VERSION } from "@shopify/shopify-api";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: "localhost",
  apiVersion: LATEST_API_VERSION,
  isCustomStoreApp: true,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN!,
});

const session = shopify.session.customAppSession("your-store.myshopify.com");
const client = new shopify.clients.Graphql({ session });

const response = await client.request(`{
  shop { name }
  products(first: 5) {
    edges { node { id title status } }
  }
}`);

console.log("Store:", response.data.shop.name);
```

### 5. Go to Production

Follow `shopify-prod-checklist` for the complete launch checklist including GDPR webhooks, security review, and App Store submission requirements.

## Key Shopify Links

- [Shopify Admin GraphQL API](https://shopify.dev/docs/api/admin-graphql/latest) -- primary API for apps
- [Storefront GraphQL API](https://shopify.dev/docs/api/storefront) -- public storefront queries
- [API Rate Limits](https://shopify.dev/docs/api/usage/rate-limits) -- calculated query cost system
- [Webhook Topics](https://shopify.dev/docs/api/webhooks) -- all available event topics
- [Access Scopes](https://shopify.dev/docs/api/usage/access-scopes) -- permission reference
- [@shopify/shopify-api on npm](https://www.npmjs.com/package/@shopify/shopify-api) -- official Node.js SDK
- [Shopify App Store Requirements](https://shopify.dev/docs/apps/launch/app-requirements) -- submission checklist
- [Shopify Status](https://www.shopifystatus.com) -- platform status page

## License

MIT
