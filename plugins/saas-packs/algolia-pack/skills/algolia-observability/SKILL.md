---
name: algolia-observability
description: |
  Set up observability for Algolia: Prometheus metrics for search latency/errors,
  OpenTelemetry tracing, structured logging, and Grafana dashboards.
  Trigger: "algolia monitoring", "algolia metrics", "algolia observability",
  "monitor algolia", "algolia alerts", "algolia tracing", "algolia dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Observability

## Overview

Algolia provides built-in analytics in the dashboard, but production systems need application-level observability: latency histograms, error rate counters, distributed traces, and alerts. This skill instruments the `algoliasearch` v5 client with Prometheus, OpenTelemetry, and structured logging.

## Key Metrics to Track

| Metric | Type | Why It Matters |
|--------|------|---------------|
| Search latency (P50/P95/P99) | Histogram | User experience, SLA compliance |
| Search requests/sec | Counter | Capacity planning, cost tracking |
| Error rate by type | Counter | Detect API issues before users report |
| Index freshness (last updated) | Gauge | Data pipeline health |
| Record count | Gauge | Cost monitoring, data integrity |

## Instructions

### Step 1: Instrumented Algolia Client Wrapper

```typescript
// src/algolia/instrumented-client.ts
import { algoliasearch, ApiError } from 'algoliasearch';
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const searchLatency = new Histogram({
  name: 'algolia_search_duration_seconds',
  help: 'Algolia search request duration in seconds',
  labelNames: ['index', 'status'],
  buckets: [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5],
  registers: [registry],
});

const searchTotal = new Counter({
  name: 'algolia_search_requests_total',
  help: 'Total Algolia search requests',
  labelNames: ['index', 'status'],
  registers: [registry],
});

const searchErrors = new Counter({
  name: 'algolia_errors_total',
  help: 'Total Algolia errors by type',
  labelNames: ['index', 'error_type', 'status_code'],
  registers: [registry],
});

const indexRecords = new Gauge({
  name: 'algolia_index_records',
  help: 'Number of records in Algolia index',
  labelNames: ['index'],
  registers: [registry],
});

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

export async function instrumentedSearch<T = any>(
  indexName: string,
  searchParams: Record<string, any>
) {
  const timer = searchLatency.startTimer({ index: indexName });

  try {
    const result = await client.searchSingleIndex<T>({ indexName, searchParams });
    timer({ status: 'success' });
    searchTotal.inc({ index: indexName, status: 'success' });
    return result;
  } catch (error) {
    timer({ status: 'error' });
    searchTotal.inc({ index: indexName, status: 'error' });

    if (error instanceof ApiError) {
      searchErrors.inc({
        index: indexName,
        error_type: error.status === 429 ? 'rate_limit' : 'api_error',
        status_code: String(error.status),
      });
    } else {
      searchErrors.inc({
        index: indexName,
        error_type: 'network',
        status_code: '0',
      });
    }
    throw error;
  }
}

// Periodic index stats collection (run every 5 minutes)
export async function collectIndexMetrics() {
  const { items } = await client.listIndices();
  for (const idx of items) {
    indexRecords.set({ index: idx.name }, idx.entries || 0);
  }
}

export { registry };
```

### Step 2: Prometheus Metrics Endpoint

```typescript
// src/api/metrics.ts (Express example)
import express from 'express';
import { registry, collectIndexMetrics } from '../algolia/instrumented-client';

const app = express();

app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});

// Collect index stats every 5 minutes
setInterval(collectIndexMetrics, 5 * 60 * 1000);
```

### Step 3: OpenTelemetry Distributed Tracing

```typescript
// src/algolia/tracing.ts
import { trace, SpanStatusCode, type Span } from '@opentelemetry/api';

const tracer = trace.getTracer('algolia-service', '1.0.0');

export async function tracedSearch<T>(
  indexName: string,
  query: string,
  searchParams: Record<string, any> = {}
): Promise<T> {
  return tracer.startActiveSpan(`algolia.search ${indexName}`, async (span: Span) => {
    span.setAttribute('algolia.index', indexName);
    span.setAttribute('algolia.query', query);
    span.setAttribute('algolia.hitsPerPage', searchParams.hitsPerPage || 20);

    try {
      const result = await client.searchSingleIndex<T>({
        indexName,
        searchParams: { query, ...searchParams },
      });

      span.setAttribute('algolia.nbHits', result.nbHits);
      span.setAttribute('algolia.processingTimeMS', result.processingTimeMS);
      span.setStatus({ code: SpanStatusCode.OK });
      return result as T;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

### Step 4: Structured Logging

```typescript
// src/algolia/logger.ts
import pino from 'pino';

const logger = pino({ name: 'algolia', level: process.env.LOG_LEVEL || 'info' });

export function logSearch(params: {
  index: string;
  query: string;
  nbHits: number;
  processingTimeMS: number;
  page: number;
  userId?: string;
}) {
  logger.info({
    event: 'algolia.search',
    index: params.index,
    query: params.query,
    hits: params.nbHits,
    latency_ms: params.processingTimeMS,
    page: params.page,
    user: params.userId,
  });
}

export function logSearchError(params: {
  index: string;
  query: string;
  error: string;
  statusCode?: number;
}) {
  logger.error({
    event: 'algolia.search.error',
    index: params.index,
    query: params.query,
    error: params.error,
    status_code: params.statusCode,
  });
}
```

### Step 5: Alert Rules (Prometheus AlertManager)

```yaml
# alerts/algolia.yml
groups:
  - name: algolia
    rules:
      - alert: AlgoliaHighErrorRate
        expr: |
          rate(algolia_errors_total[5m]) /
          rate(algolia_search_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Algolia error rate > 5% for 5 minutes"

      - alert: AlgoliaHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(algolia_search_duration_seconds_bucket[5m])
          ) > 0.5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Algolia P95 search latency > 500ms"

      - alert: AlgoliaRateLimited
        expr: rate(algolia_errors_total{error_type="rate_limit"}[5m]) > 0
        for: 2m
        labels: { severity: critical }
        annotations:
          summary: "Algolia returning 429 rate limit errors"

      - alert: AlgoliaIndexStale
        expr: algolia_index_records == 0
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Algolia index has 0 records — possible sync failure"
```

## Grafana Dashboard Queries

```
# Search rate: rate(algolia_search_requests_total[5m])
# Error rate: rate(algolia_errors_total[5m]) / rate(algolia_search_requests_total[5m])
# P50 latency: histogram_quantile(0.5, rate(algolia_search_duration_seconds_bucket[5m]))
# P95 latency: histogram_quantile(0.95, rate(algolia_search_duration_seconds_bucket[5m]))
# Records per index: algolia_index_records
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | Client not instrumented | Use `instrumentedSearch` wrapper |
| High cardinality | Too many label values | Don't use query text as label |
| Trace gaps | Missing context propagation | Ensure OTel context flows through async |
| Alert storms | Thresholds too sensitive | Add `for: 5m` minimum duration |

## Resources

- [Prometheus Client](https://www.npmjs.com/package/prom-client)
- [OpenTelemetry JS](https://opentelemetry.io/docs/languages/js/)
- [Algolia Dashboard Analytics](https://www.algolia.com/doc/guides/getting-analytics/search-analytics/)
- [pino Logger](https://getpino.io/)

## Next Steps

For incident response, see `algolia-incident-runbook`.
