---
name: hubspot-observability
description: |
  Set up observability for HubSpot integrations with metrics, traces, and alerts.
  Use when implementing monitoring for HubSpot API operations, setting up dashboards,
  or configuring alerting for CRM integration health.
  Trigger with phrases like "hubspot monitoring", "hubspot metrics",
  "hubspot observability", "monitor hubspot", "hubspot alerts", "hubspot dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Observability

## Overview

Instrument HubSpot API calls with Prometheus metrics, OpenTelemetry tracing, and structured logging to monitor CRM integration health.

## Prerequisites

- Prometheus or compatible metrics backend
- OpenTelemetry SDK (optional, for tracing)
- Structured logging library (pino recommended)

## Instructions

### Step 1: Prometheus Metrics

```typescript
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const hubspotRequests = new Counter({
  name: 'hubspot_api_requests_total',
  help: 'Total HubSpot API requests',
  labelNames: ['method', 'object_type', 'status'],
  registers: [registry],
});

const hubspotLatency = new Histogram({
  name: 'hubspot_api_request_duration_seconds',
  help: 'HubSpot API request duration',
  labelNames: ['method', 'object_type'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2, 5],
  registers: [registry],
});

const hubspotRateLimit = new Gauge({
  name: 'hubspot_rate_limit_remaining',
  help: 'HubSpot daily rate limit remaining',
  labelNames: ['type'],
  registers: [registry],
});

const hubspotErrors = new Counter({
  name: 'hubspot_api_errors_total',
  help: 'HubSpot API errors by category',
  labelNames: ['status_code', 'category'],
  registers: [registry],
});
```

### Step 2: Instrumented Client Wrapper

```typescript
import * as hubspot from '@hubspot/api-client';

class InstrumentedHubSpotClient {
  private client: hubspot.Client;

  constructor() {
    this.client = new hubspot.Client({
      accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
      numberOfApiCallRetries: 3,
    });
  }

  async tracked<T>(
    method: string,
    objectType: string,
    operation: () => Promise<T>
  ): Promise<T> {
    const timer = hubspotLatency.startTimer({ method, object_type: objectType });

    try {
      const result = await operation();
      hubspotRequests.inc({ method, object_type: objectType, status: 'success' });
      return result;
    } catch (error: any) {
      const statusCode = error?.code || error?.statusCode || 500;
      const category = error?.body?.category || 'UNKNOWN';

      hubspotRequests.inc({ method, object_type: objectType, status: 'error' });
      hubspotErrors.inc({ status_code: String(statusCode), category });
      throw error;
    } finally {
      timer();
    }
  }

  // Example: instrumented contact operations
  async getContact(id: string, properties: string[]) {
    return this.tracked('GET', 'contacts', () =>
      this.client.crm.contacts.basicApi.getById(id, properties)
    );
  }

  async createContact(properties: Record<string, string>) {
    return this.tracked('POST', 'contacts', () =>
      this.client.crm.contacts.basicApi.create({ properties, associations: [] })
    );
  }

  async searchContacts(query: any) {
    return this.tracked('SEARCH', 'contacts', () =>
      this.client.crm.contacts.searchApi.doSearch(query)
    );
  }

  async batchReadContacts(ids: string[], properties: string[]) {
    return this.tracked('BATCH_READ', 'contacts', () =>
      this.client.crm.contacts.batchApi.read({
        inputs: ids.map(id => ({ id })),
        properties,
        propertiesWithHistory: [],
      })
    );
  }
}
```

### Step 3: Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  name: 'hubspot-integration',
  level: process.env.LOG_LEVEL || 'info',
  serializers: {
    // Redact access tokens from logs
    err: pino.stdSerializers.err,
    hubspot: (data: any) => ({
      ...data,
      accessToken: undefined,
    }),
  },
});

// Log HubSpot operations with context
function logHubSpotOp(operation: string, data: Record<string, any>, durationMs: number) {
  logger.info({
    service: 'hubspot',
    operation,
    durationMs,
    ...data,
  }, `HubSpot ${operation} completed`);
}

// Log errors with correlation IDs
function logHubSpotError(operation: string, error: any) {
  logger.error({
    service: 'hubspot',
    operation,
    statusCode: error?.code || error?.statusCode,
    category: error?.body?.category,
    correlationId: error?.body?.correlationId,
    message: error?.body?.message || error.message,
  }, `HubSpot ${operation} failed`);
}
```

### Step 4: Alert Configuration

```yaml
# hubspot_alerts.yaml (Prometheus AlertManager)
groups:
  - name: hubspot_alerts
    rules:
      - alert: HubSpotHighErrorRate
        expr: |
          rate(hubspot_api_errors_total[5m]) /
          rate(hubspot_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "HubSpot API error rate > 5%"
          description: "{{ $value | humanizePercentage }} error rate"

      - alert: HubSpotHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(hubspot_api_request_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "HubSpot API P95 latency > 3s"

      - alert: HubSpotRateLimitLow
        expr: hubspot_rate_limit_remaining{type="daily"} < 50000
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "HubSpot daily rate limit below 10%"

      - alert: HubSpotAuthFailure
        expr: increase(hubspot_api_errors_total{status_code="401"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "HubSpot authentication failure -- token may be revoked"
```

### Step 5: Metrics Endpoint

```typescript
import express from 'express';

const app = express();

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});

// Update rate limit gauge periodically
setInterval(async () => {
  try {
    const response = await fetch(
      'https://api.hubapi.com/crm/v3/objects/contacts?limit=1',
      { headers: { Authorization: `Bearer ${process.env.HUBSPOT_ACCESS_TOKEN}` } }
    );
    const remaining = response.headers.get('x-hubspot-ratelimit-daily-remaining');
    if (remaining) {
      hubspotRateLimit.set({ type: 'daily' }, parseInt(remaining));
    }
  } catch { /* ignore monitoring errors */ }
}, 60000);
```

## Output

- Prometheus metrics: request count, latency histogram, error rate, rate limit gauge
- Instrumented client wrapper tracking all HubSpot operations
- Structured logging with correlation IDs and redacted secrets
- AlertManager rules for error rate, latency, rate limits, and auth failures
- `/metrics` endpoint for Prometheus scraping

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | Operations not using instrumented client | Wrap all calls through `tracked()` |
| High cardinality | Too many label values | Limit labels to method + object_type |
| Alert storms | Thresholds too sensitive | Adjust `for` duration and percentages |
| Logging PII | Contact data in logs | Use serializers to redact sensitive fields |

## Resources

- [Prometheus Client for Node.js](https://github.com/siimon/prom-client)
- [OpenTelemetry JS](https://opentelemetry.io/docs/languages/js/)
- [Pino Logger](https://github.com/pinojs/pino)

## Next Steps

For incident response, see `hubspot-incident-runbook`.
