Smart (automated) collection creation with rule-based product matching.

```typescript
// Create a smart (automated) collection
const CREATE_SMART_COLLECTION = `
  mutation collectionCreate($input: CollectionInput!) {
    collectionCreate(input: $input) {
      collection {
        id
        title
        handle
        productsCount
        ruleSet {
          appliedDisjunctively
          rules { column relation condition }
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(CREATE_SMART_COLLECTION, {
  variables: {
    input: {
      title: "Summer Sale",
      descriptionHtml: "<p>All items on summer sale</p>",
      ruleSet: {
        appliedDisjunctively: false, // AND logic
        rules: [
          { column: "TAG", relation: "EQUALS", condition: "sale" },
          { column: "PRODUCT_TYPE", relation: "EQUALS", condition: "Apparel" },
        ],
      },
    },
  },
});
```
