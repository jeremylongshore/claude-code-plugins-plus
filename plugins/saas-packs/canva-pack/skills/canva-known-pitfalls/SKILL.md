---
name: canva-known-pitfalls
description: |
  Identify and avoid Canva Connect API anti-patterns and common integration mistakes.
  Use when reviewing Canva code, onboarding developers,
  or auditing existing Canva integrations for best practices violations.
  Trigger with phrases like "canva mistakes", "canva anti-patterns",
  "canva pitfalls", "canva what not to do", "canva code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Known Pitfalls

## Overview

Common mistakes when integrating with the Canva Connect API. Each pitfall includes the anti-pattern, why it fails, and the correct approach with real API endpoints.

## Pitfall #1: Not Handling Token Expiry

```typescript
// WRONG — token expires after ~4 hours, then all calls fail
const token = await getTokenOnce();
// ... 5 hours later ...
await canvaAPI('/designs', token); // 401 Unauthorized

// RIGHT — auto-refresh before expiry
class CanvaClient {
  async request(path: string, init?: RequestInit) {
    if (Date.now() > this.tokens.expiresAt - 300_000) {
      await this.refreshToken(); // Refresh 5 min before expiry
    }
    // ... make request
  }
}
```

## Pitfall #2: Reusing Refresh Tokens

```typescript
// WRONG — refresh tokens are single-use in Canva's OAuth
const tokens = await refreshAccessToken(storedRefreshToken);
// Later, using the SAME refresh token again:
const tokens2 = await refreshAccessToken(storedRefreshToken); // FAILS

// RIGHT — always store the new refresh token immediately
const tokens = await refreshAccessToken(storedRefreshToken);
await db.saveTokens(userId, {
  accessToken: tokens.access_token,
  refreshToken: tokens.refresh_token, // NEW token — store it!
  expiresAt: Date.now() + tokens.expires_in * 1000,
});
```

## Pitfall #3: Synchronous Export Polling in Request Handler

```typescript
// WRONG — user waits 5-30 seconds while export completes
app.post('/api/export', async (req, res) => {
  const { job } = await canvaAPI('/exports', token, { method: 'POST', body: ... });
  while (job.status === 'in_progress') { // Blocks entire request
    await sleep(2000);
    // ... poll ...
  }
  res.json({ urls: job.urls }); // User waited 15+ seconds
});

// RIGHT — return job ID, poll asynchronously
app.post('/api/export', async (req, res) => {
  const { job } = await canvaAPI('/exports', token, { method: 'POST', body: ... });
  res.json({ jobId: job.id, status: 'processing' }); // 200ms response
});

app.get('/api/export/:jobId/status', async (req, res) => {
  const { job } = await canvaAPI(`/exports/${req.params.jobId}`, token);
  res.json({ status: job.status, urls: job.urls });
});
```

## Pitfall #4: Ignoring Rate Limits

```typescript
// WRONG — blast requests, crash on 429
for (const design of designs) {
  await canvaAPI(`/exports`, token, { method: 'POST', body: ... }); // 75/5min limit
}

// RIGHT — queue with rate awareness
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 1, interval: 4000, intervalCap: 1 });

for (const design of designs) {
  await queue.add(() =>
    canvaAPI(`/exports`, token, { method: 'POST', body: ... })
  );
}
```

## Pitfall #5: Caching Temporary URLs

```typescript
// WRONG — URLs expire silently
const design = await canvaAPI(`/designs/${id}`, token);
cache.set(id, design, { ttl: 86400 }); // Cache for 24 hours
// But thumbnail URLs expire in 15 minutes!

// RIGHT — cache metadata but refresh URLs
const design = await canvaAPI(`/designs/${id}`, token);
cache.set(`design:meta:${id}`, {
  id: design.design.id,
  title: design.design.title,
  pageCount: design.design.page_count,
  // DON'T cache: thumbnail.url (15 min), edit_url (30 days), view_url (30 days)
}, { ttl: 300 }); // 5 min cache
```

## Pitfall #6: Client-Side OAuth

```typescript
// WRONG — client secret exposed in browser
// frontend.js
const tokens = await fetch('https://api.canva.com/rest/v1/oauth/token', {
  body: new URLSearchParams({
    client_secret: 'EXPOSED_TO_USERS', // Anyone can see this
    // ...
  }),
});

// RIGHT — token exchange MUST happen server-side
// Canva docs: "Requests that require authenticating with your client ID
// and client secret can't be made from a web-browser client"
```

## Pitfall #7: Not Checking Enterprise Requirements

```typescript
// WRONG — calling autofill without Enterprise, getting 403
const result = await canvaAPI('/autofills', token, { method: 'POST', body: ... });
// 403: "User must be a member of a Canva Enterprise organization"

// RIGHT — check capabilities first
const capabilities = await canvaAPI('/users/me/capabilities', token);
if (!capabilities.capabilities?.includes('autofill')) {
  throw new Error('Autofill requires Canva Enterprise subscription');
}
```

## Pitfall #8: Not Validating Webhook Signatures

```typescript
// WRONG — accepts any POST as a valid webhook
app.post('/webhooks/canva', (req, res) => {
  processEvent(req.body); // Attacker can send fake events!
  res.status(200).send();
});

// RIGHT — verify JWK signature
app.post('/webhooks/canva', express.text({ type: '*/*' }), async (req, res) => {
  const payload = await verifyCanvaWebhook(req.body); // JWK verification
  if (!payload) return res.status(401).send('Invalid');
  res.status(200).send('OK'); // Return 200 first
  processEvent(payload).catch(console.error); // Process async
});
```

## Pitfall #9: Ignoring Blank Design Auto-Delete

```typescript
// WRONG — create designs and expect them to persist
const { design } = await canvaAPI('/designs', token, {
  method: 'POST',
  body: JSON.stringify({ design_type: { type: 'custom', width: 1080, height: 1080 } }),
});
// Design auto-deleted after 7 days if user never edits it!

// RIGHT — warn users or track unedited designs
await notifyUser(`Edit your design before ${sevenDaysFromNow}: ${design.urls.edit_url}`);
```

## Pitfall #10: Not Handling Export Failures

```typescript
// WRONG — assumes exports always succeed
const { job } = await canvaAPI('/exports', token, { method: 'POST', body: ... });
const urls = (await pollExport(job.id)).urls; // Crashes if failed

// RIGHT — handle all export error codes
const result = await pollExport(job.id);
if (result.status === 'failed') {
  switch (result.error?.code) {
    case 'license_required':
      throw new Error('Design uses premium elements — user needs Canva Pro');
    case 'approval_required':
      throw new Error('Design requires approval before export');
    case 'internal_failure':
      // Retry after delay
      break;
  }
}
```

## Quick Reference

| Pitfall | Detection | Prevention |
|---------|-----------|------------|
| Token expiry | 401 errors after 4h | Auto-refresh before expiry |
| Reused refresh token | Token exchange fails | Store new token every refresh |
| Sync export polling | Slow API responses | Return job ID, poll separately |
| Rate limit ignored | 429 errors | Queue with p-queue |
| Cached expired URLs | Broken images/links | Don't cache temp URLs |
| Client-side OAuth | Security audit | Server-side only |
| Missing Enterprise check | 403 on autofill | Check capabilities first |
| Unsigned webhooks | Security audit | JWK verification |
| Blank design deleted | Design disappears | Warn about 7-day window |
| Export error ignored | Crashes | Handle all error codes |

## Resources

- [Canva Authentication](https://www.canva.dev/docs/connect/authentication/)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Canva Scopes](https://www.canva.dev/docs/connect/appendix/scopes/)
