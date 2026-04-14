# Vitest Shopify API Mock Setup

Test setup with mocked Shopify API client for unit testing without hitting the real API.

```typescript
// tests/shopify-client.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the Shopify API client
vi.mock("@shopify/shopify-api", () => ({
  shopifyApi: vi.fn(() => ({
    clients: {
      Graphql: vi.fn().mockImplementation(() => ({
        request: vi.fn().mockResolvedValue({
          data: {
            products: {
              edges: [
                { node: { id: "gid://shopify/Product/1", title: "Test Product" } },
              ],
            },
          },
        }),
      })),
    },
    session: {
      customAppSession: vi.fn(() => ({ shop: "test.myshopify.com" })),
    },
  })),
}));

describe("Shopify Integration", () => {
  it("should fetch products", async () => {
    // Test your product-fetching logic here
  });

  it("should handle GraphQL errors", async () => {
    // Test error handling
  });
});
```

### package.json scripts

```json
{
  "scripts": {
    "dev": "shopify app dev",
    "build": "remix vite:build",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "lint": "eslint app/",
    "shopify": "shopify",
    "deploy": "shopify app deploy"
  }
}
```
