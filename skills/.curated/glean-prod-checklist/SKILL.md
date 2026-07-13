---
name: glean-prod-checklist
description: 'Pre-launch: All datasources indexed and searchable.

  Trigger: "glean prod checklist", "prod-checklist".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Production Checklist

## Overview

Glean provides enterprise search across all company data sources with AI-powered ranking and document understanding. A production integration requires all connectors indexed, document permissions correctly mapped, and search quality validated. Failures mean employees find stale documents, see content they lack permission for, or get zero results when data exists.

## Authentication & Secrets

- [ ] `GLEAN_API_KEY` stored in secrets manager (not config files)
- [ ] Indexing API token separated from Search API token
- [ ] Key rotation schedule documented (quarterly cycle)
- [ ] Separate credentials for staging/prod environments
- [ ] Service account permissions scoped per data source connector

## API Integration

- [ ] Production base URL configured (`https://api.glean.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] All data source connectors configured and initial crawl complete
- [ ] Document permission mapping tested with different user roles
- [ ] Connector sync scheduled (daily cron or event-driven webhooks)
- [ ] Bulk indexing supports incremental updates (not full re-index)
- [ ] Search query tested across all indexed data sources

## Error Handling & Resilience

- [ ] Circuit breaker configured for Glean API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Connector sync failure detection within 1 hour
- [ ] Stale index detection (alert if last update > 24 hours)
- [ ] Document permission errors logged (access denied on indexed docs)
- [ ] Fallback search plan if Glean is unavailable

## Monitoring & Alerting

- [ ] API latency tracked per endpoint (search, indexing)
- [ ] Error rate alerts set (threshold: >3% over 5 minutes)
- [ ] Connector health dashboard showing sync status per source
- [ ] Search quality metrics tracked (click-through rate, zero-result rate)
- [ ] Index document count monitored for unexpected drops

## Validation Script

```typescript
async function checkGleanReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // Search API connectivity
  try {
    const res = await fetch('https://api.glean.com/v1/search', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.GLEAN_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'test', pageSize: 1 }),
    });
    checks.push({ name: 'Search API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Search API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.GLEAN_API_KEY, detail: process.env.GLEAN_API_KEY ? 'Present' : 'MISSING' });
  // Indexing API connectivity
  try {
    const res = await fetch('https://api.glean.com/v1/index/status', {
      headers: { Authorization: `Bearer ${process.env.GLEAN_API_KEY}` },
    });
    checks.push({ name: 'Indexing API', pass: res.ok, detail: res.ok ? 'Accessible' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Indexing API', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkGleanReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| Permission mapping | Users see unauthorized documents | P1 |
| Connector sync monitoring | Stale search results across org | P1 |
| API key rotation | Expired key halts indexing pipeline | P2 |
| Zero-result tracking | Employees lose trust in search | P2 |
| Index count monitoring | Silent data source disconnection | P3 |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-security-basics` for document permission mapping and access control.
