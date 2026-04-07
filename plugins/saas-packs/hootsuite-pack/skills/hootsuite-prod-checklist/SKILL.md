---
name: hootsuite-prod-checklist
description: |
  Execute Hootsuite production deployment checklist and rollback procedures.
  Use when deploying Hootsuite integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "hootsuite production", "deploy hootsuite",
  "hootsuite go-live", "hootsuite launch checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Production Checklist

## Overview

Hootsuite manages social media publishing, scheduling, and analytics across multiple platforms (Twitter/X, LinkedIn, Facebook, Instagram). A production integration automates post scheduling, monitors engagement, and syncs analytics. Failures mean posts go out at wrong times, media uploads get rejected, or social profile disconnections go undetected, creating gaps in your publishing calendar.

## Authentication & Secrets

- [ ] `HOOTSUITE_API_KEY` and OAuth client secret in secrets manager
- [ ] OAuth app reviewed and approved in Hootsuite developer portal
- [ ] Token refresh logic tested with deliberately expired tokens
- [ ] Separate OAuth app for production vs development
- [ ] Key rotation schedule documented (before annual app review)

## API Integration

- [ ] Production base URL configured (`https://platform.hootsuite.com/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] Message scheduling tested with all connected social profiles
- [ ] Media upload validated (images, video, carousel per platform)
- [ ] Character limits enforced per platform (X: 280, LinkedIn: 3000, FB: 63K)
- [ ] Timezone handling verified for scheduled posts across regions
- [ ] Social profile health check detects disconnected accounts

## Error Handling & Resilience

- [ ] Circuit breaker configured for Hootsuite API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] REJECTED media states handled with user notification
- [ ] Social profile disconnection detected and alerted within 1 hour
- [ ] Scheduled post failure queued for retry (not silently dropped)
- [ ] Content moderation filter on automated posts (banned words, compliance)

## Monitoring & Alerting

- [ ] API latency tracked per endpoint (publish, schedule, analytics)
- [ ] Error rate alerts set (threshold: >3% over 10 minutes)
- [ ] Token refresh failures trigger immediate notification
- [ ] Failed post scheduling reported with platform and error detail
- [ ] Engagement analytics sync monitored for completeness

## Validation Script

```typescript
async function checkHootsuiteReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://platform.hootsuite.com/v1/me', {
      headers: { Authorization: `Bearer ${process.env.HOOTSUITE_API_KEY}` },
    });
    checks.push({ name: 'Hootsuite API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Hootsuite API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.HOOTSUITE_API_KEY, detail: process.env.HOOTSUITE_API_KEY ? 'Present' : 'MISSING' });
  // Social profiles connected
  try {
    const res = await fetch('https://platform.hootsuite.com/v1/socialProfiles', {
      headers: { Authorization: `Bearer ${process.env.HOOTSUITE_API_KEY}` },
    });
    const data = await res.json();
    const count = data?.data?.length || 0;
    checks.push({ name: 'Social Profiles', pass: count > 0, detail: `${count} profiles connected` });
  } catch (e: any) { checks.push({ name: 'Social Profiles', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkHootsuiteReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| Token refresh logic | All scheduled posts fail silently | P1 |
| Profile disconnection | Publishing gap on key platforms | P1 |
| Media rejection handling | Broken posts with missing images | P2 |
| Timezone validation | Posts published at wrong local time | P2 |
| Content moderation | Brand-damaging automated content | P3 |

## Resources

- [Hootsuite Developer Portal](https://developer.hootsuite.com)
- [Hootsuite API Overview](https://developer.hootsuite.com/docs/api-overview)

## Next Steps

See `hootsuite-security-basics` for social account protection and access control.
