---
name: grammarly-prod-checklist
description: |
  Production readiness checklist for Grammarly API integrations. Use when preparing
  a Grammarly integration for production deployment.
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Production Checklist

## Overview

Grammarly provides AI-powered writing assistance with grammar checking, tone detection, plagiarism scanning, and style suggestions. A production integration processes user-submitted text through Grammarly's API and returns actionable suggestions. Failures mean unchecked content goes live, suggestion latency degrades UX, or sensitive text leaks outside approved processing boundaries.

## Authentication & Secrets

- [ ] `GRAMMARLY_API_KEY` stored in secrets manager (not config files)
- [ ] Client credentials (ID + secret) separated from application code
- [ ] Token refresh logic handles expiry before API calls fail
- [ ] Separate credentials for dev/staging/prod environments
- [ ] Key rotation schedule documented (90-day cycle)

## API Integration

- [ ] Production base URL configured (`https://api.grammarly.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] Text chunking implemented for documents > 100K characters
- [ ] Minimum 30-word validation before sending to API
- [ ] Suggestion categories configured per use case (grammar, tone, clarity)
- [ ] AI detection endpoint integrated if content authenticity required
- [ ] Plagiarism check timeout handling (longer processing for large docs)

## Error Handling & Resilience

- [ ] Circuit breaker configured for Grammarly API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Writing score thresholds defined per content type
- [ ] Graceful degradation when API is unavailable (queue, not block)
- [ ] Error responses logged with request IDs for support escalation
- [ ] Partial suggestion results handled (incomplete analysis on timeout)

## Monitoring & Alerting

- [ ] API latency tracked per request type (check, detect, plagiarism)
- [ ] Error rate alerts set (threshold: >5% over 5 minutes)
- [ ] Token refresh failures trigger immediate notification
- [ ] Suggestion acceptance rate tracked for quality feedback loop
- [ ] Daily API usage against plan limits monitored

## Validation Script

```typescript
async function checkGrammarlyReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.grammarly.com/v1/check', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.GRAMMARLY_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'This is a production readiness test sentence for validation.' }),
    });
    checks.push({ name: 'Grammarly API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Grammarly API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.GRAMMARLY_API_KEY, detail: process.env.GRAMMARLY_API_KEY ? 'Present' : 'MISSING' });
  // Rate limit headroom
  try {
    const res = await fetch('https://api.grammarly.com/v1/usage', {
      headers: { Authorization: `Bearer ${process.env.GRAMMARLY_API_KEY}` },
    });
    checks.push({ name: 'Usage Endpoint', pass: res.ok, detail: res.ok ? 'Accessible' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Usage Endpoint', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkGrammarlyReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| Token refresh logic | Silent auth failure blocks all checks | P1 |
| Text chunking | Large documents rejected or truncated | P1 |
| Rate limit handling | Burst traffic triggers 429 cascade | P2 |
| Plagiarism timeout | Stuck requests block content pipeline | P2 |
| Usage monitoring | Surprise plan overage charges | P3 |

## Resources

- [Grammarly Developer API](https://developer.grammarly.com/)
- [Grammarly Status](https://status.grammarly.com)

## Next Steps

See `grammarly-security-basics` for text data handling and privacy controls.
