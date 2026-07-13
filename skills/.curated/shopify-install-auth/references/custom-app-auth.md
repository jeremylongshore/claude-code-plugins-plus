# Custom App / Private App Auth

For custom apps installed on a single store, use a permanent access token — no OAuth flow needed.

```typescript
// Custom app — no OAuth needed, use Admin API access token directly
import "@shopify/shopify-api/adapters/node";
import { shopifyApi, LATEST_API_VERSION } from "@shopify/shopify-api";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: process.env.SHOPIFY_HOST_NAME!,
  apiVersion: LATEST_API_VERSION,
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
