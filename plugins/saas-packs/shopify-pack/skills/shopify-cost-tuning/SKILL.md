---
name: shopify-cost-tuning
description: |
  Optimize Shopify app costs through plan selection, API usage monitoring,
  and Shopify Plus upgrade analysis.
  Trigger with phrases like "shopify cost", "shopify billing",
  "shopify pricing", "shopify Plus worth it", "shopify API usage", "reduce shopify costs".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Cost Tuning

## Overview

Optimize Shopify app and API costs through plan analysis, API usage monitoring, and strategies to minimize billable API calls. Covers Shopify store plans, Partner app billing, and API efficiency.

## Prerequisites

- Access to Shopify Partner Dashboard for app billing
- Understanding of current API usage patterns
- Knowledge of merchant's Shopify plan

## Instructions

### Step 1: Understand Shopify Plan Rate Limits

API rate limits are determined by the **merchant's** plan, not your app:

| Merchant Plan | REST Bucket | REST Leak Rate | GraphQL Points | GraphQL Restore |
|--------------|-------------|----------------|----------------|-----------------|
| Basic Shopify | 40 requests | 2/second | 1,000 points | 50/second |
| Shopify | 40 requests | 2/second | 1,000 points | 50/second |
| Advanced | 40 requests | 2/second | 1,000 points | 50/second |
| Shopify Plus | 80 requests | 4/second | 2,000 points | 100/second |

**Key insight:** Upgrading from Basic to Advanced doesn't help rate limits. Only Plus doubles them.

### Step 2: App Billing API

If your app charges merchants, use the GraphQL App Billing API:

```typescript
// Create a recurring charge
const CREATE_SUBSCRIPTION = `
  mutation appSubscriptionCreate(
    $name: String!,
    $lineItems: [AppSubscriptionLineItemInput!]!,
    $returnUrl: URL!,
    $test: Boolean
  ) {
    appSubscriptionCreate(
      name: $name,
      lineItems: $lineItems,
      returnUrl: $returnUrl,
      test: $test
    ) {
      appSubscription {
        id
        status
      }
      confirmationUrl
      userErrors { field message }
    }
  }
`;

const response = await client.request(CREATE_SUBSCRIPTION, {
  variables: {
    name: "Pro Plan",
    returnUrl: "https://your-app.com/billing/callback",
    test: process.env.NODE_ENV !== "production", // test charges in dev
    lineItems: [
      {
        plan: {
          appRecurringPricingDetails: {
            price: { amount: 9.99, currencyCode: "USD" },
            interval: "EVERY_30_DAYS",
          },
        },
      },
    ],
  },
});

// Redirect merchant to confirmationUrl to approve the charge
```

### Step 3: Monitor API Usage

```typescript
class ShopifyUsageTracker {
  private graphqlCosts: number[] = [];
  private restCalls: number = 0;
  private startOfPeriod: Date = new Date();

  trackGraphqlCost(extensions: any): void {
    if (extensions?.cost?.actualQueryCost) {
      this.graphqlCosts.push(extensions.cost.actualQueryCost);
    }
  }

  trackRestCall(): void {
    this.restCalls++;
  }

  getReport(): UsageReport {
    const totalGraphqlCost = this.graphqlCosts.reduce((a, b) => a + b, 0);
    const avgCost = totalGraphqlCost / (this.graphqlCosts.length || 1);

    return {
      period: {
        start: this.startOfPeriod,
        end: new Date(),
      },
      graphql: {
        totalQueries: this.graphqlCosts.length,
        totalCost: totalGraphqlCost,
        averageCost: Math.round(avgCost),
        maxSingleCost: Math.max(...this.graphqlCosts, 0),
      },
      rest: {
        totalCalls: this.restCalls,
      },
      recommendation: avgCost > 500
        ? "High average query cost — optimize field selection"
        : avgCost > 100
        ? "Moderate cost — consider bulk operations for large queries"
        : "Efficient usage",
    };
  }
}
```

### Step 4: Cost Reduction Strategies

**Strategy 1: Replace REST with GraphQL** (get only what you need)

```typescript
// REST returns ALL fields — 5KB+ per product
// GET /admin/api/2024-10/products/123.json
// Returns: title, body_html, vendor, product_type, handle, template_suffix,
//          published_scope, tags, admin_graphql_api_id, variants[], images[],
//          options[], ... (everything)

// GraphQL returns ONLY requested fields — 200 bytes
const response = await client.request(`{
  product(id: "gid://shopify/Product/123") {
    title
    status
    totalInventory
  }
}`);
```

**Strategy 2: Use Bulk Operations for exports**

```typescript
// Instead of 200 paginated queries (200 * ~100 cost = 20,000 points):
// Use 1 bulk operation (minimal cost, runs in background)
await client.request(`
  mutation { bulkOperationRunQuery(query: """
    { products { edges { node { id title } } } }
  """) { bulkOperation { id status } userErrors { message } } }
`);
```

**Strategy 3: Cache and invalidate via webhooks**

```typescript
// Instead of re-querying products every request:
// Cache products, invalidate only when products/update webhook fires
// Saves: hundreds of queries per hour for read-heavy apps
```

**Strategy 4: Use Storefront API for public data**

```typescript
// Storefront API has separate rate limits
// Use it for: product listings, collections, search
// Keep Admin API for: order management, customer data, fulfillments
```

## Output

- API usage monitored with cost tracking
- Rate limit-efficient query patterns
- App billing configured (if charging merchants)
- Cost reduction strategies applied

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Frequent throttling | High query cost | Reduce fields, use bulk ops |
| High hosting costs | Too many API calls | Cache responses, use webhooks |
| App billing rejection | Test mode not set | Use `test: true` in development |
| Merchant cancels | Unexpected charges | Clear billing in app onboarding |

## Examples

### Quick Usage Check

```typescript
// After every GraphQL call, log the cost
const response = await client.request(query);
const cost = response.extensions?.cost;
if (cost) {
  console.log(
    `Query cost: ${cost.actualQueryCost}/${cost.throttleStatus.maximumAvailable} ` +
    `(${cost.throttleStatus.currentlyAvailable} available)`
  );
}
```

## Resources

- [Shopify API Rate Limits](https://shopify.dev/docs/api/usage/rate-limits)
- [App Billing API](https://shopify.dev/docs/apps/build/billing)
- [Shopify Pricing](https://www.shopify.com/pricing)
- [Shopify Plus Rate Limits](https://shopify.dev/changelog/increased-admin-api-rate-limits-for-shopify-plus)

## Next Steps

For architecture patterns, see `shopify-reference-architecture`.
