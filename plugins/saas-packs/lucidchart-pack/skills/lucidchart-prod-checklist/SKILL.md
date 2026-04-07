---
name: lucidchart-prod-checklist
description: |
  Prod Checklist for Lucidchart.
  Trigger: "lucidchart prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Production Checklist

## Overview
Lucidchart integrations interact with collaborative diagrams that may be actively edited by multiple users simultaneously. A production deployment must handle OAuth2 token lifecycle management, respect document-level collaboration locks, and account for export throttling on large diagrams. Failing to version API headers correctly causes silent schema drift, while unbounded export requests can exhaust memory on complex documents. This checklist ensures your Lucidchart integration is resilient to these collaboration and export edge cases.

## Prerequisites
- OAuth2 client credentials registered in Lucid developer portal (production app)
- Secrets manager configured (Vault, AWS Secrets Manager, or GCP Secret Manager)
- Monitoring stack operational (Datadog, Grafana, or CloudWatch)
- Test workspace with sample diagrams covering all export formats (PNG, PDF, SVG)

## Authentication & Secrets
- [ ] OAuth2 client ID and secret stored in vault/secrets manager (never in code)
- [ ] Token rotation implemented with refresh token flow (access tokens expire in 60 min)
- [ ] Refresh tokens stored encrypted at rest, separate from client credentials
- [ ] Token refresh logic handles concurrent requests (mutex/lock to prevent duplicate refreshes)
- [ ] Scopes restricted to minimum required (`lucidchart.document.read`, `lucidchart.document.export`)

## API Integration
- [ ] Base URL points to `https://api.lucid.co/v1` (production endpoint)
- [ ] `Lucid-Api-Version` header set explicitly on every request (pin to tested version)
- [ ] Rate limiting enforced client-side with token bucket (respect `X-RateLimit-*` headers)
- [ ] Pagination implemented for document listing (cursor-based with `pageToken`)
- [ ] Export requests set `Accept` header matching desired format (image/png, application/pdf)
- [ ] Large document exports use async polling pattern (POST export, poll status, GET result)
- [ ] Request timeout set to 15 seconds for reads, 120 seconds for diagram exports

## Error Handling & Resilience
- [ ] Circuit breaker configured for Lucidchart API calls (open after 5 consecutive failures)
- [ ] Retry logic with exponential backoff for 429 (rate limit) and 5xx responses
- [ ] 409 Conflict responses handled for concurrent document edits (retry with latest version)
- [ ] OAuth2 401 responses trigger automatic token refresh before retry (once per request)
- [ ] Export timeout errors fall back to lower-resolution export or cached version
- [ ] Document collaboration lock detection: skip or queue writes when another user holds the lock
- [ ] Out-of-memory protection: cap export resolution for diagrams exceeding 500 objects

## Monitoring & Alerting
- [ ] API latency tracked (p50, p95, p99) with 2s p95 threshold for exports
- [ ] Error rate alerts configured (threshold: >1% over 5-minute window)
- [ ] OAuth2 token refresh failure rate monitored (alert on any failure)
- [ ] Export queue depth tracked (alert if >50 pending exports)
- [ ] API version deprecation warnings logged from response headers
- [ ] Collaboration lock contention rate measured per workspace

## Security
- [ ] OAuth2 redirect URI restricted to exact production callback URL (no wildcards)
- [ ] PKCE enforced for authorization code flow
- [ ] Exported diagram files scanned for embedded sensitive data before downstream storage
- [ ] API responses validated against expected schema before processing
- [ ] Access tokens never logged or included in error reports

## Validation Script
```typescript
async function validateLucidchartProduction(accessToken: string): Promise<void> {
  const base = 'https://api.lucid.co/v1';
  const headers = {
    Authorization: `Bearer ${accessToken}`,
    'Lucid-Api-Version': '2024-10-01',
    'Content-Type': 'application/json',
  };

  // 1. Connectivity and auth check
  const me = await fetch(`${base}/users/me`, { headers, signal: AbortSignal.timeout(5000) });
  console.assert(me.ok, `Auth failed: ${me.status}`);

  // 2. Token expiry headroom
  const tokenData = await me.json();
  console.assert(tokenData.id, 'User profile missing — token may be scoped incorrectly');

  // 3. Rate limit headroom
  const remaining = parseInt(me.headers.get('X-RateLimit-Remaining') ?? '0');
  console.assert(remaining > 10, `Rate limit headroom low: ${remaining} remaining`);

  // 4. Document listing works
  const docs = await fetch(`${base}/documents?limit=1`, { headers });
  console.assert(docs.ok, `Document listing failed: ${docs.status}`);

  // 5. API version accepted
  const apiVersion = me.headers.get('Lucid-Api-Version');
  console.assert(apiVersion, 'API version header missing from response — check version pinning');
  console.log('All Lucidchart production checks passed');
}
```

## Risk Matrix
| Check | Risk if Skipped | Priority |
|---|---|---|
| OAuth2 token refresh mutex | Duplicate refresh calls invalidate tokens, cascading 401s | Critical |
| API version header pinning | Silent schema drift breaks document parsing | Critical |
| Collaboration lock detection | Overwrites concurrent user edits, data corruption | Critical |
| Export async polling | Timeout on large diagrams, missing deliverables | High |
| Export memory cap | OOM crash on complex diagrams (500+ objects) | High |

## Resources
- [Lucid Developer Reference](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-security-basics`.
