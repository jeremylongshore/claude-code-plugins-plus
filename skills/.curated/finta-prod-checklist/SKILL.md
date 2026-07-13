---
name: finta-prod-checklist
description: 'Fundraise launch checklist using Finta CRM.

  Trigger with phrases like "finta checklist", "finta launch", "finta go-live".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Production Checklist

## Overview

Finta is a fundraising CRM for managing investor pipeline, deal rooms, and round tracking. A production integration syncs investor communications, manages deal room access, and automates pipeline stage transitions. Failures mean lost investor touchpoints, broken deal room links, or pipeline data that drifts from your actual fundraise state.

## Authentication & Secrets

- [ ] `FINTA_API_KEY` stored in secrets manager (not config files)
- [ ] OAuth tokens for email/calendar sync stored securely
- [ ] Key rotation schedule documented (before each fundraise round)
- [ ] Separate credentials for staging/prod environments
- [ ] Deal room access tokens scoped per investor group

## API Integration

- [ ] Production base URL configured (`https://api.finta.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] Pipeline stage sync tested with all custom stages
- [ ] Investor contact import validated (deduplication on email)
- [ ] Deal room link generation tested with expiration settings
- [ ] Email sync webhook configured for reply-to-stage automation
- [ ] Financial data integrations verified (Stripe, Mercury, Brex)

## Error Handling & Resilience

- [ ] Circuit breaker configured for Finta API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Email sync failure detection (stale inbox = missed investor replies)
- [ ] Deal room link expiration alerts before investor meetings
- [ ] Duplicate investor detection on bulk import
- [ ] Cap table import validation (share counts, ownership percentages)

## Monitoring & Alerting

- [ ] API latency tracked per endpoint (pipeline, investors, rooms)
- [ ] Error rate alerts set (threshold: any sync failure during active round)
- [ ] Investor reply detection latency monitored (<5 min SLA)
- [ ] Deal room access analytics reviewed weekly
- [ ] Pipeline stage transition audit log enabled

## Validation Script

```typescript
async function checkFintaReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.finta.com/v1/pipeline', {
      headers: { Authorization: `Bearer ${process.env.FINTA_API_KEY}` },
    });
    checks.push({ name: 'Finta API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Finta API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.FINTA_API_KEY, detail: process.env.FINTA_API_KEY ? 'Present' : 'MISSING' });
  // Pipeline stages configured
  try {
    const res = await fetch('https://api.finta.com/v1/pipeline/stages', {
      headers: { Authorization: `Bearer ${process.env.FINTA_API_KEY}` },
    });
    const data = await res.json();
    const count = Array.isArray(data) ? data.length : 0;
    checks.push({ name: 'Pipeline Stages', pass: count >= 3, detail: `${count} stages configured` });
  } catch (e: any) { checks.push({ name: 'Pipeline Stages', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkFintaReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Lost access during active fundraise | P1 |
| Email sync monitoring | Missed investor replies for days | P1 |
| Deal room link expiry | Investors hit dead links before meetings | P2 |
| Duplicate investor import | Fragmented communication history | P2 |
| Cap table validation | Incorrect ownership reported to board | P3 |

## Resources

- [Finta Platform](https://www.finta.com)
- [Finta Help Center](https://help.finta.com)

## Next Steps

See `finta-security-basics` for investor data protection and deal room access control.
