---
name: figma-known-pitfalls
description: |
  Avoid the most common Figma API integration mistakes and anti-patterns.
  Use when reviewing Figma code, onboarding new developers,
  or auditing an existing Figma integration.
  Trigger with phrases like "figma mistakes", "figma anti-patterns",
  "figma pitfalls", "figma code review", "figma what not to do".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Known Pitfalls

## Overview
The ten most common mistakes when integrating with the Figma REST API and Plugin API, with correct alternatives for each.

## Prerequisites
- Working Figma integration to audit
- Access to codebase

## Instructions

### Pitfall 1: Fetching Full File Trees

**Problem:** `GET /v1/files/:key` without `depth` returns the entire document tree. Large files can be 10-100 MB of JSON.

```typescript
// BAD -- downloads entire file tree
const file = await figmaFetch(`/v1/files/${fileKey}`);

// GOOD -- only get metadata and page names
const file = await figmaFetch(`/v1/files/${fileKey}?depth=1`);

// GOOD -- fetch only the nodes you need
const nodes = await figmaFetch(`/v1/files/${fileKey}/nodes?ids=${ids}`);
```

### Pitfall 2: Ignoring Rate Limit Headers

**Problem:** Blasting requests and crashing on 429 without reading `Retry-After`.

```typescript
// BAD -- no rate limit handling
for (const id of nodeIds) {
  await figmaFetch(`/v1/files/${fileKey}/nodes?ids=${id}`); // 429!
}

// GOOD -- batch IDs and honor Retry-After
const ids = nodeIds.join(',');
const res = await fetch(`https://api.figma.com/v1/files/${fileKey}/nodes?ids=${ids}`, {
  headers: { 'X-Figma-Token': token },
});
if (res.status === 429) {
  const wait = parseInt(res.headers.get('Retry-After') || '60');
  await new Promise(r => setTimeout(r, wait * 1000));
}
```

### Pitfall 3: Caching Image Export URLs Too Long

**Problem:** Figma image URLs expire after 30 days. Storing them permanently breaks.

```typescript
// BAD -- storing image URLs in database permanently
await db.save({ iconUrl: imageUrl }); // Will break in 30 days

// GOOD -- re-export when needed, or cache with short TTL
const imageCache = new LRUCache({ max: 1000, ttl: 24 * 60 * 60 * 1000 }); // 24h
```

### Pitfall 4: Hardcoded PATs

**Problem:** Personal access tokens committed to source code.

```typescript
// BAD -- token in source code (visible forever in git history)
const token = 'figd_actual_token_value_here';

// GOOD -- environment variable
const token = process.env.FIGMA_PAT!;
if (!token) throw new Error('FIGMA_PAT not set');
```

### Pitfall 5: Using Deprecated `files:read` Scope

**Problem:** The `files:read` scope is deprecated. New tokens should use granular scopes.

```
BAD:  files:read (deprecated, will be removed)
GOOD: file_content:read, file_comments:read, file_versions:read (specific)
```

### Pitfall 6: Forgetting Color Format Conversion

**Problem:** Figma returns colors as 0-1 floats, not 0-255 integers.

```typescript
// BAD -- using Figma values directly as RGB
const { r, g, b } = node.fills[0].color;
return `rgb(${r}, ${g}, ${b})`; // rgb(0.8, 0.2, 0.4) -- invalid!

// GOOD -- convert to 0-255 range
return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
```

### Pitfall 7: Not Handling null Image Renders

**Problem:** The images endpoint returns `null` for nodes that cannot be rendered (invisible, deleted, empty).

```typescript
// BAD -- assumes all nodes render successfully
const images = data.images;
for (const [id, url] of Object.entries(images)) {
  const img = await fetch(url); // TypeError: Cannot construct URL from null
}

// GOOD -- filter out null entries
for (const [id, url] of Object.entries(images)) {
  if (!url) {
    console.warn(`Node ${id} could not be rendered (null)`);
    continue;
  }
  const img = await fetch(url);
}
```

### Pitfall 8: Polling Instead of Webhooks

**Problem:** Polling `GET /v1/files/:key` every 30 seconds wastes rate limit quota.

```typescript
// BAD -- 2,880 API calls per file per day
setInterval(async () => {
  const file = await figmaFetch(`/v1/files/${fileKey}`);
  if (file.version !== lastVersion) await sync();
}, 30_000);

// GOOD -- webhook notifies you only when file changes
// POST /v2/webhooks with event_type: "FILE_UPDATE"
// Result: ~10-50 calls/day instead of 2,880
```

### Pitfall 9: SVG Export with Scale Parameter

**Problem:** Figma ignores the `scale` parameter for SVG exports. SVGs always export at 1x.

```typescript
// BAD -- scale has no effect on SVG
await figmaFetch(`/v1/images/${key}?ids=${id}&format=svg&scale=2`);

// GOOD -- SVG is vector; scale is meaningless. Use scale for PNG/JPG only.
await figmaFetch(`/v1/images/${key}?ids=${id}&format=svg`);      // SVG: always 1x
await figmaFetch(`/v1/images/${key}?ids=${id}&format=png&scale=2`); // PNG: 2x
```

### Pitfall 10: Webhook Without Passcode Verification

**Problem:** Anyone can POST to your webhook endpoint if you don't verify the passcode.

```typescript
// BAD -- trusts any incoming request
app.post('/webhooks/figma', (req, res) => {
  processEvent(req.body); // Attacker can send fake events
  res.sendStatus(200);
});

// GOOD -- verify passcode with timing-safe comparison
app.post('/webhooks/figma', (req, res) => {
  const received = req.body.passcode || '';
  const expected = process.env.FIGMA_WEBHOOK_PASSCODE!;

  if (received.length !== expected.length ||
      !crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  res.status(200).json({ received: true });
  processEvent(req.body);
});
```

## Quick Reference

| # | Pitfall | Detection | Fix |
|---|---------|-----------|-----|
| 1 | Full file fetch | Response > 1MB | Use `depth=1` or `/nodes` |
| 2 | No rate limit handling | 429 errors | Read `Retry-After`, batch requests |
| 3 | Stale image URLs | Broken images after 30 days | Re-export or short TTL cache |
| 4 | Hardcoded PAT | `grep -r figd_` in source | Use `process.env.FIGMA_PAT` |
| 5 | Deprecated scope | `files:read` in token config | Use `file_content:read` |
| 6 | Wrong color format | Colors look wrong | Multiply by 255 |
| 7 | Null image render | TypeError on null URL | Filter null entries |
| 8 | Polling loop | High API call volume | Use Webhooks V2 |
| 9 | SVG with scale | Scale parameter ignored | SVG is always 1x |
| 10 | No webhook verification | Security vulnerability | Verify passcode |

## Resources
- [Figma REST API](https://developers.figma.com/docs/rest-api/)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [Figma API Scopes](https://developers.figma.com/docs/rest-api/scopes/)
- [Figma Webhooks V2](https://developers.figma.com/docs/rest-api/webhooks/)
