# BFCM / Flash Sale Preparation

Pre-BFCM checklist and scaling patterns for Shopify apps handling high-traffic burst events.

## Application-Level Preparation

```typescript
// Pre-BFCM checklist for Shopify apps

// 1. Pre-fetch and cache product data before the sale starts
async function prewarmCache(productIds: string[]): Promise<void> {
  console.log(`Pre-warming cache for ${productIds.length} products`);
  for (const id of productIds) {
    await cachedQuery(`product:${id}`, () =>
      shopifyQuery(shop, PRODUCT_QUERY, { id })
    );
    await new Promise((r) => setTimeout(r, 100)); // Pace for rate limits
  }
}

// 2. Use Storefront API for customer-facing queries (separate rate limits)
// Admin API rate limits are shared across all apps
// Storefront API has its own higher limits

// 3. Use bulk operations to sync inventory before the event
// Don't rely on real-time inventory queries during peak traffic

// 4. Queue webhook processing — don't process inline during peak
async function handleOrderWebhook(payload: any): Promise<void> {
  // Queue for later processing instead of immediate API calls
  await queue.add("process-order", payload, {
    attempts: 5,
    backoff: { type: "exponential", delay: 5000 },
  });
}
```

## Infrastructure Scaling (Kubernetes HPA)

```yaml
# BFCM webhook volume estimates:
# 100 orders/hour → 100 orders/create webhooks/hour
# 1,000 orders/hour → 1,000 webhooks/hour (Plus stores during BFCM)
# Each webhook must respond 200 within 5 seconds

# Kubernetes HPA for webhook processing
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shopify-webhook-processor
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shopify-webhook-processor
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Pods
      pods:
        metric:
          name: webhook_queue_depth
        target:
          type: AverageValue
          averageValue: "50"
```
