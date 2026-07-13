Complete hello world script that connects to a Shopify store and queries shop info and products via the GraphQL Admin API.

```typescript
// hello-shopify.ts
import "@shopify/shopify-api/adapters/node";
import { shopifyApi, LATEST_API_VERSION } from "@shopify/shopify-api";
import "dotenv/config";

const shopify = shopifyApi({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  hostName: "localhost",
  apiVersion: LATEST_API_VERSION,
  isCustomStoreApp: true,
  adminApiAccessToken: process.env.SHOPIFY_ACCESS_TOKEN!,
});

async function main() {
  const session = shopify.session.customAppSession(
    process.env.SHOPIFY_STORE!
  );

  const client = new shopify.clients.Graphql({ session });

  // Query shop info
  const shopInfo = await client.request(`{
    shop {
      name
      currencyCode
      primaryDomain { url }
    }
  }`);
  console.log("Store:", shopInfo.data.shop.name);
  console.log("Currency:", shopInfo.data.shop.currencyCode);

  // Query first 5 products
  const products = await client.request(`{
    products(first: 5) {
      edges {
        node {
          id
          title
          status
          totalInventory
          variants(first: 3) {
            edges {
              node {
                title
                price
                sku
                inventoryQuantity
              }
            }
          }
        }
      }
    }
  }`);

  console.log("\nProducts:");
  for (const edge of products.data.products.edges) {
    const p = edge.node;
    console.log(`  - ${p.title} (${p.status}, ${p.totalInventory} in stock)`);
    for (const v of p.variants.edges) {
      console.log(`      Variant: ${v.node.title} — $${v.node.price} (SKU: ${v.node.sku})`);
    }
  }

  console.log("\nSuccess! Your Shopify connection is working.");
}

main().catch((err) => {
  console.error("Failed:", err.message);
  if (err.response) {
    console.error("Response:", JSON.stringify(err.response.body, null, 2));
  }
  process.exit(1);
});
```
