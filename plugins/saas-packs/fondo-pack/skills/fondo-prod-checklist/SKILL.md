---
name: fondo-prod-checklist
description: |
  Execute Fondo production readiness checklist for year-end tax filing,
  R&D credit claims, and board-ready financial reporting.
  Trigger: "fondo production", "fondo tax filing ready", "fondo year-end checklist".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Production Checklist

## Overview

Fondo handles startup tax preparation, R&D credit claims, bookkeeping, and compliance filings. A production integration syncs financial data from banking, payroll, and expense platforms into Fondo for automated tax workflows. Failures mean missed filing deadlines, incorrect R&D credit claims, or unreconciled books that block board reporting.

## Authentication & Secrets

- [ ] `FONDO_API_KEY` stored in secrets manager (not config files)
- [ ] Financial integration OAuth tokens stored securely (Stripe, Mercury, Brex)
- [ ] Key rotation scheduled before each tax season
- [ ] Separate credentials for staging/prod environments
- [ ] Payroll provider API tokens scoped to read-only

## API Integration

- [ ] Production base URL configured (`https://api.fondo.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] All bank accounts connected and syncing (verified daily)
- [ ] Payroll provider connected with W-2 and 1099 data flowing
- [ ] Revenue sources synced (Stripe, invoicing platforms)
- [ ] Expense tool integrations verified (Brex, Ramp, Expensify)
- [ ] Bookkeeping categorization queue drained before close

## Error Handling & Resilience

- [ ] Circuit breaker configured for Fondo API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Bank sync failure detection within 24 hours
- [ ] Intercompany transaction reconciliation validated
- [ ] R&D qualifying activity documentation verified programmatically
- [ ] Filing deadline alerts set 30/14/7 days before due dates

## Monitoring & Alerting

- [ ] API latency tracked per sync endpoint
- [ ] Error rate alerts set (any financial sync failure = immediate)
- [ ] Monthly close completion tracked (all 12 months before year-end)
- [ ] R&D credit calculation validated against employee tags
- [ ] Extension filing status monitored (Form 7004 before March 15)

## Validation Script

```typescript
async function checkFondoReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.fondo.com/v1/status', {
      headers: { Authorization: `Bearer ${process.env.FONDO_API_KEY}` },
    });
    checks.push({ name: 'Fondo API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Fondo API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.FONDO_API_KEY, detail: process.env.FONDO_API_KEY ? 'Present' : 'MISSING' });
  // Bank sync status
  try {
    const res = await fetch('https://api.fondo.com/v1/integrations/status', {
      headers: { Authorization: `Bearer ${process.env.FONDO_API_KEY}` },
    });
    const data = await res.json();
    const active = data?.integrations?.filter((i: any) => i.status === 'active').length || 0;
    checks.push({ name: 'Active Integrations', pass: active >= 2, detail: `${active} connected` });
  } catch (e: any) { checks.push({ name: 'Active Integrations', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkFondoReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| Filing deadline alerts | Missed IRS deadlines, penalties | P1 |
| Bank sync monitoring | Unreconciled transactions at year-end | P1 |
| R&D credit validation | Incorrect credit claim, audit risk | P2 |
| Payroll data sync | Missing W-2/1099 data for returns | P2 |
| Monthly close tracking | Year-end books incomplete for board | P3 |

## Resources

- [Fondo TaxPass](https://fondo.com/taxpass)
- [IRS Form 1120](https://www.irs.gov/forms-pubs/about-form-1120)

## Next Steps

See `fondo-security-basics` for financial data protection and compliance controls.
