Debug wrapper that captures timing, cost, and error data for pattern analysis of intermittent Shopify API failures.

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
