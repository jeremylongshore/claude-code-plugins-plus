---
name: shopify-cost-tuning
description: |
  Optimize Shopify app costs through plan selection, API usage monitoring,
  and Shopify Plus upgrade analysis.
  Use when analyzing API spend, choosing between Shopify plans, or reducing billable API calls.
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

If your app charges merchants, use the GraphQL `appSubscriptionCreate` mutation to create recurring charges. Set `test: true` in development to avoid real billing.

See [App Billing API](references/app-billing-api.md) for the complete mutation and variable setup.

### Step 3: Monitor API Usage

Track GraphQL query costs and REST call counts over time to identify optimization opportunities. Log `extensions.cost.actualQueryCost` from every GraphQL response.

See [Usage Tracker Class](references/usage-tracker-class.md) for a complete tracking implementation with reporting.

### Step 4: Cost Reduction Strategies

Four key strategies: replace REST with GraphQL for targeted field selection, use bulk operations for exports, cache responses and invalidate via webhooks, and use Storefront API for public data.

See [Cost Reduction Strategies](references/cost-reduction-strategies.md) for code examples of each approach.

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
