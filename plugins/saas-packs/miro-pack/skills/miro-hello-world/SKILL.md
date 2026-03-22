---
name: miro-hello-world
description: |
  Create a minimal working Miro example with real board and item operations.
  Use when starting a new Miro integration, testing your setup,
  or learning the Miro REST API v2 item model.
  Trigger with phrases like "miro hello world", "miro example",
  "miro quick start", "first miro board", "create miro sticky note".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, quickstart]
compatible-with: claude-code
---

# Miro Hello World

## Overview

Minimal working example: create a board, add a sticky note, add a shape, connect them, and read the results back — all using the Miro REST API v2.

## Prerequisites

- Completed `miro-install-auth` setup
- Valid access token with `boards:read` and `boards:write` scopes
- `@mirohq/miro-api` installed

## Instructions

### Step 1: Create a Board

```typescript
import { MiroApi } from '@mirohq/miro-api';

const api = new MiroApi(process.env.MIRO_ACCESS_TOKEN!);

async function createBoard() {
  // POST https://api.miro.com/v2/boards
  const response = await api.createBoard({
    name: 'Hello World Board',
    description: 'Created via REST API v2',
    policy: {
      sharingPolicy: {
        access: 'private',          // 'private' | 'view' | 'comment' | 'edit'
        inviteToAccountAndBoardLinkAccess: 'no_access',
      },
      permissionsPolicy: {
        collaborationToolsStartAccess: 'all_editors',
        copyAccess: 'anyone',
        sharingAccess: 'owners_and_coowners',
      },
    },
  });

  const boardId = response.body.id;
  console.log(`Board created: ${boardId}`);
  console.log(`View at: https://miro.com/app/board/${boardId}/`);
  return boardId;
}
```

### Step 2: Add a Sticky Note

```typescript
async function addStickyNote(boardId: string) {
  // POST https://api.miro.com/v2/boards/{board_id}/sticky_notes
  const response = await fetch(
    `https://api.miro.com/v2/boards/${boardId}/sticky_notes`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data: {
          content: 'Hello from the API!',
          shape: 'square',          // 'square' | 'rectangle'
        },
        style: {
          fillColor: 'light_yellow', // light_yellow | light_green | light_blue | light_pink | etc.
          textAlign: 'center',       // 'left' | 'center' | 'right'
          textAlignVertical: 'middle',
        },
        position: { x: 0, y: 0 },
        geometry: { width: 200 },
      }),
    }
  );

  const note = await response.json();
  console.log(`Sticky note created: ${note.id} (type: ${note.type})`);
  return note.id;
}
```

### Step 3: Add a Shape

```typescript
async function addShape(boardId: string) {
  // POST https://api.miro.com/v2/boards/{board_id}/shapes
  const response = await fetch(
    `https://api.miro.com/v2/boards/${boardId}/shapes`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data: {
          content: 'Next Step',
          shape: 'round_rectangle',  // rectangle | circle | triangle | rhombus | round_rectangle | etc.
        },
        style: {
          fillColor: '#4262ff',
          fontFamily: 'arial',
          fontSize: 14,
          textAlign: 'center',
          borderColor: '#1a1a2e',
          borderWidth: 2,
          borderStyle: 'normal',     // 'normal' | 'dashed' | 'dotted'
        },
        position: { x: 400, y: 0 },
        geometry: { width: 200, height: 100 },
      }),
    }
  );

  const shape = await response.json();
  console.log(`Shape created: ${shape.id} (type: ${shape.type})`);
  return shape.id;
}
```

### Step 4: Connect Items with a Connector

```typescript
async function connectItems(boardId: string, startId: string, endId: string) {
  // POST https://api.miro.com/v2/boards/{board_id}/connectors
  const response = await fetch(
    `https://api.miro.com/v2/boards/${boardId}/connectors`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        startItem: { id: startId },
        endItem: { id: endId },
        captions: [{ content: 'leads to' }],
        style: {
          strokeColor: '#1a1a2e',
          strokeWidth: 2,
          startStrokeCap: 'none',
          endStrokeCap: 'stealth',   // none | stealth | arrow | filled_triangle | etc.
        },
      }),
    }
  );

  const connector = await response.json();
  console.log(`Connector created: ${connector.id}`);
  return connector.id;
}
```

### Step 5: List All Items on the Board

```typescript
async function listBoardItems(boardId: string) {
  // GET https://api.miro.com/v2/boards/{board_id}/items
  // Returns cursor-paginated results
  const response = await fetch(
    `https://api.miro.com/v2/boards/${boardId}/items?limit=50`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
      },
    }
  );

  const result = await response.json();
  console.log(`Board has ${result.data.length} items:`);
  for (const item of result.data) {
    console.log(`  - ${item.type}: ${item.id} (${item.data?.content ?? 'no content'})`);
  }

  // Handle pagination
  if (result.cursor) {
    console.log(`More items available. Next cursor: ${result.cursor}`);
  }
}
```

### Step 6: Run the Complete Flow

```typescript
async function main() {
  const boardId = await createBoard();
  const noteId = await addStickyNote(boardId);
  const shapeId = await addShape(boardId);
  await connectItems(boardId, noteId, shapeId);
  await listBoardItems(boardId);
  console.log('\nDone! Open the board in Miro to see your items.');
}

main().catch(console.error);
```

## Miro REST API v2 Item Types

| Type | Create Endpoint | Key Properties |
|------|----------------|----------------|
| `sticky_note` | `/v2/boards/{id}/sticky_notes` | content, shape, fillColor |
| `shape` | `/v2/boards/{id}/shapes` | content, shape, fillColor, borderStyle |
| `card` | `/v2/boards/{id}/cards` | title, description, dueDate, assigneeId |
| `text` | `/v2/boards/{id}/texts` | content, fontSize |
| `frame` | `/v2/boards/{id}/frames` | title, showContent, childrenIds |
| `image` | `/v2/boards/{id}/images` | url or data (base64) |
| `document` | `/v2/boards/{id}/documents` | url |
| `embed` | `/v2/boards/{id}/embeds` | url |
| `app_card` | `/v2/boards/{id}/app_cards` | title, description, fields, status |
| `connector` | `/v2/boards/{id}/connectors` | startItem, endItem, captions |

All create endpoints require `boards:write` scope. All GET endpoints require `boards:read`.

## Error Handling

| Error | HTTP Status | Cause | Solution |
|-------|-------------|-------|----------|
| `boardNotFound` | 404 | Invalid board_id | Verify board exists and token has access |
| `insufficientPermissions` | 403 | Missing `boards:write` | Add scope in app settings |
| `invalidInput` | 400 | Bad request body | Check required fields per item type |
| `rateLimitExceeded` | 429 | Too many requests | Implement backoff (see `miro-rate-limits`) |

## Resources

- [Miro REST API Reference](https://developers.miro.com/docs/rest-api-reference-guide)
- [Create Board Endpoint](https://developers.miro.com/reference/create-board)
- [Board Items Overview](https://developers.miro.com/docs/board-items)

## Next Steps

Proceed to `miro-local-dev-loop` for development workflow setup, or `miro-core-workflow-a` for board management patterns.
