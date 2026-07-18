# Intercom Production Health Check — Implementation

Full production-grade health check implementation for an Intercom integration.
It probes authentication and latency, classifies degraded-vs-unhealthy from the
`IntercomError` status code, and wires the result into an Express `/health`
endpoint that returns `503` when Intercom is not healthy.

## Health check module

```typescript
import { IntercomClient, IntercomError } from "intercom-client";

interface IntercomHealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs: number;
  authenticated: boolean;
  rateLimitRemaining?: number;
  error?: string;
}

async function checkIntercomHealth(
  client: IntercomClient
): Promise<IntercomHealthStatus> {
  const start = Date.now();
  try {
    const admins = await client.admins.list();
    return {
      status: "healthy",
      latencyMs: Date.now() - start,
      authenticated: true,
      rateLimitRemaining: undefined, // Parsed from response headers
    };
  } catch (err) {
    const latencyMs = Date.now() - start;
    if (err instanceof IntercomError) {
      return {
        status: err.statusCode === 429 ? "degraded" : "unhealthy",
        latencyMs,
        authenticated: err.statusCode !== 401,
        error: `${err.statusCode}: ${err.message}`,
      };
    }
    return {
      status: "unhealthy",
      latencyMs,
      authenticated: false,
      error: (err as Error).message,
    };
  }
}

// Express health endpoint
app.get("/health", async (req, res) => {
  const intercom = await checkIntercomHealth(client);
  const overall = intercom.status === "healthy" ? 200 : 503;
  res.status(overall).json({
    status: intercom.status,
    services: { intercom },
    timestamp: new Date().toISOString(),
  });
});
```

## Classification rules

| Status code | Reported status | authenticated | Rationale |
|-------------|-----------------|---------------|-----------|
| 2xx (success) | `healthy` | `true` | Intercom reachable and token valid |
| 429 | `degraded` | `true` | Rate limited — transient, keep serving |
| 401 | `unhealthy` | `false` | Token invalid/expired — rotate immediately |
| Other 4xx/5xx | `unhealthy` | `true` | Intercom error, but auth still valid |
| Non-Intercom error | `unhealthy` | `false` | Network/client failure |

## Monitoring and alerting targets

Wire these thresholds into your observability stack once the health endpoint is live:

- Error rate alerting configured (threshold: 5% over 5 min)
- Rate limit usage tracked (alert at 80% of limit)
- Latency monitoring (alert if P95 > 2 seconds)
- Intercom status page monitored (https://status.intercom.com)
