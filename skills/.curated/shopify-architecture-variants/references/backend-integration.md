Variant C: Backend Integration (Standalone) project structure and custom app client setup.

**Best for:** ERP sync, warehouse management, analytics, multi-channel integration

**When to use:** You're connecting Shopify to other systems -- no merchant-facing UI needed.

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

**Auth:** Custom app access token (`shpat_xxx`) -- no OAuth flow needed

```typescript
import { LATEST_API_VERSION, shopifyApi } from "@shopify/shopify-api";

// Custom app — direct API access, no merchant UI
const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: "localhost",
  apiVersion: LATEST_API_VERSION,
  isCustomStoreApp: true,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN!,
});
```
