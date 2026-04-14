---
name: shopify-reliability-patterns
description: |
  Implement reliability patterns for Shopify apps including circuit breakers
  for API outages, webhook retry handling, and graceful degradation.
  Use when building fault-tolerant Shopify integrations, handling webhook retry storms,
  or adding resilience to API calls.
  Trigger with phrases like "shopify reliability", "shopify circuit breaker",
  "shopify resilience", "shopify fallback", "shopify retry webhook".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Reliability Patterns

## Overview

Build fault-tolerant Shopify integrations that handle API outages, webhook retry storms, and rate limit exhaustion gracefully.

## Prerequisites

- Understanding of circuit breaker pattern
- Queue infrastructure (BullMQ, SQS, etc.) for async processing
- Cache layer for fallback data

## Instructions

### Step 1: Circuit Breaker for Shopify API

Wrap all Shopify API calls in a circuit breaker (using opossum) that opens at 50% error rate, only counting 5xx and timeout errors. When open, serve cached data. The breaker auto-tests recovery after 30 seconds in half-open state.

See [Circuit Breaker](references/circuit-breaker.md) for the complete implementation.

### Step 2: Webhook Idempotency

Shopify retries webhooks up to 19 times over 48 hours if your endpoint doesn't return 200. Your handler **must** be idempotent. Use Redis to track `X-Shopify-Webhook-Id` with a 7-day TTL. Always respond 200 within 5 seconds, then process asynchronously.

See [Webhook Idempotency](references/webhook-idempotency.md) for the complete implementation.

### Step 3: Graceful Degradation with Cached Fallback

Implement a three-tier fallback: try the live API first (caching the result), fall back to cached data, then fall back to an alternative data source (e.g., local DB). Track the data source so you can log degraded responses.

See [Cached Fallback](references/cached-fallback.md) for the complete implementation.

### Step 4: Webhook Processing Queue

Don't process webhooks inline — queue them with BullMQ for resilience. Verify HMAC first, respond 200 immediately, then enqueue with topic/shop/payload metadata. The worker processes jobs with exponential backoff (5 retries) and idempotency checks.

See [Webhook Processing Queue](references/webhook-processing-queue.md) for the complete implementation.

### Step 5: Rate Limit-Aware Retry

Retry logic that respects Shopify's `Retry-After` header (REST 429) and GraphQL throttle status restore rate. Calculates optimal wait time from available points rather than blindly backing off.

See [Rate Limit-Aware Retry](references/rate-limit-retry.md) for the complete implementation.

## Output

- Circuit breaker preventing cascade failures during Shopify outages
- Idempotent webhook processing preventing duplicate operations
- Graceful degradation with cached fallback data
- Queue-based webhook processing for resilience
- Rate limit-aware retry logic

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Shopify extended outage | Serve cached data, monitor status page |
| Duplicate orders processed | Missing idempotency | Use `X-Shopify-Webhook-Id` for dedup |
| Queue growing unbounded | Worker down | Monitor queue depth, alert on backlog |
| Stale cache served for hours | Circuit never recovers | Set max cache staleness, force refresh |

## Examples

### Health Check with Circuit State

```typescript
app.get("/health", async (req, res) => {
  res.json({
    status: shopifyCircuit.opened ? "degraded" : "healthy",
    shopify: {
      circuit: shopifyCircuit.opened ? "open" : "closed",
      stats: shopifyCircuit.stats,
    },
    webhookQueue: {
      waiting: await webhookQueue.getWaitingCount(),
      active: await webhookQueue.getActiveCount(),
      failed: await webhookQueue.getFailedCount(),
    },
  });
});
```

## Resources

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum Circuit Breaker](https://nodeshift.dev/opossum/)
- [BullMQ Documentation](https://docs.bullmq.io/)
- [Shopify Webhook Retry Policy](https://shopify.dev/docs/apps/build/webhooks)
