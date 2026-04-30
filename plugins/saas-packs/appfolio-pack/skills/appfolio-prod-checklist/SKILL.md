---
name: appfolio-prod-checklist
description: 'Production readiness checklist for AppFolio integrations.

  Trigger: "appfolio production checklist".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Production Checklist

## Overview

AppFolio manages properties, tenants, leases, and work orders for real estate operations. A production integration handles sensitive tenant PII, financial transactions, and maintenance workflows. Failures here mean missed rent collections, unprocessed work orders, or tenant data exposure under CCPA. This checklist ensures your AppFolio API integration is resilient, compliant, and observable.

## Authentication & Secrets

- [ ] `APPFOLIO_API_KEY` stored in secrets manager (not environment files)
- [ ] Client ID and secret separated from application code
- [ ] Key rotation schedule documented (90-day recommended)
- [ ] Separate credentials for dev/staging/prod environments
- [ ] API credentials scoped to minimum required permissions

## API Integration

- [ ] Production base URL configured (`https://api.appfolio.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] Pagination implemented for property and tenant list endpoints
- [ ] Work order creation tested with all required fields
- [ ] Lease document upload validated for supported formats
- [ ] Webhook endpoints configured for tenant and payment events
- [ ] Idempotency keys used for payment and work order creation

## Error Handling & Resilience

- [ ] Circuit breaker configured for AppFolio API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Tenant PII handling verified CCPA/FCRA compliant
- [ ] Data validation on all API responses before storage
- [ ] Graceful degradation when property sync is unavailable
- [ ] Duplicate work order detection prevents re-creation on retry

## Monitoring & Alerting

- [ ] API latency tracked per endpoint (properties, tenants, work orders)
- [ ] Error rate alerts set (threshold: >3% over 5 minutes)
- [ ] Failed payment sync triggers immediate P1 alert
- [ ] Work order creation failures reported within 5 minutes
- [ ] Daily reconciliation of synced property counts vs source

## Validation Script

```typescript
async function checkAppFolioReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  const baseUrl = process.env.APPFOLIO_BASE_URL || 'https://api.appfolio.com/v1';
  // API connectivity
  try {
    const res = await fetch(`${baseUrl}/properties?limit=1`, {
      headers: { Authorization: `Bearer ${process.env.APPFOLIO_API_KEY}` },
    });
    checks.push({ name: 'API Connectivity', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'API Connectivity', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.APPFOLIO_API_KEY, detail: process.env.APPFOLIO_API_KEY ? 'Present' : 'MISSING' });
  // Work order endpoint
  try {
    const res = await fetch(`${baseUrl}/work_orders?limit=1`, {
      headers: { Authorization: `Bearer ${process.env.APPFOLIO_API_KEY}` },
    });
    checks.push({ name: 'Work Orders', pass: res.ok, detail: res.ok ? 'Accessible' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Work Orders', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkAppFolioReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Expired keys halt property sync | P1 |
| Payment sync failure | Missed rent collections | P1 |
| Tenant PII exposure | CCPA violation, legal liability | P1 |
| Work order duplication | Duplicate maintenance dispatch | P2 |
| Rate limit handling | 429 errors during bulk property import | P3 |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-security-basics` for tenant data protection and access control.
