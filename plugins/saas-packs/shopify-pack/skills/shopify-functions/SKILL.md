---
name: shopify-functions
description: |
  Build Shopify Functions for custom discount, payment, and delivery logic in a WASM sandbox.
  Use when creating custom discount rules, payment customizations, delivery options,
  or cart transformations that run server-side at checkout.
  Trigger with phrases like "shopify functions", "shopify discounts",
  "shopify wasm", "custom discount function", "shopify checkout customization".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Functions

## Overview

Shopify Functions execute custom business logic in a WebAssembly sandbox at checkout: discounts, payment filtering, delivery customization, and cart transforms. They run server-side with strict constraints (11ms execution, 1MB memory, no network access) and replace Shopify Scripts.

## Prerequisites

- Shopify CLI 3.x+ installed (`npm install -g @shopify/cli`)
- Shopify Partners account with a development store
- App configured for the target function API type

## Instructions

### Step 1: Configure the Function Extension

```toml
# extensions/product-discount/shopify.extension.toml
api_version = "2025-01"
type = "product_discounts"

[[targeting]]
target = "purchase.product-discount.run"
input_query = "extensions/product-discount/input.graphql"
export = "run"
```

### Step 2: Define the Input Query

The input query declares what data your function receives at runtime:

```graphql
# extensions/product-discount/input.graphql
query Input {
  cart {
    lines {
      quantity
      merchandise {
        ... on ProductVariant {
          id
          product { hasAnyTag(tags: ["VIP-DISCOUNT"]) }
        }
      }
    }
  }
  discountNode {
    metafield(namespace: "$app:discount-config", key: "percentage") { value }
  }
}
```

### Step 3: Implement the Function

```typescript
// extensions/product-discount/src/run.ts
import type { Input, FunctionRunResult } from "../generated/api";

export function run(input: Input): FunctionRunResult {
  const percentage = parseFloat(input.discountNode?.metafield?.value ?? "0");
  if (percentage === 0) return { discounts: [], discountApplicationStrategy: "FIRST" };

  const targets = input.cart.lines
    .filter((line) => line.merchandise.product.hasAnyTag)
    .map((line) => ({ productVariant: { id: line.merchandise.id } }));

  return {
    discounts: [{
      targets,
      value: { percentage: { value: percentage.toString() } },
      message: `${percentage}% VIP Discount`,
    }],
    discountApplicationStrategy: "FIRST",
  };
}
```

### Step 4: Test and Deploy

```bash
shopify app function typegen          # Generate types from input query
shopify app function build            # Build to WASM
shopify app function run --input test-input.json  # Test locally
shopify app deploy                    # Deploy with app
```

See [function-types.md](references/function-types.md) for all function types, [input-output-schemas.md](references/input-output-schemas.md) for I/O shapes, and [wasm-constraints.md](references/wasm-constraints.md) for sandbox limitations.

## Output

- WASM binary deployed as a Shopify Function extension
- Custom discount/payment/delivery logic running server-side at checkout
- Type-safe input/output via generated TypeScript types
- Configurable via metafields (merchant-editable without code changes)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `FunctionError` | Runtime panic or unhandled exception in WASM | Add error handling; check optional fields for null |
| `FUNCTION_TOO_LARGE` | WASM binary exceeds 256KB | Tree-shake deps; use Rust for smaller binaries |
| Input query validation | Query references unavailable fields | Match `api_version` to available schema fields |
| Timeout (>11ms) | Function exceeds execution limit | Reduce iterations; pre-compute in metafields |

## Examples

### Creating a VIP Discount Function

Build a product discount function that applies a configurable percentage off for items tagged "VIP-DISCOUNT" using metafield-driven configuration.

See [Function Types](references/function-types.md) for all available function types and their targeting.

### Defining Input Queries and Output Schemas

Design the GraphQL input query that declares what cart data your function receives, and return the correctly shaped `FunctionRunResult`.

See [Input/Output Schemas](references/input-output-schemas.md) for I/O shapes per function type.

### Working Within WASM Sandbox Limits

Your function hits the 11ms execution timeout or 256KB binary size limit. Apply optimization strategies for the constrained WASM environment.

See [WASM Constraints](references/wasm-constraints.md) for sandbox limitations and workarounds.

## Resources

- [Shopify Functions Overview](https://shopify.dev/docs/apps/build/functions)
- [Product Discount Tutorial](https://shopify.dev/docs/apps/build/discounts/build-discount-function)
- [Function APIs Reference](https://shopify.dev/docs/api/functions)
- [WASM Limitations](https://shopify.dev/docs/apps/build/functions/input-output#limitations)
