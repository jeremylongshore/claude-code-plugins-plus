---
name: mindtickle-prod-checklist
description: |
  Prod Checklist for MindTickle.
  Trigger: "mindtickle prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Production Checklist

## Overview
MindTickle powers sales readiness at scale, managing user provisioning via SCIM, course progress tracking across thousands of reps, and quiz completion data that feeds pipeline forecasting. A production integration must enforce multi-tenant isolation through company-specific headers, handle SCIM provisioning race conditions during bulk onboarding, and ensure quiz score integrity under concurrent submissions. Misconfigurations here can leak training data across tenants, corrupt completion records, or silently drop user provisioning events during org restructures.

## Prerequisites
- Production MindTickle API key and SCIM bearer token (not sandbox credentials)
- Secrets manager configured (Vault, AWS Secrets Manager, or GCP Secret Manager)
- Monitoring stack operational (Datadog, Grafana, or CloudWatch)
- Company ID confirmed for multi-tenant header (`X-Company-Id`)
- SCIM endpoint URL registered in your identity provider (Okta, Azure AD)

## Authentication & Secrets
- [ ] API keys stored in vault/secrets manager (never in code or config files)
- [ ] Key rotation schedule configured (every 90 days)
- [ ] SCIM bearer token stored separately from general API keys
- [ ] `X-Company-Id` header injected server-side (never exposed to client)
- [ ] Service account permissions restricted to required modules only (courses, users, analytics)

## API Integration
- [ ] Base URL points to `https://api.mindtickle.com/v2` (production, not sandbox)
- [ ] `X-Company-Id` header included on every request for tenant isolation
- [ ] Rate limiting enforced client-side (respect `X-RateLimit-*` response headers)
- [ ] Pagination implemented for user and course listing (offset-based with `limit` and `offset`)
- [ ] SCIM provisioning endpoint handles bulk operations (batch user create/update)
- [ ] Request timeout set to 10 seconds for reads, 60 seconds for bulk SCIM operations
- [ ] Course progress sync uses incremental timestamps (not full resync each run)

## Error Handling & Resilience
- [ ] Circuit breaker configured for MindTickle API calls (open after 5 consecutive failures)
- [ ] Retry logic with exponential backoff for 429 (rate limit) and 5xx responses
- [ ] SCIM conflict resolution: 409 on duplicate user triggers update-or-skip logic
- [ ] Quiz submission failures queued for retry (never silently dropped)
- [ ] Bulk provisioning errors isolated per-user (one failure does not abort the batch)
- [ ] Stale company ID detection: 403 triggers re-verification of tenant configuration
- [ ] Course progress writes are idempotent (safe to replay on retry)

## Monitoring & Alerting
- [ ] API latency tracked (p50, p95, p99) with 1s p95 threshold
- [ ] Error rate alerts configured (threshold: >1% over 5-minute window)
- [ ] SCIM provisioning success rate monitored (alert if <99% over 1 hour)
- [ ] Quiz completion event delivery lag tracked (alert if >5 min behind real-time)
- [ ] User count drift between IdP and MindTickle detected daily (reconciliation job)
- [ ] Course enrollment failures logged with user ID and course ID for manual review

## Security
- [ ] Multi-tenant isolation verified: requests scoped by `X-Company-Id` at API gateway level
- [ ] SCIM webhook signatures validated before processing provisioning events
- [ ] PII fields (email, name, manager) encrypted in transit and at rest in local cache
- [ ] Quiz score data access restricted by role (managers see team only, not cross-org)
- [ ] Audit log enabled for all SCIM create/update/deactivate operations
- [ ] Data retention policy enforced: purge local user data within 30 days of deprovisioning

## Validation Script
```typescript
async function validateMindTickleProduction(apiKey: string, companyId: string): Promise<void> {
  const base = 'https://api.mindtickle.com/v2';
  const headers = {
    Authorization: `Bearer ${apiKey}`,
    'X-Company-Id': companyId,
    'Content-Type': 'application/json',
  };

  // 1. Connectivity check
  const ping = await fetch(`${base}/health`, { headers, signal: AbortSignal.timeout(5000) });
  console.assert(ping.ok, `API unreachable: ${ping.status}`);

  // 2. Auth and tenant validation
  const users = await fetch(`${base}/users?limit=1`, { headers });
  console.assert(users.status !== 401, 'Invalid API key');
  console.assert(users.status !== 403, 'Company ID rejected — check tenant config');
  console.assert(users.ok, `Users endpoint failed: ${users.status}`);

  // 3. Rate limit headroom
  const remaining = parseInt(users.headers.get('X-RateLimit-Remaining') ?? '0');
  console.assert(remaining > 20, `Rate limit headroom low: ${remaining} remaining`);

  // 4. SCIM endpoint reachable
  const scimUrl = process.env.MINDTICKLE_SCIM_URL;
  if (scimUrl) {
    const scim = await fetch(`${scimUrl}/Users?count=1`, {
      headers: { Authorization: `Bearer ${process.env.MINDTICKLE_SCIM_TOKEN}` },
      signal: AbortSignal.timeout(5000),
    });
    console.assert(scim.ok, `SCIM endpoint failed: ${scim.status}`);
  }

  // 5. Course listing works
  const courses = await fetch(`${base}/courses?limit=1`, { headers });
  console.assert(courses.ok, `Courses endpoint failed: ${courses.status}`);
  console.log('All MindTickle production checks passed');
}
```

## Risk Matrix
| Check | Risk if Skipped | Priority |
|---|---|---|
| X-Company-Id tenant isolation | Cross-tenant data leak, compliance violation | Critical |
| SCIM conflict handling | Duplicate users or dropped provisioning during bulk onboard | Critical |
| Quiz submission retry queue | Lost quiz scores corrupt sales readiness metrics | Critical |
| Idempotent progress writes | Duplicate course completions inflate training KPIs | High |
| IdP-MindTickle user reconciliation | Ghost accounts retain access after offboarding | High |

## Resources
- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-security-basics`.
