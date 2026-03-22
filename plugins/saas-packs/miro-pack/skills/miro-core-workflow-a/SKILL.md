---
name: miro-core-workflow-a
description: |
  Manage Miro boards and items — create, read, update, delete boards,
  sticky notes, shapes, cards, frames, and tags via REST API v2.
  Trigger with phrases like "miro board management", "create miro board",
  "miro items CRUD", "miro sticky notes", "organize miro board".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, boards, items]
compatible-with: claude-code
---

# Miro Core Workflow A — Boards & Items CRUD

## Overview

The primary workflow for Miro integrations: full CRUD on boards and board items (sticky notes, shapes, cards, frames, tags) using the REST API v2 at `https://api.miro.com/v2/`.

## Prerequisites

- Valid access token with `boards:read` and `boards:write` scopes
- Understanding of Miro item types (see `miro-hello-world`)

## Board Operations

### Create a Board

```typescript
// POST https://api.miro.com/v2/boards
const board = await miroFetch('/v2/boards', 'POST', {
  name: 'Sprint Retro — Week 12',
  description: 'Team retrospective board',
  teamId: 'your-team-id',  // optional — creates in specific team
  policy: {
    sharingPolicy: {
      access: 'private',
      inviteToAccountAndBoardLinkAccess: 'no_access',
      organizationAccess: 'private',
    },
    permissionsPolicy: {
      collaborationToolsStartAccess: 'all_editors',
      copyAccess: 'anyone',
      sharingAccess: 'team_members_and_collaborators',
    },
  },
});
```

### Get a Board

```typescript
// GET https://api.miro.com/v2/boards/{board_id}
const board = await miroFetch(`/v2/boards/${boardId}`);
// Returns: id, name, description, owner, policy, createdAt, modifiedAt
```

### List All Boards

```typescript
// GET https://api.miro.com/v2/boards
// Supports filtering by team_id, project_id, query, sort, owner
const boards = await miroFetch('/v2/boards?limit=50&sort=last_modified');
for (const board of boards.data) {
  console.log(`${board.id}: ${board.name} (modified: ${board.modifiedAt})`);
}
```

### Update a Board

```typescript
// PATCH https://api.miro.com/v2/boards/{board_id}
await miroFetch(`/v2/boards/${boardId}`, 'PATCH', {
  name: 'Sprint Retro — Week 12 (CLOSED)',
  description: 'Archived — action items in Jira',
});
```

### Delete a Board

```typescript
// DELETE https://api.miro.com/v2/boards/{board_id}
await miroFetch(`/v2/boards/${boardId}`, 'DELETE');
```

## Item CRUD Operations

### Create Items

```typescript
// Sticky Note — POST /v2/boards/{board_id}/sticky_notes
const note = await miroFetch(`/v2/boards/${boardId}/sticky_notes`, 'POST', {
  data: { content: 'Went well: team communication', shape: 'square' },
  style: { fillColor: 'light_green', textAlign: 'center' },
  position: { x: -200, y: 0 },
  geometry: { width: 199 },
});

// Shape — POST /v2/boards/{board_id}/shapes
const shape = await miroFetch(`/v2/boards/${boardId}/shapes`, 'POST', {
  data: { content: 'Decision Point', shape: 'rhombus' },
  style: { fillColor: '#ff6b6b', borderColor: '#333333', borderWidth: 2 },
  position: { x: 0, y: 200 },
  geometry: { width: 200, height: 200 },
});

// Card — POST /v2/boards/{board_id}/cards
const card = await miroFetch(`/v2/boards/${boardId}/cards`, 'POST', {
  data: {
    title: 'Improve deploy pipeline',
    description: 'Reduce deploy time from 15min to 5min',
    dueDate: '2025-04-01T00:00:00Z',
    assigneeId: 'user-id-123',
  },
  style: { cardTheme: '#2d9bf0' },
  position: { x: 200, y: 0 },
});

// Frame — POST /v2/boards/{board_id}/frames
const frame = await miroFetch(`/v2/boards/${boardId}/frames`, 'POST', {
  data: {
    title: 'What went well',
    format: 'custom',   // 'custom' | 'a4' | 'letter' | etc.
    type: 'freeform',   // 'freeform' | 'heap_map' | etc.
    showContent: true,
  },
  position: { x: -400, y: -200 },
  geometry: { width: 600, height: 400 },
});

// Text — POST /v2/boards/{board_id}/texts
const text = await miroFetch(`/v2/boards/${boardId}/texts`, 'POST', {
  data: { content: '<strong>Action Items</strong>' },
  style: { fontSize: 24, textAlign: 'left' },
  position: { x: 0, y: -300 },
  geometry: { width: 300 },
});
```

