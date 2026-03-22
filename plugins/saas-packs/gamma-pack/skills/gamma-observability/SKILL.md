---
name: gamma-observability
description: |
  Implement comprehensive observability for Gamma integrations.
  Use when setting up monitoring, logging, tracing,
  or building dashboards for Gamma API usage.
  Trigger with phrases like "gamma monitoring", "gamma logging",
  "gamma metrics", "gamma observability", "gamma dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, api, monitoring, observability]

---
# Gamma Observability

## Overview

Implement monitoring, logging, and health checks for Gamma API integrations. Since Gamma does not expose rate limit headers or internal metrics, observability is built around your API call patterns, latency, error rates, credit consumption, and generation success rates.

## Prerequisites

- Working Gamma integration (see `gamma-sdk-patterns`)
- Monitoring stack (Prometheus/Grafana, Datadog, or CloudWatch)
- Logging infrastructure

## Instructions

### Step 1: Instrumented Client

```typescript
// src/observability/gamma-metrics.ts
interface GammaMetrics {
  requests: number;
  errors: number;
  generations: number;
  completions: number;
  failures: number;
  totalCredits: number;
  totalLatencyMs: number;
  errorsByStatus: Record<number, number>;
}

const metrics: GammaMetrics = {
  requests: 0, errors: 0,
  generations: 0, completions: 0, failures: 0,
  totalCredits: 0, totalLatencyMs: 0,
  errorsByStatus: {},
};

export function createInstrumentedClient(apiKey: string) {
  const base = "https://public-api.gamma.app/v1.0";
  const headers = { "X-API-KEY": apiKey, "Content-Type": "application/json" };

  async function instrumentedRequest(method: string, path: string, body?: unknown) {
    metrics.requests++;
    const start = Date.now();

    try {
      const res = await fetch(`${base}${path}`, {
        method, headers,
        body: body ? JSON.stringify(body) : undefined,
      });
      metrics.totalLatencyMs += Date.now() - start;

      if (!res.ok) {
        metrics.errors++;
        metrics.errorsByStatus[res.status] = (metrics.errorsByStatus[res.status] || 0) + 1;
        throw new Error(`Gamma ${res.status}: ${await res.text()}`);
      }
      return res.json();
    } catch (err) {
      if (!metrics.errorsByStatus[0]) metrics.errorsByStatus[0] = 0;
      metrics.totalLatencyMs += Date.now() - start;
      throw err;
    }
  }

  return {
    generate: async (body: any) => {
      metrics.generations++;
      return instrumentedRequest("POST", "/generations", body);
    },
    poll: (id: string) => instrumentedRequest("GET", `/generations/${id}`),
    listThemes: () => instrumentedRequest("GET", "/themes"),
    listFolders: () => instrumentedRequest("GET", "/folders"),

    // Record completion metrics
    recordCompletion: (creditsUsed: number) => {
      metrics.completions++;
      metrics.totalCredits += creditsUsed;
    },
    recordFailure: () => { metrics.failures++; },
  };
}

export function getMetrics() {
  return {
    ...metrics,
    avgLatencyMs: metrics.requests > 0
      ? Math.round(metrics.totalLatencyMs / metrics.requests) : 0,
    errorRate: metrics.requests > 0
      ? (metrics.errors / metrics.requests * 100).toFixed(2) + "%" : "0%",
    completionRate: metrics.generations > 0
      ? (metrics.completions / metrics.generations * 100).toFixed(1) + "%" : "N/A",
    avgCreditsPerGeneration: metrics.completions > 0
      ? Math.round(metrics.totalCredits / metrics.completions) : 0,
  };
}
```

### Step 2: Structured Logging

