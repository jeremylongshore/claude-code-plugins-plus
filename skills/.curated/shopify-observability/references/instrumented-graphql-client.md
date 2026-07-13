# Instrumented GraphQL Client

Wraps the Shopify GraphQL client to automatically record query cost, rate limit headroom, and error classification.

```typescript
async function instrumentedGraphqlQuery<T>(
  shop: string,
  operation: string,
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  const timer = apiDuration.startTimer({ operation, api_type: "graphql" });

  try {
    const client = getGraphqlClient(shop);
    const response = await client.request(query, { variables });

    // Record cost metrics from Shopify's response
    const cost = response.extensions?.cost;
    if (cost) {
      queryCostHistogram.observe(
        { operation, shop },
        cost.actualQueryCost || cost.requestedQueryCost
      );
      rateLimitGauge.set(
        { shop, api_type: "graphql" },
        cost.throttleStatus.currentlyAvailable
      );
    }

    timer({ status: "success" });
    return response.data as T;
  } catch (error: any) {
    const statusCode = error.response?.code || "unknown";
    const errorType =
      error.body?.errors?.[0]?.extensions?.code === "THROTTLED"
        ? "throttled"
        : statusCode === 401
        ? "auth"
        : "api_error";

    apiErrors.inc({ error_type: errorType, status_code: String(statusCode) });
    timer({ status: "error" });
    throw error;
  }
}
```
