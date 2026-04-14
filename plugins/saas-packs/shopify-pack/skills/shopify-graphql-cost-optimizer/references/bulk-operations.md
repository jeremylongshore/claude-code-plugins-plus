Complete guide to Shopify's bulk operation API for large data exports that bypass the query cost system.

## When to Use Bulk Operations

- Exporting more than 250 items of any resource type
- Syncing entire product catalogs to external systems
- Generating reports across all orders/customers
- Any operation where cursor-based pagination would require 10+ API calls

## Starting a Bulk Query

```typescript
const BULK_OPERATION_RUN = `
  mutation bulkOperationRunQuery($query: String!) {
    bulkOperationRunQuery(query: $query) {
      bulkOperation {
        id
        status
        url
      }
      userErrors {
        field
        message
      }
    }
  }
`;

const response = await client.request(BULK_OPERATION_RUN, {
  variables: {
    query: `{
      products {
        edges {
          node {
            id
            title
            handle
            status
            vendor
            productType
            tags
            variants {
              edges {
                node {
                  id
                  title
                  sku
                  price
                  inventoryQuantity
                  barcode
                }
              }
            }
          }
        }
      }
    }`,
  },
});

const bulkOperationId = response.data.bulkOperationRunQuery.bulkOperation.id;
```

**Important**: Bulk query syntax differs from normal queries:
- No `first`/`last` pagination arguments
- No `after`/`before` cursors
- Connections return ALL items automatically
- Only one bulk operation can run per app per store at a time

## Polling for Completion

```typescript
const POLL_OPERATION = `
  query currentBulkOperation {
    currentBulkOperation {
      id
      status
      errorCode
      objectCount
      fileSize
      url
      createdAt
      completedAt
    }
  }
`;

async function waitForBulkOperation(client: any): Promise<string | null> {
  while (true) {
    const response = await client.request(POLL_OPERATION);
    const operation = response.data.currentBulkOperation;

    switch (operation.status) {
      case "COMPLETED":
        console.log(
          `Bulk operation complete: ${operation.objectCount} objects, ` +
          `${(operation.fileSize / 1024 / 1024).toFixed(1)}MB`
        );
        return operation.url; // JSONL download URL

      case "FAILED":
        console.error(`Bulk operation failed: ${operation.errorCode}`);
        return null;

      case "CANCELED":
        console.warn("Bulk operation was canceled");
        return null;

      case "RUNNING":
      case "CREATED":
        console.log(`Status: ${operation.status}, objects so far: ${operation.objectCount}`);
        await new Promise((r) => setTimeout(r, 3000)); // Poll every 3 seconds
        break;

      default:
        throw new Error(`Unknown status: ${operation.status}`);
    }
  }
}
```

## Downloading and Parsing JSONL

The result is a JSONL (JSON Lines) file where each line is an object. Parent-child relationships use `__parentId`:

```typescript
import { createReadStream } from "fs";
import { createInterface } from "readline";

async function parseBulkResults(url: string) {
  const response = await fetch(url);
  const text = await response.text();
  const lines = text.trim().split("\n");

  const products: Map<string, any> = new Map();
  const variants: any[] = [];

  for (const line of lines) {
    const obj = JSON.parse(line);

    if (obj.id.includes("Product") && !obj.id.includes("Variant")) {
      products.set(obj.id, { ...obj, variants: [] });
    } else if (obj.id.includes("ProductVariant")) {
      variants.push(obj);
    }
  }

  // Link variants to products via __parentId
  for (const variant of variants) {
    const product = products.get(variant.__parentId);
    if (product) {
      product.variants.push(variant);
    }
  }

  return Array.from(products.values());
}
```

### Example JSONL Output

```jsonl
{"id":"gid://shopify/Product/123","title":"T-Shirt","handle":"t-shirt","status":"ACTIVE"}
{"id":"gid://shopify/ProductVariant/456","title":"Small","sku":"TSH-S","price":"29.99","__parentId":"gid://shopify/Product/123"}
{"id":"gid://shopify/ProductVariant/789","title":"Medium","sku":"TSH-M","price":"29.99","__parentId":"gid://shopify/Product/123"}
{"id":"gid://shopify/Product/234","title":"Hoodie","handle":"hoodie","status":"ACTIVE"}
{"id":"gid://shopify/ProductVariant/567","title":"Large","sku":"HOO-L","price":"59.99","__parentId":"gid://shopify/Product/234"}
```

## Using Webhooks Instead of Polling

For production, subscribe to the `BULK_OPERATIONS_FINISH` webhook:

```typescript
const WEBHOOK_CREATE = `
  mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
    webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
      webhookSubscription { id }
      userErrors { field message }
    }
  }
`;

await client.request(WEBHOOK_CREATE, {
  variables: {
    topic: "BULK_OPERATIONS_FINISH",
    webhookSubscription: {
      callbackUrl: "https://your-app.com/webhooks/bulk-complete",
      format: "JSON",
    },
  },
});
```

The webhook payload includes the download URL:

```json
{
  "admin_graphql_api_id": "gid://shopify/BulkOperation/123",
  "completed_at": "2026-01-15T10:30:00Z",
  "status": "completed",
  "type": "query",
  "url": "https://storage.googleapis.com/shopify-tiers-assets-prod/bulk-operation/..."
}
```

## Error States

| `errorCode` | Meaning | Recovery |
|-------------|---------|----------|
| `ACCESS_DENIED` | App lacks required scopes | Check app scopes in partner dashboard |
| `INTERNAL_SERVER_ERROR` | Shopify-side failure | Retry after 60 seconds |
| `TIMEOUT` | Query took too long (>24 hours) | Simplify query, reduce fields |

## Bulk Mutations

For writing data in bulk (e.g., updating thousands of products), use `bulkOperationRunMutation`:

```typescript
const BULK_MUTATION = `
  mutation bulkOperationRunMutation(
    $mutation: String!,
    $stagedUploadPath: String!
  ) {
    bulkOperationRunMutation(
      mutation: $mutation,
      stagedUploadPath: $stagedUploadPath
    ) {
      bulkOperation { id status }
      userErrors { field message }
    }
  }
`;
```

This requires first uploading a JSONL file via staged uploads, then running the mutation against it.
