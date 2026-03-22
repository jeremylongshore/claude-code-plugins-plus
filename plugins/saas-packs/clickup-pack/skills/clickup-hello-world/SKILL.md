---
name: clickup-hello-world
description: |
  Make your first ClickUp API v2 calls: list workspaces, spaces, and create a task.
  Use when starting a new ClickUp integration, testing your setup,
  or learning the ClickUp hierarchy (Workspace > Space > Folder > List > Task).
  Trigger: "clickup hello world", "clickup first call", "clickup quick start",
  "test clickup API", "create clickup task".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Hello World

## Overview

Walk through the ClickUp hierarchy and make your first API calls. ClickUp's data model: **Workspace** (called "team" in API v2) > **Space** > **Folder** (optional) > **List** > **Task**.

## Prerequisites

- Completed `clickup-install-auth` setup
- Valid `CLICKUP_API_TOKEN` in environment

## ClickUp Hierarchy

```
Workspace (team_id)        GET /api/v2/team
  └── Space (space_id)     GET /api/v2/team/{team_id}/space
       ├── List            GET /api/v2/space/{space_id}/list  (folderless lists)
       └── Folder          GET /api/v2/space/{space_id}/folder
            └── List       GET /api/v2/folder/{folder_id}/list
                 └── Task  GET /api/v2/list/{list_id}/task
```

## Step 1: Discover Your Workspace

```bash
# Get authorized workspaces (returns team_id needed for all subsequent calls)
curl -s https://api.clickup.com/api/v2/team \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.teams[] | {id, name}'
```

Response shape:
```json
{
  "teams": [{
    "id": "1234567",
    "name": "My Workspace",
    "color": "#536cfe",
    "members": [{ "user": { "id": 123, "username": "john", "email": "john@example.com" } }]
  }]
}
```

## Step 2: List Spaces

```bash
TEAM_ID="1234567"
curl -s "https://api.clickup.com/api/v2/team/${TEAM_ID}/space?archived=false" \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.spaces[] | {id, name}'
```

## Step 3: Get Lists in a Space

```bash
SPACE_ID="12345678"
# Folderless lists (directly in Space)
curl -s "https://api.clickup.com/api/v2/space/${SPACE_ID}/list" \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.lists[] | {id, name}'

# Or lists inside folders
curl -s "https://api.clickup.com/api/v2/space/${SPACE_ID}/folder" \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.folders[] | {id, name, lists: [.lists[] | {id, name}]}'
```

## Step 4: Create Your First Task

```bash
LIST_ID="900100200300"
curl -s -X POST "https://api.clickup.com/api/v2/list/${LIST_ID}/task" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hello from the ClickUp API!",
    "description": "Created via API v2",
    "priority": 3,
    "status": "to do"
  }' | jq '{id, name, url}'
```

```typescript
// TypeScript equivalent
async function createFirstTask(listId: string) {
  const task = await clickupRequest(`/list/${listId}/task`, {
    method: 'POST',
    body: JSON.stringify({
      name: 'Hello from the ClickUp API!',
      description: 'Created via API v2',
      priority: 3,         // 1=Urgent, 2=High, 3=Normal, 4=Low
      status: 'to do',
      assignees: [123456], // user IDs (optional)
      due_date: Date.now() + 86400000, // tomorrow (Unix ms)
      due_date_time: true,
    }),
  });

  console.log(`Task created: ${task.name} (${task.id})`);
  console.log(`URL: ${task.url}`);
  return task;
}
```

## Create Task Response Shape

```json
{
  "id": "abc123",
  "custom_id": null,
  "name": "Hello from the ClickUp API!",
  "status": { "status": "to do", "color": "#d3d3d3", "type": "open" },
  "priority": { "id": "3", "priority": "normal", "color": "#6fddff" },
  "date_created": "1695000000000",
  "date_updated": "1695000000000",
  "due_date": "1695086400000",
  "url": "https://app.clickup.com/t/abc123",
  "list": { "id": "900100200300", "name": "My List" },
  "folder": { "id": "456", "name": "My Folder" },
  "space": { "id": "12345678" }
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Missing/invalid token | Check `CLICKUP_API_TOKEN` |
| 404 Not Found | Invalid list_id/team_id | Verify IDs via GET /team |
| 400 Bad Request | Missing `name` field | Task name is required |
| 429 Rate Limited | Too many requests | Wait for `X-RateLimit-Reset` |

## Resources

- [ClickUp Create Task Reference](https://developer.clickup.com/reference/createtask)
- [ClickUp Get Tasks Reference](https://developer.clickup.com/reference/gettasks)
- [ClickUp API Hierarchy](https://developer.clickup.com/docs/general-v2-v3-api)

## Next Steps

Proceed to `clickup-core-workflow-a` for workspace/space/task management patterns.
