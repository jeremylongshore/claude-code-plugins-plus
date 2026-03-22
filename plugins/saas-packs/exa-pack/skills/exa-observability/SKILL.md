---
name: exa-observability
description: |
  Set up monitoring, metrics, and alerting for Exa search integrations.
  Use when implementing monitoring for Exa operations, building dashboards,
  or configuring alerting for search quality and latency.
  Trigger with phrases like "exa monitoring", "exa metrics",
  "exa observability", "monitor exa", "exa alerts", "exa dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, monitoring, observability]

---
# Exa Observability

## Overview
Monitor Exa search API performance, result quality, and cost efficiency. Key metrics: search latency by type (neural ~500-2000ms, keyword ~200-500ms), result count per query, cache hit rates, error rates by status code, and daily search volume for budget tracking.

## Prerequisites
- Exa API integration in production
- Metrics backend (Prometheus, Datadog, or OpenTelemetry)
- Alerting system (PagerDuty, Slack, or equivalent)

## Instructions

### Step 1: Instrument the Exa Client
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

// Generic metrics emitter (replace with your metrics library)
function emitMetric(name: string, value: number, tags: Record<string, string>) {
  // Prometheus: histogram/counter.observe(value, tags)
  // Datadog: dogstatsd.histogram(name, value, tags)
  // OpenTelemetry: meter.createHistogram(name).record(value, tags)
  console.log(`[metric] ${name}=${value}`, tags);
}

async function trackedSearch(query: string, options: any = {}) {
  const start = performance.now();
  const type = options.type || "auto";
  const hasContents = options.text || options.highlights || options.summary;

  try {
    const method = hasContents ? "searchAndContents" : "search";
    const results = hasContents
      ? await exa.searchAndContents(query, options)
      : await exa.search(query, options);

    const duration = performance.now() - start;

    emitMetric("exa.search.duration_ms", duration, { type, method });
    emitMetric("exa.search.result_count", results.results.length, { type });
    emitMetric("exa.search.success", 1, { type });

    return results;
  } catch (err: any) {
    const duration = performance.now() - start;
    const status = String(err.status || "unknown");

    emitMetric("exa.search.duration_ms", duration, { type, status });
    emitMetric("exa.search.error", 1, { type, status });

    throw err;
  }
}
```

### Step 2: Track Result Quality
```typescript
// Measure whether search results are actually used downstream
function trackResultUsage(
  searchId: string,
  resultIndex: number,
  action: "clicked" | "used_in_context" | "discarded"
) {
  emitMetric("exa.result.usage", 1, {
    action,
    position: String(resultIndex),
  });
  // Results at position 0-2 should have high usage
  // If top results are discarded, query needs tuning
}

// Track content extraction value
function trackContentValue(result: any) {
  if (result.text) {
    emitMetric("exa.content.text_length", result.text.length, {});
  }
  if (result.highlights) {
    emitMetric("exa.content.highlight_count", result.highlights.length, {});
  }
}
```

### Step 3: Cache Monitoring
```typescript
class MonitoredCache {
  private hits = 0;
  private misses = 0;
  private cache: Map<string, { data: any; expiry: number }> = new Map();

  async search(exa: Exa, query: string, opts: any) {
    const key = `${query}:${opts.type}:${opts.numResults}`;
    const cached = this.cache.get(key);

    if (cached && cached.expiry > Date.now()) {
      this.hits++;
      emitMetric("exa.cache.hit", 1, {});
      return cached.data;
    }

    this.misses++;
    emitMetric("exa.cache.miss", 1, {});

    const results = await exa.searchAndContents(query, opts);
    this.cache.set(key, { data: results, expiry: Date.now() + 3600 * 1000 });
    return results;
  }

  getStats() {
    const total = this.hits + this.misses;
    return {
      hits: this.hits,
      misses: this.misses,
      hitRate: total > 0 ? `${((this.hits / total) * 100).toFixed(1)}%` : "N/A",
    };
  }
}
```

### Step 4: Prometheus Alert Rules
```yaml
groups:
  - name: exa_alerts
    rules:
      - alert: ExaHighLatency
        expr: histogram_quantile(0.95, rate(exa_search_duration_ms_bucket[5m])) > 3000
        for: 5m
        annotations:
          summary: "Exa search P95 latency exceeds 3 seconds"

      - alert: ExaHighErrorRate
        expr: rate(exa_search_error[5m]) / rate(exa_search_success[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Exa API error rate exceeds 5%"

      - alert: ExaEmptyResults
        expr: rate(exa_search_result_count{result_count="0"}[15m]) > 0.2
        for: 10m
        annotations:
          summary: "Over 20% of Exa searches returning empty results"

      - alert: ExaCacheHitRateLow
        expr: rate(exa_cache_hit[5m]) / (rate(exa_cache_hit[5m]) + rate(exa_cache_miss[5m])) < 0.3
        for: 15m
        annotations:
          summary: "Exa cache hit rate below 30% — check query patterns"
```

### Step 5: Health Check Endpoint
```typescript
app.get("/health/exa", async (_req, res) => {
  const start = performance.now();
  try {
    const result = await exa.search("health check", { numResults: 1 });
    const latencyMs = Math.round(performance.now() - start);
    res.json({
      status: "healthy",
      latencyMs,
      resultCount: result.results.length,
    });
  } catch (err: any) {
    res.status(503).json({
      status: "unhealthy",
      error: err.message,
      latencyMs: Math.round(performance.now() - start),
    });
  }
});
```

## Dashboard Panels

| Panel | Metric | Purpose |
|-------|--------|---------|
| Search Volume | `rate(exa.search.success)` | Traffic trends |
| Latency P50/P95 | `histogram_quantile(exa.search.duration_ms)` | Performance SLO |
| Error Rate | `exa.search.error / exa.search.success` | Reliability |
| Result Quality | `exa.result.usage{action="discarded"}` | Query tuning signal |
| Cache Hit Rate | `exa.cache.hit / (hit + miss)` | Cost efficiency |
| Daily Cost | `sum(exa.search.success)` | Budget tracking |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Rate limit exceeded | Implement backoff + request queue |
| Zero results returned | Query too narrow | Broaden query, remove domain filter |
| Latency spike to 5s+ | Deep/neural on complex query | Switch to `fast` or `auto` type |
| Budget exhausted | Uncapped search volume | Add application-level budget tracking |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Rate Limits](https://docs.exa.ai/reference/rate-limits)
- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)

## Next Steps
For incident response, see `exa-incident-runbook`. For cost optimization, see `exa-cost-tuning`.
