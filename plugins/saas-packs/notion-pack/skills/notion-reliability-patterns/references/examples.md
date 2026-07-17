# Notion Reliability Patterns — Examples

Wiring the reliability layers into operational surfaces: a health endpoint your infra can poll, and monitoring alert rules that page on degradation.

## System Health Dashboard

Expose `notionHealthCheck()` (see [implementation.md](implementation.md) Step 3) as an HTTP endpoint so load balancers and uptime monitors can poll circuit + cache state.

```typescript
// Expose as API endpoint: GET /api/health/notion
async function handleHealthCheck(req: Request): Promise<Response> {
  const health = await notionHealthCheck();
  const statusCode = health.status === 'healthy' ? 200 : health.status === 'degraded' ? 200 : 503;

  return new Response(JSON.stringify({
    service: 'notion',
    ...health,
    circuit: circuit.getState(),
    timestamp: new Date().toISOString(),
  }), { status: statusCode, headers: { 'Content-Type': 'application/json' } });
}
```

## Monitoring Alert Rules

Prometheus rules that fire when the circuit trips or when too much traffic is served from stale cache — both signals that Notion is degraded even if your app is still responding.

```yaml
# prometheus/alerts.yml
groups:
  - name: notion-reliability
    rules:
      - alert: NotionCircuitOpen
        expr: notion_circuit_state == 2  # 0=closed, 1=half-open, 2=open
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Notion API circuit breaker is open"

      - alert: NotionHighCacheRate
        expr: rate(notion_cache_hits[5m]) / rate(notion_total_requests[5m]) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Over 50% of Notion requests served from cache"
```
