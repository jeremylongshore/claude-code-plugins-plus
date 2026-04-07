---
name: juicebox-prod-checklist
description: |
  Execute Juicebox production checklist.
  Trigger: "juicebox production", "deploy juicebox".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Production Checklist

## Overview

Juicebox provides AI-powered people search and analysis, enabling dataset creation, candidate discovery, and structured analysis across professional profiles. A production integration queries datasets, retrieves analysis results, and powers talent intelligence workflows. Failures mean missed candidates, stale analysis data, or quota exhaustion that blocks time-sensitive searches.

## Authentication & Secrets

- [ ] `JUICEBOX_API_KEY` stored in secrets manager (not config files)
- [ ] API key scoped to production workspace only
- [ ] Key rotation schedule documented (90-day cycle)
- [ ] Separate credentials for dev/staging/prod environments
- [ ] Candidate data access restricted to authorized roles

## API Integration

- [ ] Production base URL configured (`https://api.juicebox.ai/v1`)
- [ ] Rate limiting configured per plan tier
- [ ] Dataset creation and query endpoints tested end-to-end
- [ ] Analysis result pagination implemented for large datasets
- [ ] Search query optimization validated (precision vs recall tradeoffs)
- [ ] Bulk analysis requests batched to avoid rate limits
- [ ] Result caching configured for repeated queries

## Error Handling & Resilience

- [ ] Circuit breaker configured for Juicebox API outages
- [ ] Retry with exponential backoff for 429/5xx responses
- [ ] Candidate data encrypted at rest in downstream storage
- [ ] GDPR/CCPA retention policy enforced on stored profiles
- [ ] Empty result sets handled gracefully (no silent failures)
- [ ] Quota exhaustion detected before critical searches fail

## Monitoring & Alerting

- [ ] API latency tracked per endpoint (search, analysis, datasets)
- [ ] Error rate alerts set (threshold: >5% over 5 minutes)
- [ ] Quota usage monitored with alert at 80% consumption
- [ ] Analysis completion rate tracked for reliability metrics
- [ ] Daily digest of search volumes and result quality

## Validation Script

```typescript
async function checkJuiceboxReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.juicebox.ai/v1/search', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.JUICEBOX_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'test', limit: 1 }),
    });
    checks.push({ name: 'Juicebox API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Juicebox API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.JUICEBOX_API_KEY, detail: process.env.JUICEBOX_API_KEY ? 'Present' : 'MISSING' });
  // Quota check
  try {
    const res = await fetch('https://api.juicebox.ai/v1/usage', {
      headers: { Authorization: `Bearer ${process.env.JUICEBOX_API_KEY}` },
    });
    const data = await res.json();
    const pct = data?.usagePercent || 0;
    checks.push({ name: 'Quota Headroom', pass: pct < 80, detail: `${pct}% used` });
  } catch (e: any) { checks.push({ name: 'Quota Headroom', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkJuiceboxReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Expired key blocks all searches | P1 |
| GDPR/CCPA retention | Regulatory violation on candidate data | P1 |
| Quota monitoring | Exhaustion blocks time-sensitive searches | P2 |
| Rate limit handling | Bulk analysis requests rejected | P2 |
| Data encryption at rest | Candidate PII exposure risk | P3 |

## Resources

- [Juicebox Platform](https://juicebox.ai)
- [Juicebox Status](https://status.juicebox.ai)

## Next Steps

See `juicebox-security-basics` for candidate data protection and compliance.
