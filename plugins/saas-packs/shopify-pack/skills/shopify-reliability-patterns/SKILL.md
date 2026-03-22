---
name: shopify-reliability-patterns
description: |
  Implement reliability patterns for Shopify apps including circuit breakers
  for API outages, webhook retry handling, and graceful degradation.
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

```typescript
import CircuitBreaker from "opossum";

// Create circuit breaker wrapping Shopify API calls
const shopifyCircuit = new CircuitBreaker(
  async (fn: () => Promise<any>) => fn(),
  {
    timeout: 10000,                 // 10s timeout per request
    errorThresholdPercentage: 50,   // Open at 50% error rate
    resetTimeout: 30000,            // Try half-open after 30s
    volumeThreshold: 5,             // Need 5 requests before tripping
    errorFilter: (error: any) => {
      // Don't count 422 validation errors as circuit failures
      // Only count 5xx and timeout errors
      const code = error.response?.code || error.statusCode;
      return code >= 500 || error.code === "ECONNRESET" || error.code === "ETIMEDOUT";
    },
  }
);

shopifyCircuit.on("open", () => {
  console.error("[CIRCUIT OPEN] Shopify API failing — serving cached data");
});
shopifyCircuit.on("halfOpen", () => {
  console.info("[CIRCUIT HALF-OPEN] Testing Shopify recovery...");
});
shopifyCircuit.on("close", () => {
  console.info("[CIRCUIT CLOSED] Shopify API recovered");
});

// Usage
async function resilientShopifyQuery<T>(
  shop: string,
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  return shopifyCircuit.fire(async () => {
    const client = getGraphqlClient(shop);
    const response = await client.request(query, { variables });

    // Check for THROTTLED in GraphQL response
    if (response.errors?.some((e: any) => e.extensions?.code === "THROTTLED")) {
      throw new Error("THROTTLED"); // Triggers circuit breaker
    }

    return response.data as T;
  });
}
```

### Step 2: Webhook Idempotency

Shopify retries webhooks up to 19 times over 48 hours if your endpoint doesn't return 200. Your handler **must** be idempotent.

```typescript
import { Redis } from "ioredis";
const redis = new Redis(process.env.REDIS_URL!);

async function processWebhookIdempotently(
  webhookId: string, // X-Shopify-Webhook-Id header
  topic: string,
  handler: () => Promise<void>
): Promise<{ processed: boolean; duplicate: boolean }> {
  const key = `shopify:webhook:${webhookId}`;

  // Check if already processed
  const exists = await redis.exists(key);
  if (exists) {
    console.log(`Duplicate webhook ${webhookId} for ${topic} — skipping`);
    return { processed: false, duplicate: true };
  }

  // Mark as processing (with TTL to auto-expire)
  await redis.set(key, "processing", "EX", 7 * 86400, "NX"); // 7 day TTL

  try {
    await handler();
    await redis.set(key, "completed", "EX", 7 * 86400);
    return { processed: true, duplicate: false };
  } catch (error) {
    // Remove the key so Shopify's retry can re-process
    await redis.del(key);
    throw error;
  }
}

// Usage in webhook handler
app.post("/webhooks", rawBodyParser, async (req, res) => {
  const webhookId = req.headers["x-shopify-webhook-id"] as string;
  const topic = req.headers["x-shopify-topic"] as string;

  // ALWAYS respond 200 within 5 seconds
  res.status(200).send("OK");

  // Process asynchronously with idempotency
  await processWebhookIdempotently(webhookId, topic, async () => {
    const payload = JSON.parse(req.body.toString());
    await handleWebhookEvent(topic, payload);
  });
});
```

### Step 3: Graceful Degradation with Cached Fallback

```typescript
async function withFallback<T>(
  primary: () => Promise<T>,
  fallback: () => Promise<T>,
  cacheKey?: string
): Promise<{ data: T; source: "live" | "cached" | "fallback" }> {
  try {
    const data = await primary();
    // Update cache for future fallback
    if (cacheKey) {
      await redis.set(`fallback:${cacheKey}`, JSON.stringify(data), "EX", 3600);
    }
    return { data, source: "live" };
  } catch (error) {
    console.warn("Shopify API failed, trying cached data:", (error as Error).message);

    // Try cached data first
    if (cacheKey) {
      const cached = await redis.get(`fallback:${cacheKey}`);
      if (cached) {
        return { data: JSON.parse(cached), source: "cached" };
      }
    }

    // Fall back to alternative data source
    try {
      const data = await fallback();
      return { data, source: "fallback" };
    } catch {
      throw error; // Re-throw original error if all fallbacks fail
    }
  }
}

// Usage
const { data: products, source } = await withFallback(
  () => shopifyQuery(shop, PRODUCTS_QUERY),
  () => db.cachedProducts.findMany({ where: { shop } }),
  `products:${shop}`
);

if (source !== "live") {
  console.warn(`Serving ${source} product data for ${shop}`);
}
```

### Step 4: Webhook Processing Queue

Don't process webhooks inline — queue them for resilience:

```typescript
import { Queue, Worker } from "bullmq";

const webhookQueue = new Queue("shopify-webhooks", {
  connection: { host: "localhost", port: 6379 },
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: "exponential", delay: 5000 },
    removeOnComplete: 1000,
    removeOnFail: 5000,
  },
});

// Enqueue webhook for processing
app.post("/webhooks", rawBodyParser, (req, res) => {
  // Verify HMAC first
  if (!verifyHmac(req.body, req.headers["x-shopify-hmac-sha256"]!)) {
    return res.status(401).send();
  }

  // Respond immediately
  res.status(200).send("OK");

  // Queue for async processing
  webhookQueue.add(req.headers["x-shopify-topic"] as string, {
    topic: req.headers["x-shopify-topic"],
    shop: req.headers["x-shopify-shop-domain"],
    webhookId: req.headers["x-shopify-webhook-id"],
    payload: req.body.toString(),
  });
});

// Worker processes queued webhooks
const worker = new Worker("shopify-webhooks", async (job) => {
  const { topic, shop, webhookId, payload } = job.data;

  await processWebhookIdempotently(webhookId, topic, async () => {
    await handleWebhookEvent(topic, JSON.parse(payload));
  });
}, {
  connection: { host: "localhost", port: 6379 },
  concurrency: 10,
});
```

### Step 5: Rate Limit-Aware Retry

```typescript
async function shopifyRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const isRetryable =
        error.response?.code === 429 ||
        error.response?.code >= 500 ||
        error.body?.errors?.[0]?.extensions?.code === "THROTTLED";

      if (!isRetryable || attempt === maxRetries) throw error;

      // For REST 429: use Retry-After header
      const retryAfter = error.response?.headers?.["retry-after"];
      // For GraphQL THROTTLED: calculate from available points
      const throttle = error.body?.extensions?.cost?.throttleStatus;
      const waitForPoints = throttle
        ? ((100 - throttle.currentlyAvailable) / throttle.restoreRate) * 1000
        : 0;

      const delay = retryAfter
        ? parseFloat(retryAfter) * 1000
        : Math.max(waitForPoints, 1000 * Math.pow(2, attempt));

      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${(delay / 1000).toFixed(1)}s`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

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

## Next Steps

For policy enforcement, see `shopify-policy-guardrails`.
