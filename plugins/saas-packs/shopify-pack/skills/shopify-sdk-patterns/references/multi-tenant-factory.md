# Multi-Tenant Client Factory

Client factory for apps installed on multiple stores with per-merchant session isolation and eviction on uninstall.

```typescript
// src/shopify/factory.ts
// For apps installed on multiple stores

import { Session, GraphqlClient } from "@shopify/shopify-api";

interface TenantConfig {
  shop: string;
  accessToken: string;
}

class ShopifyClientFactory {
  private clients = new Map<string, GraphqlClient>();

  getClient(config: TenantConfig): GraphqlClient {
    if (!this.clients.has(config.shop)) {
      const session = new Session({
        id: config.shop,
        shop: config.shop,
        state: "",
        isOnline: false,
        accessToken: config.accessToken,
      });

      this.clients.set(
        config.shop,
        new shopify.clients.Graphql({ session })
      );
    }
    return this.clients.get(config.shop)!;
  }

  // Evict when merchant uninstalls
  removeClient(shop: string): void {
    this.clients.delete(shop);
  }
}

export const clientFactory = new ShopifyClientFactory();
```
