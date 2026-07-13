# Bulk Product Import with productSet

The `productSet` mutation is idempotent — it creates or updates based on `handle`, making it ideal for migrations.

```typescript
const PRODUCT_SET = `
  mutation productSet($input: ProductSetInput!) {
    productSet(input: $input) {
      product {
        id
        title
        handle
        variants(first: 50) {
          edges {
            node { id sku price inventoryQuantity }
          }
        }
      }
      userErrors { field message code }
    }
  }
`;

// Migrate products in batches
async function migrateProducts(sourceProducts: SourceProduct[]): Promise<MigrationResult> {
  const results: MigrationResult = { success: 0, errors: [] };

  for (const product of sourceProducts) {
    try {
      const response = await client.request(PRODUCT_SET, {
        variables: {
          input: {
            title: product.name,
            handle: product.slug, // unique identifier for upsert
            descriptionHtml: product.description,
            vendor: product.brand,
            productType: product.category,
            tags: product.tags,
            status: "DRAFT", // Keep as draft until verified
            variants: product.variants.map((v) => ({
              price: String(v.price),
              sku: v.sku,
              barcode: v.barcode,
              optionValues: v.options.map((opt) => ({
                optionName: opt.name,
                name: opt.value,
              })),
            })),
            metafields: product.metadata?.map((m) => ({
              namespace: "migration",
              key: m.key,
              value: m.value,
              type: "single_line_text_field",
            })),
          },
        },
      });

      if (response.data.productSet.userErrors.length > 0) {
        results.errors.push({
          product: product.name,
          errors: response.data.productSet.userErrors,
        });
      } else {
        results.success++;
      }
    } catch (error) {
      results.errors.push({ product: product.name, errors: [{ message: (error as Error).message }] });
    }

    // Respect rate limits — pause between batches
    await new Promise((r) => setTimeout(r, 200));
  }

  return results;
}
```
