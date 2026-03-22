---
name: figma-observability
description: |
  Set up monitoring, metrics, and alerting for Figma API integrations.
  Use when implementing observability for Figma operations, tracking API health,
  or configuring alerts for rate limits and errors.
  Trigger with phrases like "figma monitoring", "figma metrics",
  "figma observability", "figma alerts", "figma dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Observability

## Overview
Monitor Figma REST API health with custom metrics, structured logging, and alerts. Track request latency, error rates, rate limit headroom, and cache hit rates.

## Prerequisites
- Prometheus or compatible metrics backend (or use OpenTelemetry)
- Structured logging (pino, winston)
- Alerting system (PagerDuty, Slack, OpsGenie)

## Instructions

### Step 1: Instrumented Figma Client
```typescript
// Wrap every Figma API call with metrics and logging
class InstrumentedFigmaClient {
  private metrics = {
    requests: 0,
    errors: 0,
    rateLimits: 0,
    totalLatencyMs: 0,
  };

  async request<T>(path: string, token: string): Promise<T> {
    const start = performance.now();
    const endpoint = path.replace(/[a-zA-Z0-9]{15,}/, ':key'); // normalize

    try {
      const res = await fetch(`https://api.figma.com${path}`, {
        headers: { 'X-Figma-Token': token },
      });

      const latencyMs = performance.now() - start;
      this.metrics.requests++;
      this.metrics.totalLatencyMs += latencyMs;

      // Log every request with structured data
      console.log(JSON.stringify({
        service: 'figma',
        endpoint,
        status: res.status,
        latencyMs: Math.round(latencyMs),
        rateLimit: {
          remaining: res.headers.get('X-RateLimit-Remaining'),
          type: res.headers.get('X-Figma-Rate-Limit-Type'),
        },
      }));

      if (res.status === 429) {
        this.metrics.rateLimits++;
        const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
        throw new FigmaRateLimitError(retryAfter);
      }

      if (!res.ok) {
        this.metrics.errors++;
        throw new FigmaApiError(res.status, await res.text());
      }

      return res.json();
    } catch (error) {
      if (!(error instanceof FigmaApiError)) {
        this.metrics.errors++;
        console.error(JSON.stringify({
          service: 'figma',
          endpoint,
          error: error instanceof Error ? error.message : 'Unknown',
          latencyMs: Math.round(performance.now() - start),
        }));
      }
      throw error;
    }
  }

  getMetrics() {
    return {
      ...this.metrics,
      avgLatencyMs: this.metrics.requests > 0
        ? Math.round(this.metrics.totalLatencyMs / this.metrics.requests)
        : 0,
      errorRate: this.metrics.requests > 0
        ? (this.metrics.errors / this.metrics.requests * 100).toFixed(1) + '%'
        : '0%',
    };
  }
}
```

### Step 2: Prometheus Metrics
```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const figmaRequests = new Counter({
  name: 'figma_api_requests_total',
  help: 'Total Figma API requests',
  labelNames: ['endpoint', 'status'],
  registers: [registry],
});

const figmaLatency = new Histogram({
  name: 'figma_api_request_duration_seconds',
  help: 'Figma API request duration in seconds',
  labelNames: ['endpoint'],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry],
});

const figmaRateLimitRemaining = new Gauge({
  name: 'figma_rate_limit_remaining',
  help: 'Remaining Figma API rate limit',
  registers: [registry],
});

const figmaCacheHits = new Counter({
  name: 'figma_cache_hits_total',
  help: 'Figma cache hits vs misses',
  labelNames: ['result'], // 'hit' or 'miss'
  registers: [registry],
});

// Expose /metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

### Step 3: Alert Rules
```yaml
# prometheus-alerts.yml
groups:
  - name: figma
    rules:
      - alert: FigmaHighErrorRate
        expr: |
          rate(figma_api_requests_total{status=~"4..|5.."}[5m])
          / rate(figma_api_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Figma API error rate > 5% for 5 minutes"

      - alert: FigmaRateLimited
        expr: figma_rate_limit_remaining < 5
        for: 1m
        labels: { severity: warning }
        annotations:
          summary: "Figma rate limit nearly exhausted"

      - alert: FigmaHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(figma_api_request_duration_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Figma API P95 latency > 5 seconds"

      - alert: FigmaAuthFailure
        expr: figma_api_requests_total{status="403"} > 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Figma auth failures detected (possible expired PAT)"
```

### Step 4: Health Check with Details
```typescript
async function figmaHealthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, any>;
}> {
  const start = Date.now();

  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
      signal: AbortSignal.timeout(5000),
    });

    const latencyMs = Date.now() - start;
    const remaining = res.headers.get('X-RateLimit-Remaining');

    return {
      status: res.ok ? (latencyMs > 3000 ? 'degraded' : 'healthy') : 'degraded',
      details: {
        authenticated: res.ok,
        latencyMs,
        rateLimitRemaining: remaining ? parseInt(remaining) : null,
        planTier: res.headers.get('X-Figma-Plan-Tier'),
      },
    };
  } catch {
    return {
      status: 'unhealthy',
      details: { authenticated: false, latencyMs: Date.now() - start },
    };
  }
}
```

## Output
- Instrumented client logging every Figma API call
- Prometheus metrics for requests, latency, rate limits, cache
- Alert rules for error rate, rate limits, latency, auth failures
- Health check endpoint with Figma connectivity details

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High cardinality | Too many label values | Normalize endpoint paths |
| Alert storms | Threshold too low | Tune `for` duration and thresholds |
| Missing rate limit headers | Not all endpoints return them | Handle null values gracefully |
| Metrics not scraping | Wrong port or path | Verify Prometheus scrape config |

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry JS SDK](https://opentelemetry.io/docs/languages/js/)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)

## Next Steps
For incident response, see `figma-incident-runbook`.
