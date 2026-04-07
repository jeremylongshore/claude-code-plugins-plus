---
name: openevidence-observability
description: |
  Observability for OpenEvidence.
  Trigger: "openevidence observability".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Observability

## Overview

OpenEvidence delivers clinical evidence queries where response accuracy and freshness have direct patient safety implications. Monitor query response times to ensure clinicians get timely answers, track evidence freshness to catch stale citations, and audit every query for compliance. Observability must also verify citation accuracy and maintain complete audit logs for regulatory requirements (HIPAA, clinical decision support standards).

## Key Metrics

| Metric | Type | Target | Alert Threshold |
|--------|------|--------|-----------------|
| Query response time p95 | Histogram | < 3s | > 8s |
| Evidence freshness | Gauge | < 7 days median | > 30 days |
| Citation accuracy rate | Gauge | > 95% | < 90% |
| API error rate | Gauge | < 0.5% | > 2% |
| Audit log completeness | Gauge | 100% | < 99.9% |
| Daily query volume | Counter | Within quota | > 90% quota |

## Instrumentation

```typescript
async function trackClinicalQuery(queryType: string, fn: () => Promise<any>) {
  const start = Date.now();
  const traceId = crypto.randomUUID();
  try {
    const result = await fn();
    metrics.histogram('openevidence.query.latency', Date.now() - start, { queryType });
    metrics.increment('openevidence.query.total', { queryType });
    auditLog.record({ traceId, queryType, status: 'ok', latency: Date.now() - start });
    return result;
  } catch (err) {
    metrics.increment('openevidence.query.errors', { queryType, error: err.code });
    auditLog.record({ traceId, queryType, status: 'error', error: err.message });
    throw err;
  }
}
```

## Health Check Dashboard

```typescript
async function openEvidenceHealth(): Promise<Record<string, string>> {
  const latencyP95 = await metrics.query('openevidence.query.latency', 'p95', '5m');
  const errorRate = await metrics.query('openevidence.query.error_rate', 'avg', '5m');
  const freshness = await openEvAdmin.getMedianEvidenceAge();
  return {
    query_latency: latencyP95 < 3000 ? 'healthy' : 'slow',
    error_rate: errorRate < 0.005 ? 'healthy' : 'degraded',
    evidence_freshness: freshness < 7 ? 'healthy' : 'stale',
  };
}
```

## Alerting Rules

```typescript
const alerts = [
  { metric: 'openevidence.query.latency_p95', condition: '> 8s', window: '10m', severity: 'warning' },
  { metric: 'openevidence.query.error_rate', condition: '> 0.02', window: '5m', severity: 'critical' },
  { metric: 'openevidence.evidence.median_age_days', condition: '> 30', window: '1d', severity: 'warning' },
  { metric: 'openevidence.audit.completeness', condition: '< 0.999', window: '1h', severity: 'critical' },
];
```

## Structured Logging

```typescript
function logClinicalEvent(event: string, data: Record<string, any>) {
  console.log(JSON.stringify({
    service: 'openevidence', event,
    query_type: data.queryType, duration_ms: data.latency,
    citation_count: data.citations, evidence_age_days: data.evidenceAge,
    // HIPAA: never log patient identifiers or query text
    trace_id: data.traceId, audit_seq: data.auditSeq,
    timestamp: new Date().toISOString(),
  }));
}
```

## Error Handling

| Signal | Meaning | Action |
|--------|---------|--------|
| Query timeout > 8s | Evidence index overloaded | Check index health, scale read replicas |
| Citation accuracy drop | Stale or retracted sources | Trigger evidence refresh pipeline |
| Audit log gap | Logging pipeline failure | Critical — investigate immediately for compliance |
| 429 rate limit | Quota approaching limit | Throttle non-critical queries, request increase |
| Evidence age > 30 days | Refresh pipeline stalled | Check ingestion jobs, verify source feeds |

## Resources

- [OpenEvidence](https://www.openevidence.com)

## Next Steps

See `openevidence-incident-runbook`.
