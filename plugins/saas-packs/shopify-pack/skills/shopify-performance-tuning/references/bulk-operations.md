# Bulk Operations for Large Exports

Shopify bulk operations bypass rate limits and are designed for exporting large datasets asynchronously.

```typescript
// Step 1: Start bulk operation
const START_BULK = `
  mutation {
    bulkOperationRunQuery(query: """
      {
        products {
          edges {
            node {
              id
              title
              handle
              variants {
                edges {
                  node {
                    id
                    sku
                    price
                    inventoryQuantity
                  }
                }
              }
            }
          }
        }
      }
    """) {
      bulkOperation {
        id
        status
      }
      userErrors { field message }
    }
  }
`;

// Step 2: Poll for completion
const CHECK_BULK = `{
  currentBulkOperation {
    id
    status       # CREATED, RUNNING, COMPLETED, FAILED
    errorCode
    objectCount
    fileSize
    url          # JSONL download URL when COMPLETED
    createdAt
  }
}`;

// Step 3: Download results (JSONL format — one JSON object per line)
// const response = await fetch(bulkOperation.url);
// Each line: {"id":"gid://shopify/Product/123","title":"Widget",...}
```

### Performance Comparison

| Approach | 10K Products Export | Rate Limit Impact |
|----------|-------------------|-------------------|
| Paginated (first: 250) | 40 queries, ~60s | Uses ~6,000 points |
| Paginated (first: 50) | 200 queries, ~300s | Uses ~22,000 points |
| Bulk Operation | 1 query + poll, ~30s | Minimal impact |
