# Typed GraphQL Client Wrapper

Full singleton client setup with session caching and typed query helper.

```typescript
// src/shopify/client.ts
import "@shopify/shopify-api/adapters/node";
import { shopifyApi, Session, GraphqlClient, LATEST_API_VERSION } from "@shopify/shopify-api";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: process.env.SHOPIFY_HOST_NAME!,
  apiVersion: LATEST_API_VERSION,
  isCustomStoreApp: !!process.env.SHOPIFY_ACCESS_TOKEN,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN,
});

// Singleton session cache per shop
const sessionCache = new Map<string, Session>();

export function getSession(shop: string): Session {
  if (!sessionCache.has(shop)) {
    const session = shopify.session.customAppSession(shop);
    sessionCache.set(shop, session);
  }
  return sessionCache.get(shop)!;
}

export function getGraphqlClient(shop: string): GraphqlClient {
  return new shopify.clients.Graphql({
    session: getSession(shop),
  });
}

// Typed query helper
export async function shopifyQuery<T = any>(
  shop: string,
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  const client = getGraphqlClient(shop);
  const response = await client.request(query, { variables });
  return response.data as T;
}
```
