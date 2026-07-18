# Notion Observability — Examples

Copy-paste queries and lightweight instrumentation snippets referenced from
`SKILL.md`.

## Quick Metrics Dashboard Query (PromQL)

```promql
# Request rate by operation
rate(notion_requests_total[5m])

# Error percentage
100 * rate(notion_errors_total[5m]) / rate(notion_requests_total[5m])

# P95 latency per operation
histogram_quantile(0.95, rate(notion_request_duration_seconds_bucket[5m]))

# Rate limit events in last hour
increase(notion_errors_total{code="rate_limited"}[1h])
```

## Inline Metrics Check (No Prometheus)

```typescript
// Quick console-based metrics for debugging
setInterval(() => {
  const m = notion.getMetrics();
  console.log(
    `[Notion] requests=${m.requestCount} errors=${m.errorCount} ` +
    `rate_limits=${m.rateLimitCount} avg_latency=${m.avgLatencyMs}ms ` +
    `p95_latency=${m.p95LatencyMs}ms`
  );
}, 60_000); // Log every minute
```
