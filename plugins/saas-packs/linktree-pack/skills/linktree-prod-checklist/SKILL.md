---
name: linktree-prod-checklist
description: 'Prod Checklist for Linktree.

  Trigger: "linktree prod checklist".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree Production Checklist

## Overview
Linktree profiles serve as the single gateway between a creator's social audience and their monetized destinations. A misconfigured integration can silently drop link-click analytics, leak API keys through client-side calls, or trip the 100 req/min rate limit during viral traffic spikes. This checklist hardens your Linktree API integration for production-grade reliability, ensuring click tracking stays accurate, webhook delivery remains verified, and your link-in-bio pages load under high concurrency.

## Prerequisites
- Production Linktree API key (not sandbox/dev key)
- Secrets manager configured (Vault, AWS Secrets Manager, or GCP Secret Manager)
- Monitoring stack operational (Datadog, Grafana, or CloudWatch)
- Staging environment validated with synthetic traffic test

## Authentication & Secrets
- [ ] API keys stored in vault/secrets manager (never in code or environment files)
- [ ] Key rotation schedule configured (every 90 days)
- [ ] Separate keys for staging vs production environments
- [ ] Bearer token included in Authorization header, not query params
- [ ] API key scopes restricted to minimum required permissions (read-only where possible)

## API Integration
- [ ] Base URL points to `https://api.linktr.ee/v1` (production, not sandbox)
- [ ] Rate limiting enforced client-side at 90 req/min (buffer below 100 req/min hard limit)
- [ ] Pagination implemented for profile link listing (cursor-based, not offset)
- [ ] Request timeout set to 10 seconds for profile reads, 30 seconds for analytics queries
- [ ] `Content-Type: application/json` and `Accept` headers set on every request
- [ ] Link click tracking webhook endpoint registered and reachable from Linktree servers
- [ ] Bulk link updates batched to avoid rate limit bursts during campaign launches

## Error Handling & Resilience
- [ ] Circuit breaker configured for Linktree API calls (open after 5 consecutive failures)
- [ ] Retry logic with exponential backoff for 429 (rate limit) and 5xx responses
- [ ] 429 responses parse `Retry-After` header to schedule next attempt
- [ ] Graceful degradation serves cached profile data when API is unreachable
- [ ] Link click events queued locally during outages and replayed on recovery
- [ ] Timeout errors distinguished from authentication errors in alerting

## Monitoring & Alerting
- [ ] API latency tracked (p50, p95, p99) with 500ms p95 threshold
- [ ] Error rate alerts configured (threshold: >1% over 5-minute window)
- [ ] Rate limit headroom monitored (alert when usage exceeds 80 req/min sustained)
- [ ] Click tracking event delivery lag measured (alert if >60s behind real-time)
- [ ] Profile cache hit ratio tracked (target: >90% for high-traffic creators)
- [ ] Webhook delivery failures logged with payload for manual replay

## Security
- [ ] Webhook signatures verified using HMAC-SHA256 with shared secret
- [ ] CORS restricted to known frontend domains (no wildcard origins)
- [ ] API responses sanitized before rendering user-generated link titles/descriptions
- [ ] Click analytics data access restricted by creator account scope
- [ ] No PII logged in plain text (creator emails, visitor IPs masked)

## Validation Script
```typescript
async function validateLinktreeProduction(apiKey: string): Promise<void> {
  const base = 'https://api.linktr.ee/v1';
  const headers = { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' };

  // 1. Connectivity check
  const ping = await fetch(`${base}/health`, { headers, signal: AbortSignal.timeout(5000) });
  console.assert(ping.ok, `API unreachable: ${ping.status}`);

  // 2. Auth validation
  const profile = await fetch(`${base}/me`, { headers });
  console.assert(profile.status !== 401, 'Invalid API key');
  console.assert(profile.status !== 403, 'Insufficient key permissions');

  // 3. Rate limit headroom
  const remaining = parseInt(profile.headers.get('X-RateLimit-Remaining') ?? '0');
  console.assert(remaining > 20, `Rate limit headroom low: ${remaining} remaining`);

  // 4. Webhook endpoint reachable
  const webhookUrl = process.env.LINKTREE_WEBHOOK_URL;
  if (webhookUrl) {
    const wh = await fetch(webhookUrl, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
    console.assert(wh.ok, `Webhook endpoint unreachable: ${wh.status}`);
  }

  // 5. Click tracking active
  const links = await fetch(`${base}/links`, { headers });
  console.assert(links.ok, `Links endpoint failed: ${links.status}`);
  console.log('All Linktree production checks passed');
}
```

## Risk Matrix
| Check | Risk if Skipped | Priority |
|---|---|---|
| HMAC webhook verification | Spoofed click events corrupt analytics | Critical |
| Rate limit client-side cap | 429 storm during viral spikes, data loss | Critical |
| Bearer token in vault | Key leak via repo/logs, full account takeover | Critical |
| Cached profile fallback | Blank link-in-bio page during outage | High |
| Click event replay queue | Permanent analytics gaps after transient failures | High |

## Resources
- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-security-basics`.
