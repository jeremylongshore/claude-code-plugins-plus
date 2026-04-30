---
name: linktree-core-workflow-a
description: 'Execute Linktree primary workflow: Profile & Links Management.

  Trigger: "linktree profile & links management", "primary linktree workflow".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree — Profile & Links Management

## Overview

Manages the complete lifecycle of a Linktree profile and its links through the
Linktree REST API. This skill covers retrieving profile metadata, creating new
links with positioning and thumbnails, updating existing link properties, listing
all links for a profile, and reordering links by position. Use this workflow when
building integrations that programmatically manage a creator's or brand's
link-in-bio page — for example, syncing product launches, rotating seasonal
promotions, or bulk-importing links from a spreadsheet. All operations use bearer
token authentication against the Linktree API.

## Prerequisites

- **Linktree Developer Account** — register at [linktr.ee/marketplace/developer](https://linktr.ee/marketplace/developer)
- **API Key** — set `LINKTREE_API_KEY` in your environment
- **Node.js >= 18** and **TypeScript >= 5.0**
- **Linktree SDK** — install with `npm install @linktree/sdk`

## Instructions

### Step 1: Get Profile

```typescript
try {
  const profile = await client.profiles.get('myprofile');
  console.log(`Bio: ${profile.bio}`);
  console.log(`Links: ${profile.links.length}`);
} catch (err: any) {
  if (err.status === 404) throw new Error('Profile not found — verify the username');
  throw err;
}
```

### Step 2: Create a Link

```typescript
try {
  const link = await client.links.create({
    profile_id: profile.id,
    title: 'My Website',
    url: 'https://example.com',
    position: 0,  // Top of list
    thumbnail: 'https://example.com/icon.png'
  });
  console.log(`Created link: ${link.id}`);
} catch (err: any) {
  if (err.status === 422) throw new Error(`Validation failed: ${err.message}`);
  if (err.status === 429) console.warn('Rate limited — retry after backoff');
  throw err;
}
```

### Step 3: Update Link

```typescript
try {
  await client.links.update(link.id, {
    title: 'Updated Title',
    archived: false
  });
} catch (err: any) {
  if (err.status === 404) throw new Error(`Link ${link.id} not found — it may have been deleted`);
  throw err;
}
```

### Step 4: List All Links

```typescript
try {
  const links = await client.links.list({ profile_id: profile.id });
  links.forEach(l => console.log(`${l.position}: ${l.title} → ${l.url}`));
} catch (err: any) {
  if (err.status === 401) throw new Error('Invalid API key — check LINKTREE_API_KEY');
  throw err;
}
```

## Error Handling

| Error | Status | Cause | Resolution |
|-------|--------|-------|------------|
| `Unauthorized` | 401 | Missing or expired `LINKTREE_API_KEY` | Regenerate key in developer dashboard |
| `Not Found` | 404 | Invalid profile username or deleted link ID | Verify the resource exists before operating |
| `Validation Error` | 422 | Malformed URL, missing required field, or duplicate position | Check request body against API schema |
| `Rate Limited` | 429 | Too many requests in window | Implement exponential backoff (start at 1s) |
| `Server Error` | 500 | Linktree API outage | Retry with backoff; check [status.linktr.ee](https://status.linktr.ee) |

## Output

A successful workflow produces a fully configured Linktree profile with an ordered
set of active links. Each link includes an `id`, `title`, `url`, `position` (zero-indexed),
`thumbnail` URL, and `archived` status. The profile object contains the username, bio,
avatar URL, and a `links` array reflecting the current ordering. Use the returned link
IDs for subsequent update or delete operations in downstream workflows.

## Resources

- [Linktree API Reference](https://linktr.ee/marketplace/developer)
- [Linktree API Status Page](https://status.linktr.ee)
- [Linktree Developer Blog](https://linktr.ee/blog/developers)

## Next Steps

See `linktree-core-workflow-b`.
