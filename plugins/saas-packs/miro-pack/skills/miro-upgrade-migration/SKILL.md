---
name: miro-upgrade-migration
description: |
  Migrate Miro integrations from REST API v1 to v2 and upgrade @mirohq/miro-api SDK.
  Use when upgrading SDK versions, migrating v1 widget endpoints to v2 item endpoints,
  or handling breaking changes in the Miro platform.
  Trigger with phrases like "upgrade miro", "miro migration",
  "miro v1 to v2", "update miro SDK", "miro breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, migration, upgrade]
compatible-with: claude-code
---

# Miro Upgrade & Migration

## Overview

Guide for migrating from Miro REST API v1 to v2, upgrading the `@mirohq/miro-api` SDK, and handling the key breaking changes between versions.

## Key Breaking Changes: v1 to v2

### Terminology Changes

| v1 Term | v2 Term | Notes |
|---------|---------|-------|
| Widget | Item | All board elements renamed |
| Line | Connector | Lines renamed, gained captions and snapTo |
| Sticker | Sticky Note | Type value: `sticky_note` |
| Widget API (polymorphic) | Per-type endpoints | No more universal create endpoint |
| `text` property | `content` property | In data objects |
| `shapeType` | `shape` (in `data`) | Moved from style to data object |
| `startWidget` / `endWidget` | `startItem` / `endItem` | Connector endpoints |
| Board User Connection | Board Member | Sharing/permissions model |

### Endpoint Migration Map

```
# v1 (DEPRECATED)                          → v2 (CURRENT)
POST /v1/boards/{id}/widgets               → POST /v2/boards/{id}/sticky_notes
                                              POST /v2/boards/{id}/shapes
                                              POST /v2/boards/{id}/cards
                                              POST /v2/boards/{id}/texts
                                              POST /v2/boards/{id}/frames
                                              POST /v2/boards/{id}/images
                                              POST /v2/boards/{id}/documents
                                              POST /v2/boards/{id}/embeds
                                              POST /v2/boards/{id}/app_cards

GET  /v1/boards/{id}/widgets               → GET  /v2/boards/{id}/items
GET  /v1/boards/{id}/widgets/{widget_id}   → GET  /v2/boards/{id}/items/{item_id}
                                              (or type-specific: /v2/boards/{id}/sticky_notes/{item_id})

POST /v1/boards/{id}/widgets (type: line)  → POST /v2/boards/{id}/connectors
GET  /v1/boards/{id}/widgets?type=line     → GET  /v2/boards/{id}/connectors
```

### Request Body Changes

```typescript
// v1: Create a sticky note (via universal widgets endpoint)
// POST /v1/boards/{id}/widgets
{
  "type": "sticker",
  "text": "Hello World",
  "style": {
    "stickerBackgroundColor": "#FFFF00"
  },
  "x": 100,
  "y": 200,
  "width": 200
}

// v2: Create a sticky note (dedicated endpoint)
// POST /v2/boards/{id}/sticky_notes
{
  "data": {
    "content": "Hello World",      // "text" → "content"
    "shape": "square"              // Required in v2
  },
  "style": {
    "fillColor": "light_yellow"    // Named colors or hex
  },
  "position": {
    "x": 100,                      // Nested under "position"
    "y": 200
  },
  "geometry": {
    "width": 200                   // Nested under "geometry"
  }
}
```

```typescript
// v1: Connector (line)
{
  "type": "line",
  "startWidget": { "id": "123" },
  "endWidget": { "id": "456" }
}

// v2: Connector
{
  "startItem": { "id": "123", "snapTo": "right" },    // Gains snapTo/position
  "endItem": { "id": "456", "snapTo": "left" },
  "captions": [{ "content": "connects to" }],          // New: captions
  "shape": "curved",                                     // New: shape control
  "style": {
    "startStrokeCap": "none",
    "endStrokeCap": "stealth"
  }
}
```

## SDK Upgrade Steps

### Step 1: Check Current Version and Update

