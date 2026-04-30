---
name: fathom-prod-checklist
description: 'Production readiness checklist for Fathom API integrations.

  Trigger with phrases like "fathom production", "fathom go-live", "fathom checklist".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- meeting-intelligence
- ai-notes
- fathom
compatibility: Designed for Claude Code
---
# Fathom Production Checklist

## Overview

Fathom provides AI-powered meeting intelligence with automated transcription, summaries, and action item extraction. A production integration ingests meeting recordings, processes transcripts, and syncs action items to downstream systems. Failures mean lost meeting context, missed follow-ups, or transcript data leaking outside authorized channels. This checklist ensures reliable, compliant meeting data pipelines.

## Authentication & Secrets

- [ ] `FATHOM_API_KEY` stored in secrets manager (not environment files)
- [ ] OAuth app registered if building public-facing integration
- [ ] Key rotation schedule documented (90-day cycle)
- [ ] Separate credentials for dev/staging/prod environments
- [ ] Webhook signing secret configured for payload verification

## API Integration

- [ ] Production base URL configured (`https://api.fathom.video/v1`)
- [ ] Rate limit handling with backoff (60 req/min standard tier)
- [ ] Webhook endpoint registered and tested with sample payloads
- [ ] Meeting recording retrieval handles large file downloads
- [ ] Transcript pagination implemented for long meetings (>60 min)
- [ ] Action item extraction tested with various meeting formats
- [ ] Calendar integration sync verified (Google Calendar / Outlook)

## Error Handling & Resilience

- [ ] Circuit breaker configured for Fathom API outages
- [ ] Retry with exponential backoff for 429/5xx responses
- [ ] Empty or partial transcript handling (silent meetings, poor audio)
- [ ] Webhook delivery failures trigger re-fetch via polling
- [ ] Meeting data PII handling documented (GDPR consent, retention)
- [ ] Backup webhook URL configured for failover

## Monitoring & Alerting

- [ ] API latency tracked per endpoint (meetings, transcripts)
- [ ] Error rate alerts set (threshold: >5% over 10 minutes)
- [ ] Failed transcript processing triggers notification
- [ ] Webhook delivery success rate monitored
- [ ] Daily digest of processed meeting counts vs scheduled

## Validation Script

```typescript
async function checkFathomReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.fathom.video/v1/meetings?limit=1', {
      headers: { Authorization: `Bearer ${process.env.FATHOM_API_KEY}` },
    });
    checks.push({ name: 'Fathom API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Fathom API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.FATHOM_API_KEY, detail: process.env.FATHOM_API_KEY ? 'Present' : 'MISSING' });
  // Webhook endpoint reachable
  const webhookUrl = process.env.FATHOM_WEBHOOK_URL;
  if (webhookUrl) {
    try {
      const res = await fetch(webhookUrl, { method: 'HEAD' });
      checks.push({ name: 'Webhook Endpoint', pass: res.ok, detail: `HTTP ${res.status}` });
    } catch (e: any) { checks.push({ name: 'Webhook Endpoint', pass: false, detail: e.message }); }
  } else { checks.push({ name: 'Webhook Endpoint', pass: false, detail: 'URL not configured' }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkFathomReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Expired key halts transcript pipeline | P1 |
| Webhook verification | Spoofed payloads inject bad data | P1 |
| PII retention policy | GDPR/CCPA violation on meeting data | P1 |
| Empty transcript handling | Downstream systems crash on null | P2 |
| Rate limit backoff | Bulk meeting import blocked by 429 | P3 |

## Resources

- [Fathom API Docs](https://fathom.video/developers)
- [Fathom Status](https://status.fathom.video)

## Next Steps

See `fathom-security-basics` for meeting data privacy and consent patterns.
