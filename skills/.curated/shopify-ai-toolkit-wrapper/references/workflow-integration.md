Combining the Shopify MCP server with other shopify-pack skills for efficient development workflows.

## Workflow: Validate-Then-Execute

Use the MCP server's schema validation before running any GraphQL mutation from other shopify-pack skills:

```
1. Write your GraphQL query/mutation
2. MCP validates against live schema → catches errors before execution
3. MCP checks query cost → avoid THROTTLED/MAX_COST_EXCEEDED
4. Execute the validated query via @shopify/shopify-api
```

### Example: Product Creation Pipeline

```typescript
// Step 1: Use MCP to verify ProductCreateInput shape for your API version
// The MCP server introspects the schema and confirms field names

// Step 2: Use shopify-graphql-cost-optimizer to check estimated cost
// products(first: 10) with 5 fields ≈ 52 points (safe)

// Step 3: Execute using the pattern from shopify-core-workflow-a
import { LATEST_API_VERSION } from "@shopify/shopify-api";

const response = await client.request(CREATE_PRODUCT, {
  variables: {
    input: {
      title: "New Product",
      status: "DRAFT",
    },
  },
});

// Step 4: Validate response using shopify-common-errors patterns
if (response.data.productCreate.userErrors.length > 0) {
  // Handle per shopify-common-errors skill
}
```

## Workflow: Theme Development Loop

Combine MCP linting with theme performance optimization:

```
1. Edit Liquid template
2. MCP lints for deprecated filters (img_url → image_url)
3. MCP checks for anti-patterns (include → render)
4. Apply shopify-theme-performance optimizations
5. Run Liquid profiler (?profile=true) to verify improvement
```

### Example: Fix Deprecated Filters

```liquid
{% comment %} MCP flags this as deprecated {% endcomment %}
{{ product.featured_image | img_url: '800x' }}

{% comment %} Apply image-optimization.md reference pattern {% endcomment %}
{{ product.featured_image | image_url: width: 800 | image_tag:
    loading: 'lazy',
    sizes: '(max-width: 749px) 100vw, 50vw',
    widths: '400,600,800' }}
```

## Workflow: B2B Setup with Validation

When setting up B2B using shopify-b2b-wholesale, validate each step:

```
1. MCP confirms B2B mutations exist for your API version
2. MCP verifies required scopes (read_customers, write_customers)
3. Run companyCreate → MCP validates input shape
4. Run catalogCreate → MCP checks catalog limit for plan
5. Run priceListCreate → MCP confirms pricing fields
```

## Workflow: Cost-Aware Bulk Operations

Decide between paginated queries and bulk operations:

```
1. Write initial query
2. MCP predicts requestedQueryCost
3. If cost > 500: use shopify-graphql-cost-optimizer splitting patterns
4. If total items > 250: switch to bulk operations (shopify-graphql-cost-optimizer)
5. MCP validates bulk query syntax (no first/last params allowed)
```

### Decision Matrix

| Scenario | Approach | Skill Reference |
|----------|----------|----------------|
| < 50 items, interactive | Direct query | shopify-core-workflow-a |
| 50-250 items, background | Paginated with cursor | shopify-graphql-cost-optimizer (query-splitting.md) |
| > 250 items, export | Bulk operations | shopify-graphql-cost-optimizer (bulk-operations.md) |
| Real-time sync | Webhooks | shopify-webhooks-events |
| Rate-limited operation | Throttle-aware client | shopify-rate-limits |

## Combining MCP Tools in Claude Code

When working in Claude Code with the Shopify MCP server configured, you can chain capabilities:

```
User: "Create a new product collection for summer items"

Claude Code workflow:
1. [MCP] Search docs for collectionCreate mutation shape
2. [MCP] Validate the mutation against store's schema
3. [shopify-core-workflow-a] Use the collection creation pattern
4. [shopify-graphql-cost-optimizer] Verify query cost is reasonable
5. Execute the validated, cost-checked mutation
```

This creates a safety net where queries are validated and cost-checked before hitting the Shopify API, reducing wasted API calls and avoiding throttling.
