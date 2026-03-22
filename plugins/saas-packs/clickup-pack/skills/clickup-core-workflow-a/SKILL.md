---
name: clickup-core-workflow-a
description: |
  Manage ClickUp tasks via API v2: create, read, update, delete tasks with
  assignees, priorities, due dates, subtasks, and statuses.
  Trigger: "clickup task", "create clickup task", "update task status",
  "manage clickup tasks", "clickup CRUD", "clickup task management".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Core Workflow A — Task Management

## Overview

CRUD operations on ClickUp tasks via API v2. Tasks live in Lists and support assignees, priorities (1-4), statuses, due dates, tags, checklists, and custom fields.

## Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create task | POST | `/api/v2/list/{list_id}/task` |
| Get task | GET | `/api/v2/task/{task_id}` |
| Update task | PUT | `/api/v2/task/{task_id}` |
| Delete task | DELETE | `/api/v2/task/{task_id}` |
| Get tasks in list | GET | `/api/v2/list/{list_id}/task` |
| Add task to list | POST | `/api/v2/list/{list_id}/task/{task_id}` |
| Create subtask | POST | `/api/v2/list/{list_id}/task` (with `parent` field) |

## Create Task

```typescript
interface CreateTaskBody {
  name: string;                    // Required
  description?: string;            // Plain text
  markdown_description?: string;   // Markdown (use instead of description)
  assignees?: number[];            // Array of user IDs
  tags?: string[];                 // Tag names
  status?: string;                 // Status name (e.g., "to do", "in progress")
  priority?: 1 | 2 | 3 | 4 | null; // 1=Urgent, 2=High, 3=Normal, 4=Low
  due_date?: number;               // Unix timestamp in milliseconds
  due_date_time?: boolean;         // true = show time, false = date only
  start_date?: number;             // Unix ms
  start_date_time?: boolean;
  time_estimate?: number;          // Time estimate in milliseconds
  notify_all?: boolean;            // Notify assignees
  parent?: string;                 // Parent task ID (creates subtask)
  links_to?: string;               // Task ID to link to
  custom_fields?: Array<{
    id: string;                    // Custom field UUID
    value: any;                    // Type-dependent value
  }>;
}

async function createTask(listId: string, task: CreateTaskBody) {
  return clickupRequest(`/list/${listId}/task`, {
    method: 'POST',
    body: JSON.stringify(task),
  });
}

// Example: Create an urgent task with assignee
await createTask('900100200300', {
  name: 'Fix production bug in auth module',
  markdown_description: '## Bug\nLogin fails for SSO users\n\n## Steps\n1. Go to /login\n2. Click SSO',
  assignees: [183],
  priority: 1,
  status: 'in progress',
  due_date: Date.now() + 3600000,
  due_date_time: true,
  tags: ['bug', 'production'],
});
```

## Get Tasks (with Filtering)

```typescript
async function getTasks(listId: string, params: Record<string, string> = {}) {
  const query = new URLSearchParams({
    archived: 'false',
    include_closed: 'false',
    subtasks: 'true',
    ...params,
  });
  return clickupRequest(`/list/${listId}/task?${query}`);
}

// Filter by assignee and status
const tasks = await getTasks('900100200300', {
  'assignees[]': '183',
  'statuses[]': 'in progress',
  order_by: 'due_date',
  reverse: 'true',
  page: '0',          // Pagination: 100 tasks per page
});
// Response: { tasks: [...] }
```

## Update Task

```typescript
// Only include fields you want to change
async function updateTask(taskId: string, updates: Partial<CreateTaskBody>) {
  return clickupRequest(`/task/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

// Change status and add assignee
await updateTask('abc123', {
  status: 'complete',
  assignees: { add: [456], rem: [] },  // Add/remove pattern for assignees on update
});
```

## Create Subtask

```typescript
await createTask('900100200300', {
  name: 'Write unit tests for auth fix',
  parent: 'abc123',  // Parent task ID makes this a subtask
  assignees: [183],
  priority: 3,
});
```

## Bulk Operations

```typescript
// Get all tasks across workspace with team-level endpoint
async function searchTasks(teamId: string, query: string) {
  return clickupRequest(`/team/${teamId}/task?${new URLSearchParams({
    page: '0',
    order_by: 'updated',
    reverse: 'true',
    include_closed: 'true',
    subtasks: 'true',
  })}`);
}
```

## Error Handling

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Missing `name` field | Task name is required |
| 401 | Invalid token | Re-authenticate |
| 404 | Invalid list_id or task_id | Verify IDs via GET endpoints |
| 403 | No permission on this list | Check workspace membership |

## Resources

- [Create Task API](https://developer.clickup.com/reference/createtask)
- [Update Task API](https://developer.clickup.com/reference/updatetask)
- [Get Tasks API](https://developer.clickup.com/reference/gettasks)

## Next Steps

For spaces, folders, and lists management see `clickup-core-workflow-b`.
