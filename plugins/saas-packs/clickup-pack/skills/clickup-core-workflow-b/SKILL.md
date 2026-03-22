---
name: clickup-core-workflow-b
description: |
  Manage ClickUp workspaces, spaces, folders, lists, and views via API v2.
  Use when creating project structures, organizing spaces and lists,
  or managing the ClickUp hierarchy programmatically.
  Trigger: "clickup space", "clickup folder", "clickup list", "clickup views",
  "create clickup space", "organize clickup workspace", "clickup hierarchy".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Core Workflow B — Spaces, Folders, Lists & Views

## Overview

Manage the ClickUp organizational hierarchy: Workspace > Space > Folder > List. Also covers views (list, board, calendar, gantt) and tags.

## Space Operations

```
POST   /api/v2/team/{team_id}/space          Create Space
GET    /api/v2/team/{team_id}/space           Get Spaces
GET    /api/v2/space/{space_id}               Get Space
PUT    /api/v2/space/{space_id}               Update Space
DELETE /api/v2/space/{space_id}               Delete Space
```

```typescript
// Create a Space with ClickApps enabled
async function createSpace(teamId: string, name: string) {
  return clickupRequest(`/team/${teamId}/space`, {
    method: 'POST',
    body: JSON.stringify({
      name,
      multiple_assignees: true,
      features: {
        due_dates: { enabled: true, start_date: true, remap_due_dates: true },
        time_tracking: { enabled: true },
        tags: { enabled: true },
        time_estimates: { enabled: true },
        checklists: { enabled: true },
        custom_fields: { enabled: true },
        points: { enabled: false },
      },
    }),
  });
}
```

## Folder Operations

```
POST   /api/v2/space/{space_id}/folder        Create Folder
GET    /api/v2/space/{space_id}/folder         Get Folders
GET    /api/v2/folder/{folder_id}              Get Folder
PUT    /api/v2/folder/{folder_id}              Update Folder
DELETE /api/v2/folder/{folder_id}              Delete Folder
```

```typescript
async function createFolder(spaceId: string, name: string) {
  return clickupRequest(`/space/${spaceId}/folder`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}
```

## List Operations

```
POST   /api/v2/folder/{folder_id}/list         Create List in Folder
POST   /api/v2/space/{space_id}/list            Create Folderless List
GET    /api/v2/folder/{folder_id}/list           Get Lists in Folder
GET    /api/v2/space/{space_id}/list              Get Folderless Lists
GET    /api/v2/list/{list_id}                    Get List
PUT    /api/v2/list/{list_id}                    Update List
DELETE /api/v2/list/{list_id}                    Delete List
```

```typescript
// Create list with custom statuses
async function createList(folderId: string, name: string) {
  return clickupRequest(`/folder/${folderId}/list`, {
    method: 'POST',
    body: JSON.stringify({
      name,
      content: 'List description here',
      due_date: Date.now() + 604800000, // 1 week from now
      priority: 2,
      status: 'to do',
    }),
  });
}

// Create folderless list (directly in space)
async function createFolderlessList(spaceId: string, name: string) {
  return clickupRequest(`/space/${spaceId}/list`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}
```

## View Operations

```
POST   /api/v2/list/{list_id}/view             Create List View
POST   /api/v2/folder/{folder_id}/view          Create Folder View
POST   /api/v2/team/{team_id}/view             Create Workspace View
GET    /api/v2/view/{view_id}                   Get View
GET    /api/v2/view/{view_id}/task              Get View Tasks
DELETE /api/v2/view/{view_id}                   Delete View
```

Supported view types: `list`, `board`, `calendar`, `gantt`, `table`, `timeline`, `workload`, `activity`, `map`, `chat`.

```typescript
async function createBoardView(listId: string, name: string) {
  return clickupRequest(`/list/${listId}/view`, {
    method: 'POST',
    body: JSON.stringify({
      name,
      type: 'board',
      grouping: { field: 'status', dir: 1 },
      sorting: { fields: [{ field: 'due_date', dir: 1 }] },
    }),
  });
}
```

## Tag Operations

```
GET    /api/v2/space/{space_id}/tag             Get Space Tags
POST   /api/v2/task/{task_id}/tag/{tag_name}    Add Tag to Task
DELETE /api/v2/task/{task_id}/tag/{tag_name}     Remove Tag from Task
```

## Build a Complete Project Structure

```typescript
async function scaffoldProject(teamId: string, projectName: string) {
  // 1. Create space
  const space = await createSpace(teamId, projectName);

  // 2. Create folders for phases
  const folders = await Promise.all(
    ['Planning', 'Development', 'QA', 'Deployment'].map(name =>
      createFolder(space.id, name)
    )
  );

  // 3. Create lists in each folder
  for (const folder of folders) {
    await createList(folder.id, `${folder.name} Tasks`);
  }

  // 4. Create a board view on the development folder
  const devFolder = folders[1];
  const lists = await clickupRequest(`/folder/${devFolder.id}/list`);
  await createBoardView(lists.lists[0].id, 'Sprint Board');

  return { space, folders };
}
```

## Error Handling

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Missing `name` field | Name is required for spaces/folders/lists |
| 403 | Insufficient permissions | Need admin access for space creation |
| 404 | Invalid parent ID | Verify team_id/space_id/folder_id |

## Resources

- [Get Spaces](https://developer.clickup.com/reference/getspaces)
- [Get Folders](https://developer.clickup.com/reference/getfolders)
- [Views Documentation](https://developer.clickup.com/docs/views)

## Next Steps

For error troubleshooting, see `clickup-common-errors`.
