---
name: maintainx-observability
description: |
  Implement comprehensive observability for MaintainX integrations.
  Use when setting up monitoring, logging, tracing, and alerting
  for MaintainX API integrations.
  Trigger with phrases like "maintainx monitoring", "maintainx logging",
  "maintainx metrics", "maintainx observability", "maintainx alerts".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Observability

## Overview
Implement metrics, structured logging, and alerting for MaintainX integrations to ensure reliability and rapid issue detection.

## Prerequisites
- MaintainX integration deployed
- Node.js 18+
- Monitoring platform (Prometheus/Grafana, Datadog, or CloudWatch)

## Instructions

### Step 1: Prometheus Metrics

```typescript
// src/observability/metrics.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const register = new Registry();

export const metrics = {
  apiRequests: new Counter({
    name: 'maintainx_api_requests_total',
    help: 'Total MaintainX API requests',
    labelNames: ['method', 'endpoint', 'status'],
    registers: [register],
  }),

  apiLatency: new Histogram({
    name: 'maintainx_api_latency_seconds',
    help: 'MaintainX API request latency',
    labelNames: ['method', 'endpoint'],
    buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
    registers: [register],
  }),

  rateLimitHits: new Counter({
    name: 'maintainx_rate_limit_hits_total',
    help: 'Times rate limited by MaintainX API',
    registers: [register],
  }),

  workOrdersProcessed: new Counter({
    name: 'maintainx_work_orders_processed_total',
    help: 'Work orders processed',
    labelNames: ['action', 'status'],
    registers: [register],
  }),

  syncLag: new Gauge({
    name: 'maintainx_sync_lag_seconds',
    help: 'Seconds since last successful sync',
    registers: [register],
  }),
};

export { register };
```

### Step 2: Instrumented API Client

```typescript
// src/observability/instrumented-client.ts
import axios, { AxiosInstance } from 'axios';
import { metrics } from './metrics';

export function createInstrumentedClient(apiKey: string): AxiosInstance {
  const client = axios.create({
    baseURL: 'https://api.getmaintainx.com/v1',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    timeout: 30_000,
  });

  client.interceptors.request.use((config) => {
    (config as any).__startTime = process.hrtime.bigint();
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      const elapsed = Number(process.hrtime.bigint() - (response.config as any).__startTime) / 1e9;
      const endpoint = response.config.url?.split('?')[0] || 'unknown';

      metrics.apiRequests.inc({
        method: response.config.method?.toUpperCase() || 'GET',
        endpoint,
        status: String(response.status),
      });
      metrics.apiLatency.observe(
        { method: response.config.method?.toUpperCase() || 'GET', endpoint },
        elapsed,
      );
      return response;
    },
    (error) => {
      const status = error.response?.status || 0;
      const endpoint = error.config?.url?.split('?')[0] || 'unknown';

      metrics.apiRequests.inc({
        method: error.config?.method?.toUpperCase() || 'GET',
        endpoint,
        status: String(status),
      });

      if (status === 429) {
        metrics.rateLimitHits.inc();
      }
      throw error;
    },
  );

  return client;
}
```

### Step 3: Structured Logging

```typescript
// src/observability/logger.ts

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  service: string;
  timestamp: string;
  [key: string]: any;
}

class StructuredLogger {
  private service: string;

  constructor(service: string) {
    this.service = service;
  }

  private log(level: LogLevel, message: string, data?: Record<string, any>) {
    const entry: LogEntry = {
      level,
      message,
      service: this.service,
      timestamp: new Date().toISOString(),
      ...data,
    };
    // JSON output for log aggregation (ELK, CloudWatch, Datadog)
    console.log(JSON.stringify(entry));
  }

  info(message: string, data?: Record<string, any>) { this.log('info', message, data); }
  warn(message: string, data?: Record<string, any>) { this.log('warn', message, data); }
  error(message: string, data?: Record<string, any>) { this.log('error', message, data); }
  debug(message: string, data?: Record<string, any>) { this.log('debug', message, data); }
}

export const logger = new StructuredLogger('maintainx-integration');

// Usage
logger.info('Work order created', { workOrderId: 12345, priority: 'HIGH' });
logger.error('API call failed', { endpoint: '/workorders', status: 500, retryCount: 2 });
```

### Step 4: Health and Metrics Endpoints

```typescript
// src/observability/server.ts
import express from 'express';
import { register, metrics } from './metrics';

const app = express();

// Prometheus scrape endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Health check with metrics
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    uptime: process.uptime(),
    metrics: {
      totalRequests: await metrics.apiRequests.get(),
      rateLimitHits: await metrics.rateLimitHits.get(),
      syncLagSeconds: (await metrics.syncLag.get()).values[0]?.value || 0,
    },
  };
  res.json(health);
});

app.listen(9090, () => logger.info('Metrics server on :9090'));
```

### Step 5: Alerting Rules (Prometheus)

```yaml
# prometheus/alerts.yml
groups:
  - name: maintainx
    rules:
      - alert: MaintainXHighErrorRate
        expr: rate(maintainx_api_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "MaintainX API error rate > 10%"

      - alert: MaintainXHighLatency
        expr: histogram_quantile(0.95, rate(maintainx_api_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MaintainX API p95 latency > 5s"

      - alert: MaintainXRateLimited
        expr: rate(maintainx_rate_limit_hits_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "MaintainX API rate limiting detected"

      - alert: MaintainXSyncStale
        expr: maintainx_sync_lag_seconds > 900
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "MaintainX sync lag > 15 minutes"
```

## Output
- Prometheus metrics (request count, latency histogram, rate limit counter, sync lag gauge)
- Instrumented axios client automatically recording metrics on every API call
- Structured JSON logging for all operations
- `/metrics` endpoint for Prometheus scraping
- Alerting rules for error rate, latency, rate limits, and sync staleness

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics endpoint 500 | prom-client not initialized | Ensure `Registry` is created before metrics |
| Missing labels | Metric name mismatch | Check `labelNames` match `inc()`/`observe()` calls |
| Log volume too high | Debug logging in production | Set `LOG_LEVEL=info` in production |
| Stale sync alert | Sync job stopped | Check cron schedule, restart sync process |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [prom-client](https://github.com/siimon/prom-client) -- Prometheus metrics for Node.js
- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)

## Next Steps
For incident response, see `maintainx-incident-runbook`.

## Examples

**Datadog integration using DogStatsD**:

```typescript
import StatsD from 'hot-shots';

const dogstatsd = new StatsD({ prefix: 'maintainx.' });

// Record API call
dogstatsd.increment('api.requests', 1, { endpoint: '/workorders', status: '200' });
dogstatsd.histogram('api.latency', 0.45, { endpoint: '/workorders' });
```
