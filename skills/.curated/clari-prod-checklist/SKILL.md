---
name: clari-prod-checklist
description: 'Production readiness checklist for Clari API integrations.

  Use when launching a Clari data pipeline, validating export automation,

  or preparing for production forecast sync.

  Trigger with phrases like "clari production", "clari go-live",

  "clari checklist", "clari launch".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari Production Checklist

## Overview

Clari provides revenue intelligence through forecast data, pipeline analytics, and deal inspection. A production integration typically exports forecast snapshots, syncs pipeline data to a warehouse, and powers revenue dashboards. Incorrect data pipelines mean unreliable forecasts, missed quota signals, or stale deal intelligence that undermines board-level reporting.

## Authentication & Secrets

- [ ] `CLARI_API_KEY` stored in secrets manager (not config files)
- [ ] Token tested against production endpoint before go-live
- [ ] Key rotation procedure documented (quarterly cycle)
- [ ] Separate tokens for dev/staging/prod environments
- [ ] Service account with least-privilege scopes (read-only for exports)

## API Integration

- [ ] Production base URL configured (`https://api.clari.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] All required `typesToExport` configured (forecast, quota, crm_closed)
- [ ] Time period coverage verified (current quarter + 4 historical)
- [ ] Deduplication logic handles re-exports and overlapping periods
- [ ] Pagination implemented for large pipeline result sets
- [ ] Export job polling with configurable timeout (default: 10 min)

## Error Handling & Resilience

- [ ] Circuit breaker configured for Clari API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Empty export results handled (data quality alert, not silent pass)
- [ ] Export job timeout detection with automatic re-queue
- [ ] MERGE/UPSERT in warehouse prevents duplicate forecast records
- [ ] Data retention policy enforced (rolling 8 quarters typical)

## Monitoring & Alerting

- [ ] API latency tracked per export job
- [ ] Error rate alerts set (threshold: any export failure)
- [ ] Forecast amount anomaly detection (>20% swing triggers review)
- [ ] Pipeline health dashboard with job completion rates
- [ ] Daily reconciliation: exported row counts vs expected

## Validation Script

```typescript
async function checkClariReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.clari.com/v1/forecast/types', {
      headers: { Authorization: `Bearer ${process.env.CLARI_API_KEY}` },
    });
    checks.push({ name: 'Clari API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Clari API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.CLARI_API_KEY, detail: process.env.CLARI_API_KEY ? 'Present' : 'MISSING' });
  // Export types available
  try {
    const res = await fetch('https://api.clari.com/v1/forecast/types', {
      headers: { Authorization: `Bearer ${process.env.CLARI_API_KEY}` },
    });
    const data = await res.json();
    const count = Array.isArray(data) ? data.length : 0;
    checks.push({ name: 'Export Types', pass: count > 0, detail: `${count} types available` });
  } catch (e: any) { checks.push({ name: 'Export Types', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkClariReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Expired token halts all exports | P1 |
| Empty export detection | Silent data gaps in forecasts | P1 |
| Duplicate record prevention | Inflated pipeline numbers | P2 |
| Export job timeout | Stuck jobs block scheduling queue | P2 |
| Forecast anomaly alerts | Missed revenue signals | P3 |

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)
- [Clari Status](https://status.clari.com)

## Next Steps

See `clari-security-basics` for data access controls and PII handling.
