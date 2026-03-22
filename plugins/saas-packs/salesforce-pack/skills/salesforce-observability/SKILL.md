---
name: salesforce-observability
description: |
  Set up observability for Salesforce integrations with API limit monitoring, error tracking, and alerting.
  Use when implementing monitoring for Salesforce operations, tracking API consumption,
  or configuring alerting for Salesforce integration health.
  Trigger with phrases like "salesforce monitoring", "salesforce metrics",
  "salesforce observability", "monitor salesforce", "salesforce alerts", "salesforce API usage dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Observability

## Overview
Instrument Salesforce integrations with API limit monitoring, SOQL performance tracking, error classification, and alerting. Uses Salesforce's built-in Limits API and EventLogFile for deep visibility.

## Prerequisites
- jsforce connection configured
- Prometheus or compatible metrics backend (optional)
- Grafana or similar dashboarding tool (optional)
- Salesforce Enterprise+ for EventLogFile access

## Instructions

### Step 1: API Limit Monitoring (Core Metric)

```typescript
import { getConnection } from './salesforce/connection';
import { Registry, Gauge, Counter, Histogram } from 'prom-client';

const registry = new Registry();

// The single most important Salesforce metric
const apiLimitGauge = new Gauge({
  name: 'salesforce_api_limit_remaining',
  help: 'Remaining daily API calls',
  registers: [registry],
});

const apiLimitMaxGauge = new Gauge({
  name: 'salesforce_api_limit_max',
  help: 'Maximum daily API calls',
  registers: [registry],
});

const apiUsagePercent = new Gauge({
  name: 'salesforce_api_usage_percent',
  help: 'Percentage of daily API calls used',
  registers: [registry],
});

// Poll limits every 5 minutes (each poll = 1 API call)
setInterval(async () => {
  try {
    const conn = await getConnection();
    const limits = await conn.request('/services/data/v59.0/limits/');

    apiLimitGauge.set(limits.DailyApiRequests.Remaining);
    apiLimitMaxGauge.set(limits.DailyApiRequests.Max);

    const used = limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining;
    apiUsagePercent.set((used / limits.DailyApiRequests.Max) * 100);
  } catch (error) {
    console.error('Failed to poll SF limits:', error);
  }
}, 5 * 60 * 1000);
```

### Step 2: Request Instrumentation

```typescript
const sfRequestDuration = new Histogram({
  name: 'salesforce_request_duration_seconds',
  help: 'Salesforce API request duration',
  labelNames: ['operation', 'sobject'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const sfRequestCounter = new Counter({
  name: 'salesforce_requests_total',
  help: 'Total Salesforce API requests',
  labelNames: ['operation', 'sobject', 'status'],
  registers: [registry],
});

const sfErrorCounter = new Counter({
  name: 'salesforce_errors_total',
  help: 'Salesforce errors by error code',
  labelNames: ['error_code', 'sobject'],
  registers: [registry],
});

// Instrumented wrapper for all SF operations
async function instrumentedSfCall<T>(
  operation: string,
  sobject: string,
  fn: () => Promise<T>
): Promise<T> {
  const timer = sfRequestDuration.startTimer({ operation, sobject });

  try {
    const result = await fn();
    sfRequestCounter.inc({ operation, sobject, status: 'success' });
    return result;
  } catch (error: any) {
    const errorCode = error.errorCode || 'UNKNOWN';
    sfRequestCounter.inc({ operation, sobject, status: 'error' });
    sfErrorCounter.inc({ error_code: errorCode, sobject });
    throw error;
  } finally {
    timer();
  }
}

// Usage
const accounts = await instrumentedSfCall('query', 'Account', () =>
  conn.query('SELECT Id, Name FROM Account LIMIT 10')
);
```

### Step 3: Salesforce-Native Monitoring (EventLogFile)

```typescript
// EventLogFile provides detailed API usage data (Enterprise+ only)
// Available event types: API, Login, Logout, URI, BulkApi, etc.

async function getApiUsageEvents(days: number = 1) {
  const conn = await getConnection();

  const events = await conn.query(`
    SELECT Id, EventType, LogDate, LogFileLength
    FROM EventLogFile
    WHERE EventType IN ('API', 'RestApi', 'BulkApi')
      AND LogDate >= LAST_N_DAYS:${days}
    ORDER BY LogDate DESC
  `);

  for (const event of events.records) {
    // Download and parse the CSV log file
    const logContent = await conn.request(
      `/services/data/v59.0/sobjects/EventLogFile/${event.Id}/LogFile`
    );
    // Parse CSV to extract: USER_ID, URI, METHOD, STATUS_CODE, RUN_TIME, CPU_TIME
    console.log(`${event.EventType} on ${event.LogDate}: ${event.LogFileLength} bytes`);
  }
}
```

### Step 4: Structured Logging

```typescript
import pino from 'pino';

const logger = pino({ name: 'salesforce-integration' });

function logSfOperation(
  operation: string,
  sobject: string,
  details: Record<string, any>,
  durationMs: number
) {
  logger.info({
    service: 'salesforce',
    operation,
    sobject,
    durationMs,
    ...details,
    // Parse Sforce-Limit-Info header from response
    // Format: "api-usage=135/150000"
  });
}
```

### Step 5: Alert Rules

```yaml
# prometheus-alerts.yaml
groups:
  - name: salesforce_alerts
    rules:
      - alert: SalesforceApiLimitCritical
        expr: salesforce_api_usage_percent > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Salesforce API usage above 90% ({{ $value }}%)"
          description: "API calls will be blocked at 100%. Reduce usage or contact Salesforce for limit increase."

      - alert: SalesforceApiLimitWarning
        expr: salesforce_api_usage_percent > 75
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Salesforce API usage above 75%"

      - alert: SalesforceHighErrorRate
        expr: |
          rate(salesforce_errors_total[5m]) /
          rate(salesforce_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Salesforce error rate > 5%"

      - alert: SalesforceHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(salesforce_request_duration_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Salesforce P95 latency > 5s"

      - alert: SalesforceAuthFailure
        expr: increase(salesforce_errors_total{error_code="INVALID_SESSION_ID"}[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Salesforce authentication failures detected"
```

## Key Salesforce Metrics to Monitor

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Daily API remaining | `/services/data/v59.0/limits/` | < 10% remaining |
| Request latency P95 | Instrumented client | > 5 seconds |
| Error rate by code | Instrumented client | > 5% |
| Bulk API job failures | Bulk job results | Any failures |
| Session/token expiry | Auth error count | Any INVALID_SESSION_ID |
| Data storage used | Limits API | > 90% capacity |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Limits poll failing | Token expired | Auto-refresh connection |
| High cardinality | Too many label values | Use error_code, not error message |
| Missing EventLogFile | Not Enterprise+ | Use instrumented client instead |
| Alert storms | Threshold too low | Tune thresholds with historical data |

## Resources
- [Limits REST Resource](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm)
- [EventLogFile](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
- [Salesforce Status API](https://api.status.salesforce.com/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)

## Next Steps
For incident response, see `salesforce-incident-runbook`.
