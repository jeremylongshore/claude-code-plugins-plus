---
name: miro-core-workflow-b
description: |
  Manage Miro connectors, images, embeds, app cards, and document items via REST API v2.
  Use for visual workflows, embedding content, and building rich board layouts.
  Trigger with phrases like "miro connectors", "miro embed",
  "miro app card", "miro image upload", "connect miro items".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, connectors, embeds, app-cards]
compatible-with: claude-code
---

# Miro Core Workflow B — Connectors, Embeds & Rich Items

## Overview

Advanced item operations: connectors between items, image uploads, embedded content, app cards for custom integrations, and document items — all via the Miro REST API v2.

## Prerequisites

- Completed `miro-core-workflow-a` (boards and basic items)
- Access token with `boards:read` and `boards:write` scopes

## Connectors

Connectors are lines that visually link two items on a board. They replaced "lines" from the v1 API.

### Create a Connector

```typescript
// POST https://api.miro.com/v2/boards/{board_id}/connectors
const connector = await miroFetch(`/v2/boards/${boardId}/connectors`, 'POST', {
  startItem: {
    id: startItemId,
    position: {
      x: 1.0,   // 0.0–1.0 relative position on item boundary
      y: 0.5,   // 0.0 = top/left, 1.0 = bottom/right
    },
    // or use snapTo: 'right' | 'left' | 'top' | 'bottom' | 'auto'
  },
  endItem: {
    id: endItemId,
    snapTo: 'left',
  },
  captions: [
    {
      content: 'depends on',
      position: 0.5,             // 0.0–1.0 along the connector line
      textAlignVertical: 'top',  // 'top' | 'middle' | 'bottom'
    },
  ],
  shape: 'curved',               // 'straight' | 'elbowed' | 'curved'
  style: {
    color: '#1a1a2e',
    fontSize: 12,
    strokeColor: '#1a1a2e',
    strokeWidth: 2,
    strokeStyle: 'normal',       // 'normal' | 'dashed' | 'dotted'
    startStrokeCap: 'none',      // 'none' | 'stealth' | 'diamond' | 'filled_diamond' | etc.
    endStrokeCap: 'stealth',     // arrow-style endpoint
  },
});

console.log(`Connector ${connector.id}: ${startItemId} → ${endItemId}`);
```

### List All Connectors on a Board

```typescript
// GET https://api.miro.com/v2/boards/{board_id}/connectors
const connectors = await miroFetch(`/v2/boards/${boardId}/connectors?limit=50`);
for (const c of connectors.data) {
  console.log(`${c.startItem.id} --[${c.captions?.[0]?.content ?? ''}]--> ${c.endItem.id}`);
}
```

### Update a Connector

```typescript
// PATCH https://api.miro.com/v2/boards/{board_id}/connectors/{connector_id}
await miroFetch(`/v2/boards/${boardId}/connectors/${connectorId}`, 'PATCH', {
  captions: [{ content: 'blocks', position: 0.5 }],
  style: { strokeColor: '#ff0000', endStrokeCap: 'filled_triangle' },
});
```

### Delete a Connector

```typescript
// DELETE https://api.miro.com/v2/boards/{board_id}/connectors/{connector_id}
await miroFetch(`/v2/boards/${boardId}/connectors/${connectorId}`, 'DELETE');
```

## Images

### Upload Image from URL

```typescript
// POST https://api.miro.com/v2/boards/{board_id}/images
const image = await miroFetch(`/v2/boards/${boardId}/images`, 'POST', {
  data: {
    url: 'https://example.com/architecture-diagram.png',
    title: 'System Architecture',
  },
  position: { x: 500, y: 0 },
  geometry: { width: 400 },   // height auto-calculated from aspect ratio
});
```

### Upload Image from Base64 Data URL

```typescript
import fs from 'fs';

// Read file and convert to data URL
const imageBuffer = fs.readFileSync('diagram.png');
const base64 = imageBuffer.toString('base64');
const dataUrl = `data:image/png;base64,${base64}`;

const image = await miroFetch(`/v2/boards/${boardId}/images`, 'POST', {
  data: { url: dataUrl, title: 'Local Diagram' },
  position: { x: 0, y: 400 },
});
```

## Embed Items

Embed external content (URLs rendered as previews).

```typescript
// POST https://api.miro.com/v2/boards/{board_id}/embeds
const embed = await miroFetch(`/v2/boards/${boardId}/embeds`, 'POST', {
  data: {
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    mode: 'inline',    // 'inline' | 'modal'
    previewUrl: '',     // optional custom preview image
  },
  position: { x: -400, y: 400 },
  geometry: { width: 480, height: 270 },
});
```

