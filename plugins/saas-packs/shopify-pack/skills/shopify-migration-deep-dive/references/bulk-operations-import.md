# Bulk Operations for Large Imports

For importing thousands of products, use Shopify's staged uploads combined with bulk mutation. This avoids rate limit issues by offloading the processing to Shopify's infrastructure.

```typescript
// Step 1: Create a staged upload target
const STAGED_UPLOAD = `
  mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
    stagedUploadsCreate(input: $input) {
      stagedTargets {
        url
        resourceUrl
        parameters { name value }
      }
      userErrors { field message }
    }
  }
`;

const uploadTarget = await client.request(STAGED_UPLOAD, {
  variables: {
    input: [{
      resource: "BULK_MUTATION_VARIABLES",
      filename: "products.jsonl",
      mimeType: "text/jsonl",
      httpMethod: "POST",
    }],
  },
});

// Step 2: Upload JSONL file to the staged target
// Each line is the variables for one mutation call
const jsonlContent = products.map((p) =>
  JSON.stringify({ input: { title: p.name, handle: p.slug } })
).join("\n");

// Upload to the staged target URL...

// Step 3: Run bulk mutation
const BULK_MUTATION = `
  mutation bulkOperationRunMutation($mutation: String!, $stagedUploadPath: String!) {
    bulkOperationRunMutation(mutation: $mutation, stagedUploadPath: $stagedUploadPath) {
      bulkOperation { id status }
      userErrors { field message }
    }
  }
`;
```
