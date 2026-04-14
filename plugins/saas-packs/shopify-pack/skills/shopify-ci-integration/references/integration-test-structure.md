Vitest integration test structure for verifying Shopify store connectivity, scopes, and rate limit compliance.

```typescript
// tests/integration/shopify.test.ts
import { describe, it, expect, beforeAll } from "vitest";

const SKIP = !process.env.SHOPIFY_ACCESS_TOKEN;

describe.skipIf(SKIP)("Shopify Integration", () => {
  let client: any;

  beforeAll(() => {
    client = getGraphqlClient(process.env.SHOPIFY_STORE!);
  });

  it("should connect to store", async () => {
    const response = await client.request("{ shop { name } }");
    expect(response.data.shop.name).toBeTruthy();
  });

  it("should have required scopes", async () => {
    const response = await client.request(`{
      app { installation { accessScopes { handle } } }
    }`);
    const scopes = response.data.app.installation.accessScopes.map(
      (s: any) => s.handle
    );
    expect(scopes).toContain("read_products");
    expect(scopes).toContain("read_orders");
  });

  it("should query products within rate limits", async () => {
    const response = await client.request(`{
      products(first: 5) {
        edges { node { id title } }
      }
    }`);
    expect(response.extensions.cost.actualQueryCost).toBeLessThan(100);
  });
});
```
