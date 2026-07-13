# Langfuse Incident Runbook - Implementation Details

## Quick Diagnosis Script

```bash
#!/bin/bash
echo "=== Langfuse Quick Diagnosis ==="

# 1. Check Langfuse status
echo "1. Langfuse Status:"
curl -s https://status.langfuse.com/api/v2/status.json | jq '.status.description'

# 2. Check API connectivity
echo "2. API Connectivity:"
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  https://cloud.langfuse.com/api/public/health

# 3. Check authentication
echo "3. Auth Test:"
AUTH=$(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "Authorization: Basic $AUTH" \
  "https://cloud.langfuse.com/api/public/traces?limit=1"
```

## Section A: Traces Not Appearing

```typescript
// Verify SDK is enabled
console.log("Langfuse enabled:", process.env.LANGFUSE_ENABLED !== "false");

// Check for pending events
const langfuse = getLangfuse();
console.log("Pending events:", langfuse.pendingItems?.length || "unknown");

// Force flush and check for errors
try {
  await langfuse.flushAsync();
  console.log("Flush successful");
} catch (error) {
  console.error("Flush failed:", error);
}

// Resolution: Ensure shutdown handlers
process.on("beforeExit", async () => { await langfuse.shutdownAsync(); });

// Resolution: Reduce batch size temporarily
const langfuse = new Langfuse({ flushAt: 1, flushInterval: 1000 });

// Resolution: Enable debug logging
// DEBUG=langfuse* npm start
```

## Section B: Authentication Errors

```bash
# Verify environment variables
echo "Public key starts with: ${LANGFUSE_PUBLIC_KEY:0:10}"
echo "Secret key is set: ${LANGFUSE_SECRET_KEY:+yes}"

# Test credentials directly
curl -v -X GET \
  -H "Authorization: Basic $(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)" \
  "${LANGFUSE_HOST:-https://cloud.langfuse.com}/api/public/traces?limit=1"
```

## Section C: High Latency / Timeouts

```typescript
// Check flush timing
const start = Date.now();
await langfuse.flushAsync();
console.log(`Flush took ${Date.now() - start}ms`);

// Circuit breaker for resilience
class CircuitBreaker {
  private failures = 0;
  private lastFailure?: Date;
  private readonly threshold = 5;
  private readonly resetMs = 60000;

  async execute<T>(operation: () => Promise<T>): Promise<T | null> {
    if (this.isOpen()) {
      console.warn("Circuit breaker open, skipping Langfuse");
      return null;
    }
    try {
      const result = await operation();
      this.reset();
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }

  private isOpen(): boolean {
    if (this.failures < this.threshold) return false;
    return Date.now() - (this.lastFailure?.getTime() || 0) < this.resetMs;
  }
}
```

## Section D: Missing/Partial Data

```typescript
// Ensure all spans are ended
const span = trace.span({ name: "operation" });
try {
  return await doWork();
} finally {
  span.end(); // Always end in finally
}

// Don't swallow flush errors
try {
  await langfuse.flushAsync();
} catch (error) {
  console.error("Langfuse flush error:", error);
}
```

## Section E: Langfuse Service Outage

```typescript
// Graceful degradation
const langfuse = new Langfuse({ enabled: false });

// Queue events locally during outage
const pendingEvents: any[] = [];
function queueEvent(event: any) {
  pendingEvents.push({ ...event, timestamp: new Date().toISOString() });
  if (pendingEvents.length > 1000) {
    fs.writeFileSync(`langfuse-backup-${Date.now()}.json`, JSON.stringify(pendingEvents));
    pendingEvents.length = 0;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