## App Cards

App cards display custom data from your integration, with structured fields and status indicators.

```typescript
// POST https://api.miro.com/v2/boards/{board_id}/app_cards
const appCard = await miroFetch(`/v2/boards/${boardId}/app_cards`, 'POST', {
  data: {
    title: 'JIRA-1234: Fix login bug',
    description: 'Users unable to log in after password reset',
    status: 'connected',     // 'disconnected' | 'connected' | 'disabled'
    fields: [
      { value: 'High', iconUrl: '', fillColor: '#ff0000', iconShape: 'round', tooltip: 'Priority' },
      { value: 'In Progress', fillColor: '#ffd700', iconShape: 'square', tooltip: 'Status' },
      { value: 'John Doe', tooltip: 'Assignee' },
    ],
  },
  style: { cardTheme: '#2d9bf0' },
  position: { x: 600, y: 200 },
});
```

### Update App Card Status

```typescript
// PATCH https://api.miro.com/v2/boards/{board_id}/app_cards/{item_id}
await miroFetch(`/v2/boards/${boardId}/app_cards/${appCardId}`, 'PATCH', {
  data: {
    status: 'connected',
    fields: [
      { value: 'Done', fillColor: '#00c853', tooltip: 'Status' },
    ],
  },
});
```

## Document Items

```typescript
// POST https://api.miro.com/v2/boards/{board_id}/documents
const doc = await miroFetch(`/v2/boards/${boardId}/documents`, 'POST', {
  data: {
    url: 'https://example.com/spec.pdf',
    title: 'Technical Specification v2',
  },
  position: { x: -600, y: 0 },
});
```

## Building a Visual Workflow

Complete example: Kanban-style board with frames, cards, and connectors.

```typescript
async function buildKanbanBoard(boardId: string) {
  // Create column frames
  const todoFrame = await miroFetch(`/v2/boards/${boardId}/frames`, 'POST', {
    data: { title: 'To Do', format: 'custom' },
    position: { x: 0, y: 0 },
    geometry: { width: 400, height: 800 },
  });

  const doingFrame = await miroFetch(`/v2/boards/${boardId}/frames`, 'POST', {
    data: { title: 'In Progress', format: 'custom' },
    position: { x: 500, y: 0 },
    geometry: { width: 400, height: 800 },
  });

  const doneFrame = await miroFetch(`/v2/boards/${boardId}/frames`, 'POST', {
    data: { title: 'Done', format: 'custom' },
    position: { x: 1000, y: 0 },
    geometry: { width: 400, height: 800 },
  });

  // Add cards inside frames
  const card1 = await miroFetch(`/v2/boards/${boardId}/cards`, 'POST', {
    data: { title: 'Design API schema', description: 'OpenAPI 3.1 spec' },
    position: { x: 0, y: -200 },    // Inside todo frame
    parent: { id: todoFrame.id },
  });

  const card2 = await miroFetch(`/v2/boards/${boardId}/cards`, 'POST', {
    data: { title: 'Implement auth', description: 'OAuth 2.0 flow' },
    position: { x: 500, y: -200 },
    parent: { id: doingFrame.id },
  });

  // Connect cards to show dependency
  await miroFetch(`/v2/boards/${boardId}/connectors`, 'POST', {
    startItem: { id: card1.id, snapTo: 'right' },
    endItem: { id: card2.id, snapTo: 'left' },
    captions: [{ content: 'blocks' }],
    style: { endStrokeCap: 'stealth', strokeStyle: 'dashed' },
  });
}
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `connectorStartItemNotFound` | 404 | Start item deleted | Verify both items exist |
| `connectorEndItemNotFound` | 404 | End item deleted | Verify both items exist |
| `invalidImageUrl` | 400 | URL inaccessible | Check URL is publicly reachable |
| `imageTooLarge` | 400 | File exceeds size limit | Resize image before upload |
| `embedUrlNotSupported` | 400 | URL cannot be embedded | Check Miro's supported embed providers |

## Resources

- [Work with Connectors](https://developers.miro.com/docs/work-with-connectors)
- [Create Connector](https://developers.miro.com/reference/create-connector)
- [App Card Use Cases](https://developers.miro.com/docs/app-card-use-cases)
- [Create Image from Data URL](https://developers.miro.com/docs/create-an-image-from-a-data-url-source)

## Next Steps

For common errors and troubleshooting, see `miro-common-errors`.
