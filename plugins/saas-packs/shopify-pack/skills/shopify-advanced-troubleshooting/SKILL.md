---
name: shopify-advanced-troubleshooting
description: |
  Debug complex Shopify API issues using cost analysis, request tracing,
  webhook delivery inspection, and GraphQL introspection.
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

When queries THROTTLE unexpectedly, use the cost debug header:

```bash
# Get detailed per-field cost breakdown
curl -X POST "https://$STORE/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Shopify-GraphQL-Cost-Debug: 1" \
  -d '{
    "query": "{ products(first: 50) { edges { node { id title variants(first: 20) { edges { node { id price metafields(first: 5) { edges { node { key value } } } } } } } } } }"
  }' | jq '.extensions.cost'
```

Response shows why the cost is high:
```json
{
  "requestedQueryCost": 1552,
  "actualQueryCost": 234,
  "throttleStatus": {
    "maximumAvailable": 1000.0,
    "currentlyAvailable": 766.0,
    "restoreRate": 50.0
  }
}
```

**Key:** `requestedQueryCost` is `first` multiplied through nested connections. `50 products * 20 variants * (1 + 5 metafields)` = high cost even if actual data is small.

### Step 2: Trace a Specific Request

Every Shopify response includes `X-Request-Id`. Capture it for support:

```bash
# Capture full response headers and body
curl -v -X POST "https://$STORE/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' 2>&1 | tee /tmp/shopify-debug.txt

# Extract the request ID
grep -i "x-request-id" /tmp/shopify-debug.txt
```

### Step 3: Webhook Delivery Inspection

Inspect webhook delivery status in the Partner Dashboard, or query via API:

```typescript
// Check webhook subscription health
const WEBHOOK_STATUS = `{
  webhookSubscriptions(first: 50) {
    edges {
      node {
        id
        topic
        endpoint {
          ... on WebhookHttpEndpoint {
            callbackUrl
          }
        }
        format
        apiVersion
        createdAt
        updatedAt
      }
    }
  }
}`;

// Common webhook delivery issues:
// 1. Your endpoint returns non-200 — Shopify retries 19 times over 48 hours
// 2. Response takes > 5 seconds — Shopify considers it failed
// 3. Endpoint is HTTP (not HTTPS) — Shopify won't deliver
// 4. SSL certificate invalid — delivery fails silently
```

### Step 4: GraphQL Introspection for API Version Differences

```bash
# Check if a specific field exists in your API version
curl -X POST "https://$STORE/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __type(name: \"Product\") { fields { name type { name kind } } } }"
  }' | jq '.data.__type.fields[] | {name, type: .type.name}'

# Check available mutations
curl -X POST "https://$STORE/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { mutationType { fields { name description } } } }"
  }' | jq '.data.__schema.mutationType.fields[] | select(.name | startswith("product"))'
```

### Step 5: Systematic Isolation

```bash
#!/bin/bash
# shopify-layer-test.sh — test each layer independently
STORE="$SHOPIFY_STORE"
TOKEN="$SHOPIFY_ACCESS_TOKEN"
VERSION="2024-10"

echo "=== Layer-by-Layer Diagnostic ==="

# Layer 1: DNS
echo -n "1. DNS: "
dig +short "$STORE" >/dev/null 2>&1 && echo "OK" || echo "FAIL"

# Layer 2: TCP connectivity
echo -n "2. TCP: "
timeout 5 bash -c "echo > /dev/tcp/${STORE}/443" 2>/dev/null && echo "OK" || echo "FAIL"

# Layer 3: TLS handshake
echo -n "3. TLS: "
echo | openssl s_client -connect "$STORE:443" -servername "$STORE" 2>/dev/null | grep -q "Verify return code: 0" && echo "OK" || echo "FAIL"

# Layer 4: HTTP response
echo -n "4. HTTP: "
HTTP=$(curl -sf -o /dev/null -w "%{http_code}" "https://$STORE/admin/api/$VERSION/shop.json" -H "X-Shopify-Access-Token: $TOKEN")
[ "$HTTP" = "200" ] && echo "OK ($HTTP)" || echo "FAIL ($HTTP)"

# Layer 5: GraphQL
echo -n "5. GraphQL: "
GQL=$(curl -sf "https://$STORE/admin/api/$VERSION/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' | jq -r '.data.shop.name')
[ -n "$GQL" ] && echo "OK ($GQL)" || echo "FAIL"

# Layer 6: Rate limit state
echo -n "6. Rate limit: "
curl -sf "https://$STORE/admin/api/$VERSION/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  | jq -r '.extensions.cost.throttleStatus | "\(.currentlyAvailable)/\(.maximumAvailable) available"'
```

### Step 6: Debug Intermittent Failures

```typescript
// Capture timing and response details for pattern analysis
interface DebugEntry {
  timestamp: string;
  operation: string;
  requestId: string;
  statusCode: number;
  durationMs: number;
  queryCost: number;
  availablePoints: number;
  error?: string;
}

const debugLog: DebugEntry[] = [];

async function debugShopifyCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = Date.now();
  try {
    const result = await fn();
    debugLog.push({
      timestamp: new Date().toISOString(),
      operation,
      requestId: "from-response-headers",
      statusCode: 200,
      durationMs: Date.now() - start,
      queryCost: (result as any).extensions?.cost?.actualQueryCost || 0,
      availablePoints: (result as any).extensions?.cost?.throttleStatus?.currentlyAvailable || 0,
    });
    return result;
  } catch (error: any) {
    debugLog.push({
      timestamp: new Date().toISOString(),
      operation,
      requestId: error.response?.headers?.["x-request-id"] || "unknown",
      statusCode: error.response?.code || 0,
      durationMs: Date.now() - start,
      queryCost: 0,
      availablePoints: 0,
      error: error.message,
    });
    throw error;
  }
}

// After running, analyze the debug log for patterns:
// - Do failures cluster at specific times?
// - Does availablePoints drop to 0 before failures?
// - Are specific operations consistently slow?
```

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

### Support Escalation with Evidence

```bash
# Collect everything for a support ticket
echo "=== Shopify Support Evidence ===" > evidence.txt
echo "Date: $(date -u)" >> evidence.txt
echo "Store: $SHOPIFY_STORE" >> evidence.txt
echo "API Version: 2024-10" >> evidence.txt
echo "" >> evidence.txt
echo "Error X-Request-Ids:" >> evidence.txt
echo "  - abc123def456" >> evidence.txt
echo "" >> evidence.txt
echo "Query that fails:" >> evidence.txt
echo '  { products(first: 50) { edges { node { id title } } } }' >> evidence.txt
echo "" >> evidence.txt
echo "Frequency: ~5% of requests between 2pm-4pm UTC" >> evidence.txt
```

## Resources

- [Shopify GraphQL Cost Debug](https://shopify.dev/docs/api/usage/rate-limits#query-cost)
- [Webhook Troubleshooting](https://shopify.dev/docs/apps/build/webhooks/troubleshoot)
- [Shopify Partner Support](https://help.shopify.com/en/partners)
- [Shopify Community Forums](https://community.shopify.dev)

## Next Steps

For load testing, see `shopify-load-scale`.
