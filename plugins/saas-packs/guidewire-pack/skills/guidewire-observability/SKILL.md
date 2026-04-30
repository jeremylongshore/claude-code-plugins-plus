---
name: guidewire-observability
description: 'Monitor Guidewire InsuranceSuite: logging, metrics, tracing, and alerting
  via GCC.

  Trigger: "guidewire observability", "observability".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- insurance
- guidewire
compatibility: Designed for Claude Code
---
# Guidewire Observability

## Overview

Guidewire InsuranceSuite processes claims, policies, and billing through long-running batch jobs and synchronous Cloud APIs. Observability must track claim processing times, policy synchronization health, billing accuracy, and integration endpoint status. Batch failures in ClaimCenter or PolicyCenter can silently block downstream workflows, so real-time alerting on queue depth and job completion is critical for insurance operations SLAs.

## Key Metrics

| Metric | Type | Target | Alert Threshold |
|--------|------|--------|-----------------|
| Claim processing time | Histogram | < 30s | > 60s |
| Policy sync success rate | Gauge | > 99.5% | < 98% |
| Billing accuracy rate | Gauge | > 99.9% | < 99.5% |
| Cloud API latency p95 | Histogram | < 500ms | > 2s |
| Batch job completion rate | Gauge | 100% | < 95% per cycle |
| Integration queue depth | Gauge | < 100 | > 500 |

## Instrumentation

```typescript
async function trackGuidewireAPI(endpoint: string, operation: string, fn: () => Promise<any>) {
  const start = Date.now();
  try {
    const result = await fn();
    metrics.histogram('guidewire.api.latency', Date.now() - start, { endpoint, operation });
    metrics.increment('guidewire.api.calls', { endpoint, status: 'ok' });
    return result;
  } catch (err) {
    metrics.increment('guidewire.api.errors', { endpoint, status: err.statusCode });
    throw err;
  }
}
```

## Health Check Dashboard

```typescript
async function guidewireHealth(): Promise<Record<string, string>> {
  const batchStatus = await gccAdmin.getBatchJobStatus();
  const apiLatency = await metrics.query('guidewire.api.latency', 'p95', '5m');
  const queueDepth = await gccAdmin.getIntegrationQueueDepth();
  return {
    batch_jobs: batchStatus.allCompleted ? 'healthy' : 'failed',
    api_latency: apiLatency < 500 ? 'healthy' : 'slow',
    integration_queue: queueDepth < 100 ? 'healthy' : 'backlogged',
  };
}
```

## Alerting Rules

```typescript
const alerts = [
  { metric: 'guidewire.claim.processing_time_p95', condition: '> 60s', window: '15m', severity: 'warning' },
  { metric: 'guidewire.batch.completion_rate', condition: '< 0.95', window: '1h', severity: 'critical' },
  { metric: 'guidewire.integration.queue_depth', condition: '> 500', window: '10m', severity: 'critical' },
  { metric: 'guidewire.api.error_rate', condition: '> 0.02', window: '5m', severity: 'warning' },
];
```

## Structured Logging

```typescript
function logGuidewireEvent(event: string, data: Record<string, any>) {
  console.log(JSON.stringify({
    service: 'guidewire', event,
    module: data.module, // ClaimCenter | PolicyCenter | BillingCenter
    operation: data.operation, duration_ms: data.latency,
    // Redact PII: no policyholder names, SSNs, or claim details
    claim_id: data.claimId, policy_number: data.policyNum,
    timestamp: new Date().toISOString(),
  }));
}
```

## Error Handling

| Signal | Meaning | Action |
|--------|---------|--------|
| Batch job timeout | Long-running claim/policy sync stalled | Check GCC batch monitor, restart job |
| Queue depth > 500 | Integration backlog growing | Scale consumers, check downstream APIs |
| Policy sync < 98% | Data mismatch between systems | Audit sync logs, compare source records |
| API 503 errors | GCC maintenance or overload | Check GCC status page, retry with backoff |
| Billing discrepancy | Calculation or rounding error | Flag for manual review, audit batch output |

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)

## Next Steps

See `guidewire-incident-runbook`.
