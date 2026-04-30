---
name: hex-prod-checklist
description: 'Execute Hex production deployment checklist and rollback procedures.

  Use when deploying Hex integrations to production, preparing for launch,

  or implementing go-live procedures.

  Trigger with phrases like "hex production", "deploy hex",

  "hex go-live", "hex launch checklist".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex Production Checklist

## Overview

Hex is a collaborative data analytics platform where teams build notebooks, dashboards, and scheduled data pipelines. A production integration triggers project runs, retrieves results, and monitors pipeline health via the Hex API. Failures mean stale dashboards, broken scheduled reports, or data pipelines that silently stop producing output for downstream consumers.

## Authentication & Secrets

- [ ] `HEX_API_KEY` stored in secrets manager (not config files)
- [ ] Token scoped to "Run projects" permission only
- [ ] Token expiration set > 90 days with calendar renewal reminder
- [ ] Separate tokens for dev/staging/prod workspaces
- [ ] Key rotation schedule documented (quarterly cycle)

## API Integration

- [ ] Production base URL configured (`https://app.hex.tech/api/v1`)
- [ ] Rate limits respected (20 requests/min, 60/hour)
- [ ] All orchestrated projects published before triggering runs
- [ ] Input parameters documented and validated before submission
- [ ] Run status polling with configurable interval (default: 5s)
- [ ] Result retrieval handles large datasets (pagination/streaming)
- [ ] Project version pinning prevents unexpected behavior changes

## Error Handling & Resilience

- [ ] Circuit breaker configured for Hex API outages
- [ ] Retry with exponential backoff for 429/5xx responses
- [ ] ERRORED and KILLED run states handled with alert + re-queue
- [ ] Run timeout detection (alert if run exceeds 2x typical duration)
- [ ] Database connection errors in Hex projects surface to caller
- [ ] Graceful degradation serves cached results when API is down

## Monitoring & Alerting

- [ ] API latency tracked per project run
- [ ] Error rate alerts set (any ERRORED run = notification)
- [ ] Run duration regression tracked (>50% increase = warning)
- [ ] Scheduled run completion rate monitored daily
- [ ] API quota usage tracked against plan limits

## Validation Script

```typescript
async function checkHexReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://app.hex.tech/api/v1/projects', {
      headers: { Authorization: `Bearer ${process.env.HEX_API_KEY}` },
    });
    checks.push({ name: 'Hex API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Hex API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.HEX_API_KEY, detail: process.env.HEX_API_KEY ? 'Present' : 'MISSING' });
  // Rate limit check
  try {
    const res = await fetch('https://app.hex.tech/api/v1/projects', {
      headers: { Authorization: `Bearer ${process.env.HEX_API_KEY}` },
    });
    const remaining = res.headers.get('x-ratelimit-remaining');
    checks.push({ name: 'Rate Limit', pass: Number(remaining) > 5, detail: `${remaining} remaining` });
  } catch (e: any) { checks.push({ name: 'Rate Limit', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkHexReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key expiration | All scheduled runs stop silently | P1 |
| ERRORED run detection | Stale dashboards served to stakeholders | P1 |
| Rate limit handling | Burst orchestration blocked by 429 | P2 |
| Run duration regression | Slow pipelines delay downstream reports | P2 |
| Project version pinning | Unexpected notebook changes break output | P3 |

## Resources

- [Hex API Overview](https://learn.hex.tech/docs/api/api-overview)
- [Hex Status](https://status.hex.tech)

## Next Steps

See `hex-security-basics` for data connection security and access control.
