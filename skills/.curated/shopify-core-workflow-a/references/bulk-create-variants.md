Bulk variant creation with pricing, SKU, barcode, option values, and inventory quantities.

```typescript
// Create variants in bulk
const BULK_CREATE_VARIANTS = `
  mutation productVariantsBulkCreate(
    $productId: ID!,
    $variants: [ProductVariantsBulkInput!]!
  ) {
    productVariantsBulkCreate(productId: $productId, variants: $variants) {
      productVariants {
        id
        title
        price
        sku
        barcode
        inventoryQuantity
        selectedOptions { name value }
      }
      userErrors {
        field
        message
        code
      }
    }
  }
`;

await client.request(BULK_CREATE_VARIANTS, {
  variables: {
    productId: "gid://shopify/Product/1234567890",
    variants: [
      {
        price: "29.99",
        sku: "TSH-BLK-S",
        barcode: "1234567890123",
        optionValues: [
          { optionName: "Color", name: "Black" },
          { optionName: "Size", name: "S" },
        ],
        inventoryQuantities: [
          {
            availableQuantity: 100,
            locationId: "gid://shopify/Location/1234",
          },
        ],
      },
    ],
  },
});
```