```bash
# Check current version
npm list @mirohq/miro-api

# View available versions
npm view @mirohq/miro-api versions --json | tail -5

# Create upgrade branch
git checkout -b upgrade/miro-api-v2

# Install latest
npm install @mirohq/miro-api@latest
```

### Step 2: Update Import Patterns

```typescript
// OLD: Some early SDK versions
import { MiroClient } from '@miro/sdk';

// CURRENT: Official @mirohq/miro-api
import { Miro, MiroApi } from '@mirohq/miro-api';

// High-level (OAuth-aware, stateful)
const miro = new Miro({ clientId, clientSecret, redirectUrl });
const userApi = await miro.as(userId);

// Low-level (stateless, pass token)
const api = new MiroApi(accessToken);
```

### Step 3: Migrate Widget Calls to Item Calls

```typescript
// BEFORE: Generic widget create
const widget = await client.createWidget(boardId, {
  type: 'sticker',
  text: 'Note content',
});

// AFTER: Type-specific item create
const stickyNote = await fetch(
  `https://api.miro.com/v2/boards/${boardId}/sticky_notes`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: { content: 'Note content', shape: 'square' },
      style: { fillColor: 'light_yellow' },
      position: { x: 0, y: 0 },
    }),
  }
);
```

### Step 4: Update Response Handling

```typescript
// v1 response: flat structure
// { id, type, text, x, y, width, style: { stickerBackgroundColor } }

// v2 response: nested structure
// {
//   id, type: 'sticky_note',
//   data: { content, shape },
//   style: { fillColor, textAlign },
//   position: { x, y, origin },
//   geometry: { width },
//   createdAt, modifiedAt, createdBy
// }

// Adapter for gradual migration
function adaptV2ToV1Shape(v2Item: any): any {
  return {
    id: v2Item.id,
    type: v2Item.type === 'sticky_note' ? 'sticker' : v2Item.type,
    text: v2Item.data?.content,
    x: v2Item.position?.x,
    y: v2Item.position?.y,
    width: v2Item.geometry?.width,
  };
}
```

### Step 5: Verify and Test

```bash
# Run tests
npm test

# Verify against a test board
MIRO_TEST_BOARD_ID=your-test-board npm run test:integration

# Check for any remaining v1 patterns
grep -r "widgets\|sticker\|startWidget\|endWidget\|shapeType" src/ --include="*.ts"
```

## v2 Response Pagination Change

```typescript
// v1: offset-based pagination
// GET /v1/boards/{id}/widgets?offset=100&limit=50

// v2: cursor-based pagination
// GET /v2/boards/{id}/items?limit=50&cursor=eyJ0...

async function getAllItemsV2(boardId: string): Promise<any[]> {
  const items: any[] = [];
  let cursor: string | undefined;

  do {
    const url = new URL(`https://api.miro.com/v2/boards/${boardId}/items`);
    url.searchParams.set('limit', '50');
    if (cursor) url.searchParams.set('cursor', cursor);

    const response = await fetch(url.toString(), {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const result = await response.json();
    items.push(...result.data);
    cursor = result.cursor;
  } while (cursor);

  return items;
}
```

## Error Handling

| Issue | Detection | Solution |
|-------|-----------|----------|
| `Cannot find module '@miro/sdk'` | Import error | Update to `@mirohq/miro-api` |
| `widgets is not a function` | SDK API change | Use per-type endpoints |
| `text` field undefined | v2 response shape | Access via `data.content` |
| Connector fails | v1 line syntax | Update to `startItem`/`endItem` |
| Position wrong | Flat vs nested | Wrap in `position: { x, y }` |

## Resources

- [REST API Comparison Guide (v1 vs v2)](https://developers.miro.com/docs/rest-api-comparison-guide)
- [Migrate from v1 to v2](https://developers.miro.com/v1.0/docs/introduction-to-rest-api)
- [REST API Reference Guide](https://developers.miro.com/docs/rest-api-reference-guide)
- [@mirohq/miro-api Changelog](https://www.npmjs.com/package/@mirohq/miro-api?activeTab=versions)

## Next Steps

For CI integration during upgrades, see `miro-ci-integration`.