### Get a Specific Item

```typescript
// GET https://api.miro.com/v2/boards/{board_id}/items/{item_id}
const item = await miroFetch(`/v2/boards/${boardId}/items/${itemId}`);
// Or type-specific:
// GET /v2/boards/{board_id}/sticky_notes/{item_id}
```

### Update an Item

```typescript
// PATCH https://api.miro.com/v2/boards/{board_id}/sticky_notes/{item_id}
await miroFetch(`/v2/boards/${boardId}/sticky_notes/${noteId}`, 'PATCH', {
  data: { content: 'Updated: team communication was excellent' },
  style: { fillColor: 'light_blue' },
});
```

### Delete an Item

```typescript
// DELETE https://api.miro.com/v2/boards/{board_id}/items/{item_id}
await miroFetch(`/v2/boards/${boardId}/items/${itemId}`, 'DELETE');
```

## Tags

Tags can be attached to sticky notes and cards (up to 8 per item).

```typescript
// Step 1: Create a tag — POST /v2/boards/{board_id}/tags
const tag = await miroFetch(`/v2/boards/${boardId}/tags`, 'POST', {
  title: 'Action Item',
  fillColor: 'red',  // red | light_green | cyan | yellow | magenta | green | blue | etc.
});

// Step 2: Attach tag to an item — POST /v2/boards/{board_id}/items/{item_id}/tags
await miroFetch(`/v2/boards/${boardId}/items/${noteId}/tags`, 'POST', {
  tagId: tag.id,
});

// NOTE: Tag changes via API do NOT appear on the board in realtime.
// Users must refresh the board to see tag updates made via REST API.
```

## Board Members

```typescript
// List members — GET /v2/boards/{board_id}/members
const members = await miroFetch(`/v2/boards/${boardId}/members?limit=50`);

// Share board with a user — POST /v2/boards/{board_id}/members
await miroFetch(`/v2/boards/${boardId}/members`, 'POST', {
  emails: ['colleague@company.com'],
  role: 'commenter',  // 'viewer' | 'commenter' | 'editor' | 'coowner'
  message: 'Check out our retro board!',
});
```

## Helper: Fetch Wrapper

```typescript
async function miroFetch(path: string, method = 'GET', body?: unknown) {
  const response = await fetch(`https://api.miro.com${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`Miro ${method} ${path}: ${response.status} ${error.message ?? ''}`);
  }

  if (response.status === 204) return null; // DELETE returns no body
  return response.json();
}
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `boardNotFound` | 404 | Board deleted or wrong ID | Verify board ID |
| `invalidInput` | 400 | Missing required field | Check request body per item type |
| `insufficientPermissions` | 403 | Missing `boards:write` scope | Re-authorize with correct scopes |
| `itemNotFound` | 404 | Item ID wrong or deleted | Re-fetch board items |
| `duplicateTagTitle` | 409 | Tag name already exists on board | Reuse existing tag ID |

## Resources

- [Create Board](https://developers.miro.com/reference/create-board)
- [Get Items on Board](https://developers.miro.com/reference/get-items)
- [Create Sticky Notes and Tags](https://developers.miro.com/docs/working-with-sticky-notes-and-tags-with-the-rest-api)
- [REST API Reference Guide](https://developers.miro.com/docs/rest-api-reference-guide)

## Next Steps

For connectors and visual relationships, see `miro-core-workflow-b`.