```typescript
// src/observability/logger.ts
function logGammaEvent(event: string, data: Record<string, any>) {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    service: "gamma",
    event,
    ...data,
    // Never log: apiKey, raw content (may contain PII)
  }));
}

// Usage
logGammaEvent("generation.started", {
  generationId: "gen_abc123",
  outputFormat: "presentation",
  contentLength: 500,
});

logGammaEvent("generation.completed", {
  generationId: "gen_abc123",
  creditsUsed: 42,
  latencyMs: 15000,
});

logGammaEvent("generation.failed", {
  generationId: "gen_abc123",
  error: "Generation failed after 180s",
});
```

### Step 3: Health Check Endpoint

```typescript
// src/api/health.ts
async function checkGammaHealth() {
  const start = Date.now();
  try {
    const res = await fetch("https://public-api.gamma.app/v1.0/themes", {
      headers: { "X-API-KEY": process.env.GAMMA_API_KEY! },
    });
    const latencyMs = Date.now() - start;

    if (!res.ok) {
      return { status: "unhealthy", latencyMs, error: `HTTP ${res.status}` };
    }
    if (latencyMs > 5000) {
      return { status: "degraded", latencyMs, message: "High latency" };
    }
    return { status: "healthy", latencyMs };
  } catch (err: any) {
    return { status: "unhealthy", latencyMs: Date.now() - start, error: err.message };
  }
}

app.get("/health/gamma", async (req, res) => {
  const health = await checkGammaHealth();
  res.status(health.status === "unhealthy" ? 503 : 200).json(health);
});
```

### Step 4: Prometheus Metrics Endpoint

```typescript
// src/api/metrics.ts
app.get("/metrics/gamma", (req, res) => {
  const m = getMetrics();
  res.type("text/plain").send(`
# HELP gamma_requests_total Total API requests
# TYPE gamma_requests_total counter
gamma_requests_total ${m.requests}

# HELP gamma_errors_total Total API errors
# TYPE gamma_errors_total counter
gamma_errors_total ${m.errors}

# HELP gamma_generations_total Total generations started
# TYPE gamma_generations_total counter
gamma_generations_total ${m.generations}

# HELP gamma_completions_total Successful generations
# TYPE gamma_completions_total counter
gamma_completions_total ${m.completions}

# HELP gamma_credits_total Total credits consumed
# TYPE gamma_credits_total counter
gamma_credits_total ${m.totalCredits}

# HELP gamma_avg_latency_ms Average request latency
# TYPE gamma_avg_latency_ms gauge
gamma_avg_latency_ms ${m.avgLatencyMs}
  `.trim());
});
```

### Step 5: Alerting Rules

```yaml
# alerting-rules.yml (Prometheus)
groups:
  - name: gamma
    rules:
      - alert: GammaHighErrorRate
        expr: rate(gamma_errors_total[5m]) / rate(gamma_requests_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Gamma error rate above 10%"

      - alert: GammaHealthUnhealthy
        expr: up{job="gamma-health"} == 0
        for: 2m
        annotations:
          summary: "Gamma health check failing"

      - alert: GammaHighCreditBurn
        expr: rate(gamma_credits_total[1h]) > 100
        for: 30m
        annotations:
          summary: "Gamma credit consumption > 100/hour"

      - alert: GammaLowCompletionRate
        expr: gamma_completions_total / gamma_generations_total < 0.8
        for: 15m
        annotations:
          summary: "Gamma generation completion rate below 80%"
```

## Key Metrics to Monitor

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| API error rate | < 5% | 5-10% | > 10% |
| Health check latency | < 2s | 2-5s | > 5s |
| Generation completion rate | > 90% | 80-90% | < 80% |
| Credits per hour | Within budget | 75% of budget | Over budget |
| Average generation time | < 30s | 30-60s | > 60s |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics not appearing | Scrape config wrong | Check Prometheus targets |
| Health check flapping | Network jitter | Add `for: 2m` to alert rules |
| Credit alerts too noisy | Thresholds too low | Calibrate to your usage pattern |
| Missing generation metrics | Not calling `recordCompletion()` | Ensure poll results feed metrics |

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Gamma Developer Docs](https://developers.gamma.app/)

## Next Steps

Proceed to `gamma-incident-runbook` for incident response.
