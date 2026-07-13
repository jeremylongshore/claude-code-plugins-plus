# Inventory Levels & URL Redirects

Post-product-import steps: setting inventory quantities at locations and creating URL redirects to preserve SEO.

## Set Inventory Levels

```typescript
// After products are created, set inventory quantities
const SET_INVENTORY = `
  mutation inventorySetQuantities($input: InventorySetQuantitiesInput!) {
    inventorySetQuantities(input: $input) {
      inventoryAdjustmentGroup {
        reason
        changes {
          name
          delta
          quantityAfterChange
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(SET_INVENTORY, {
  variables: {
    input: {
      reason: "correction",
      name: "available",
      quantities: [
        {
          inventoryItemId: "gid://shopify/InventoryItem/12345",
          locationId: "gid://shopify/Location/67890",
          quantity: 100,
        },
      ],
    },
  },
});
```

## URL Redirects (SEO Preservation)

```typescript
// Preserve old URLs by creating redirects
const CREATE_REDIRECT = `
  mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
    urlRedirectCreate(urlRedirect: $urlRedirect) {
      urlRedirect { id path target }
      userErrors { field message }
    }
  }
`;

// Map old URLs to new Shopify URLs
for (const redirect of urlMappings) {
  await client.request(CREATE_REDIRECT, {
    variables: {
      urlRedirect: {
        path: redirect.oldPath,     // "/old-product-page"
        target: redirect.newPath,   // "/products/new-handle"
      },
    },
  });
}
```
