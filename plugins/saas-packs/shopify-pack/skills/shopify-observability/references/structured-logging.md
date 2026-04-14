# Structured Logging

Pino-based structured logger with automatic PII redaction and Shopify-specific context fields.

```typescript
import pino from "pino";

const logger = pino({
  name: "shopify-app",
  level: process.env.LOG_LEVEL || "info",
  serializers: {
    // Redact sensitive fields automatically
    shopifyRequest: (req: any) => ({
      shop: req.shop,
      operation: req.operation,
      queryCost: req.cost?.actualQueryCost,
      available: req.cost?.throttleStatus?.currentlyAvailable,
      // Never log: accessToken, apiSecret, customer PII
    }),
  },
});

// Log every Shopify API call with structured context
function logShopifyCall(operation: string, shop: string, cost: any, durationMs: number) {
  logger.info({
    msg: "shopify_api_call",
    operation,
    shop,
    queryCost: cost?.actualQueryCost,
    requestedCost: cost?.requestedQueryCost,
    availablePoints: cost?.throttleStatus?.currentlyAvailable,
    durationMs,
  });
}
```
