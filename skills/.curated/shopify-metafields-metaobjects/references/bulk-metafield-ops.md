Bulk metafield operations for setting and deleting metafields across many resources.

## Bulk Set via metafieldsSet

The `metafieldsSet` mutation accepts up to 25 metafield inputs per call. Each input targets a specific owner resource.

```typescript
const BULK_SET = `
  mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
    metafieldsSet(metafields: $metafields) {
      metafields {
        id
        namespace
        key
        value
        owner { ... on Product { id title } }
      }
      userErrors { field message code }
    }
  }
`;

// Set metafields on multiple products in one call (max 25 per mutation)
await client.request(BULK_SET, {
  variables: {
    metafields: [
      {
        ownerId: "gid://shopify/Product/111",
        namespace: "custom",
        key: "care_instructions",
        value: "Dry clean only",
        type: "single_line_text_field",
      },
      {
        ownerId: "gid://shopify/Product/222",
        namespace: "custom",
        key: "care_instructions",
        value: "Machine wash warm",
        type: "single_line_text_field",
      },
      // ...up to 25 total
    ],
  },
});
```

## Bulk Delete

```typescript
const BULK_DELETE = `
  mutation metafieldsDelete($metafields: [MetafieldIdentifierInput!]!) {
    metafieldsDelete(metafields: $metafields) {
      deletedMetafields { ownerId namespace key }
      userErrors { field message }
    }
  }
`;

await client.request(BULK_DELETE, {
  variables: {
    metafields: [
      {
        ownerId: "gid://shopify/Product/111",
        namespace: "custom",
        key: "care_instructions",
      },
      {
        ownerId: "gid://shopify/Product/222",
        namespace: "custom",
        key: "care_instructions",
      },
    ],
  },
});
```

## Large-Scale Operations with Bulk API

For thousands of resources, use Shopify's `bulkOperationRunMutation`:

```typescript
const BULK_MUTATION = `
  mutation bulkOperationRunMutation($mutation: String!, $stagedUploadPath: String!) {
    bulkOperationRunMutation(
      mutation: $mutation,
      stagedUploadPath: $stagedUploadPath
    ) {
      bulkOperation { id status }
      userErrors { field message }
    }
  }
`;

// 1. Stage upload a JSONL file with one mutation per line
// 2. Each line: {"input":{"ownerId":"gid://shopify/Product/1","namespace":"custom","key":"tag","value":"sale","type":"single_line_text_field"}}
// 3. The mutation string references the metafieldsSet mutation
// 4. Poll bulkOperation for completion
```

### JSONL File Format

```jsonl
{"input":{"ownerId":"gid://shopify/Product/111","namespace":"custom","key":"sale_price","value":"19.99","type":"number_decimal"}}
{"input":{"ownerId":"gid://shopify/Product/222","namespace":"custom","key":"sale_price","value":"24.99","type":"number_decimal"}}
{"input":{"ownerId":"gid://shopify/Product/333","namespace":"custom","key":"sale_price","value":"14.99","type":"number_decimal"}}
```

## Rate Limit Considerations

- `metafieldsSet`: Each call costs query points based on input count. Budget ~10 points per call.
- `bulkOperationRunMutation`: No direct cost, but only one bulk operation runs at a time per app.
- Polling: Check `bulkOperation.status` every 5-10 seconds. Statuses: `CREATED`, `RUNNING`, `COMPLETED`, `FAILED`.
