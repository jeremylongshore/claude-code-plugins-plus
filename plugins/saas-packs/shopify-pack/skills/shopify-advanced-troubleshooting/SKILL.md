---
name: shopify-advanced-troubleshooting
description: |
  Debug complex Shopify API issues using cost analysis, request tracing,
  webhook delivery inspection, and GraphQL introspection.
  Use when encountering intermittent failures, throttling mysteries, or webhook delivery gaps.
  Trigger with phrases like "shopify hard bug", "shopify mystery error",
  "shopify deep debug", "difficult shopify issue", "shopify intermittent failure".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Advanced Troubleshooting

## Overview

Deep debugging for complex Shopify API issues: cost analysis with debug headers, webhook delivery inspection, GraphQL query introspection, and systematic isolation of intermittent failures.

## Prerequisites

- Access to Shopify admin and Partner Dashboard
- Familiarity with GraphQL and HTTP debugging
- `curl` and `jq` available

## Instructions

### Step 1: GraphQL Cost Analysis

When queries THROTTLE unexpectedly, use the cost debug header by adding `Shopify-GraphQL-Cost-Debug: 1` to your request. The response `extensions.cost` reveals why a query is expensive.

**Key:** `requestedQueryCost` is `first` multiplied through nested connections. `50 products * 20 variants * (1 + 5 metafields)` = high cost even if actual data is small.

### Step 2: Trace a Specific Request

Every Shopify response includes `X-Request-Id`. Capture it for support escalation:

```bash
curl -v -X POST "https://$STORE/admin/api/2025-04/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' 2>&1 | tee /tmp/shopify-debug.txt

grep -i "x-request-id" /tmp/shopify-debug.txt
```

### Step 3: Webhook Delivery Inspection

Inspect webhook delivery status in the Partner Dashboard, or query subscription health via API.

See [Webhook Status Query](references/webhook-status-query.md) for the complete query and common delivery failure patterns.

### Step 4: GraphQL Introspection for API Version Differences

Use introspection queries to check if specific fields or mutations exist in your API version. Query `__type` for field lists or `__schema` for available mutations filtered by prefix.

### Step 5: Systematic Isolation

Run a layer-by-layer diagnostic that tests DNS, TCP, TLS, HTTP, GraphQL, and rate limit state independently.

See [Layer-by-Layer Diagnostic](references/layer-by-layer-diagnostic.md) for the complete shell script.

### Step 6: Debug Intermittent Failures

Wrap Shopify calls in a debug logger that captures timing, cost, and error data for pattern analysis.

See [Debug Intermittent Failures](references/debug-intermittent-failures.md) for the complete TypeScript implementation.

## Output

- Query cost breakdown identifying expensive fields
- Request IDs captured for Shopify support
- Webhook delivery health verified
- Layer-by-layer isolation identifying failure point
- Debug log with timing patterns for intermittent issues

## Error Handling

| Issue | Root Cause Pattern | Solution |
|-------|-------------------|----------|
| Random THROTTLED errors | `requestedQueryCost` spikes on specific queries | Reduce `first:` and nested depth |
| Webhooks stop arriving | SSL certificate expired | Renew cert, check webhook subscriptions |
| 502 errors on GraphQL | Shopify infrastructure blip | Retry with backoff, capture X-Request-Id |
| Slow responses (> 5s) | Complex query with metafields | Remove `metafields` or reduce page size |
| Data inconsistency | Race condition between webhook and query | Use `updatedAt` filter, add idempotency |

## Examples

### Diagnosing Intermittent 502 Errors

A store experiences random 502 errors on product sync queries. Use the debug wrapper to capture timing and cost data across 100 requests, then analyze the pattern.

See [Debug Intermittent Failures](references/debug-intermittent-failures.md) for the complete TypeScript implementation.

### Isolating a Webhook Delivery Gap

Orders are created but the fulfillment webhook never fires. Run the webhook status query to check subscription health and delivery success rates.

See [Webhook Status Query](references/webhook-status-query.md) for the complete query and common delivery failure patterns.

### Pinpointing a Network Layer Failure

API calls fail sporadically from a specific server. Run the layer-by-layer diagnostic to test DNS, TCP, TLS, HTTP, and GraphQL independently.

See [Layer-by-Layer Diagnostic](references/layer-by-layer-diagnostic.md) for the complete shell script.

## Resources

- [Shopify GraphQL Cost Debug](https://shopify.dev/docs/api/usage/rate-limits#query-cost)
- [Webhook Troubleshooting](https://shopify.dev/docs/apps/build/webhooks/troubleshoot)
- [Shopify Partner Support](https://help.shopify.com/en/partners)
- [Shopify Community Forums](https://community.shopify.dev)
