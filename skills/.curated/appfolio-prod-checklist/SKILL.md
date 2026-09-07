---
name: appfolio-prod-checklist
description: 'Production readiness checklist for AppFolio integrations.

  Trigger: "appfolio production checklist".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
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

## Prerequisites

- A verified production partner contract, base URL, auth mechanism, permitted
  endpoint scopes, and named owners for business, security, operations, and
  rollback decisions.
- A completed sandbox rehearsal using synthetic data, separate managed
  credentials, a request budget, and a recorded rollback/reconciliation plan.
- Evidence for observability, PII minimization, idempotent writes, and alert
  routing—not a checklist item that merely asserts those controls exist.

## Instructions

1. Validate the actual provider-issued client configuration through the secret
   manager; do not default an endpoint or authentication scheme in release code.
2. Run the readiness checks in staging, then a controlled production-shaped
   rehearsal that performs only authorized safe reads.
3. Review every failed, skipped, or unverifiable control as a no-go; preserve
   redacted receipts for credentials, endpoints, monitoring, and recovery.
4. Release progressively only with a tested rollback and reconciliation owner;
   pause write paths if payment, work-order, tenant, or lease state is unknown.

## Authentication & Secrets

- [ ] `APPFOLIO_API_KEY` stored in secrets manager (not environment files)
- [ ] Client ID and secret separated from application code
- [ ] Key rotation schedule documented (90-day recommended)
- [ ] Separate credentials for dev/staging/prod environments
- [ ] API credentials scoped to minimum required permissions

## API Integration

- [ ] Production base URL and authentication method verified against the current partner contract
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
  const client = createVerifiedAppFolioClient(); // contract-bound client from appfolio-security-basics
  // API connectivity
  try {
    const res = await client.get('/properties?limit=1');
    checks.push({ name: 'API Connectivity', pass: res.status >= 200 && res.status < 300, detail: `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'API Connectivity', pass: false, detail: e.message }); }
  // Client construction proves the managed credential and provider contract are available.
  checks.push({ name: 'Verified client configuration', pass: true, detail: 'Loaded from managed configuration' });
  // Work order endpoint
  try {
    const res = await client.get('/work_orders?limit=1');
    checks.push({ name: 'Work Orders', pass: res.status >= 200 && res.status < 300, detail: `HTTP ${res.status}` });
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

## Output

- A redacted go/no-go receipt binding the verified client, safe-read checks,
  monitoring state, owner approvals, and rollback/reconciliation plan
- A list of failed or unproven controls that blocks release until remediated
- A bounded release decision that keeps sensitive or write-capable paths off
  until their production-shaped rehearsal has evidence

## Examples

For a work-order integration release, run the checklist first against a
synthetic staging fixture, then use the managed production-shaped client for a
single authorized safe read. Confirm the alert route, PII redaction, and
idempotency/reconciliation controls while all writes remain disabled. If a
credential, endpoint contract, readiness check, or rollback exercise cannot be
verified, declare no-go, retain the previous revision, and have the assigned
owner remediate before a new rehearsal.

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-security-basics` for tenant data protection and access control.
