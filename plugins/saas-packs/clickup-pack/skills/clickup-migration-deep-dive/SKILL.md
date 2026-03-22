---
name: clickup-migration-deep-dive
description: |
  Migrate to ClickUp from other project management tools (Jira, Asana, Trello)
  or migrate data between ClickUp workspaces using API v2.
  Trigger: "migrate to clickup", "clickup migration", "jira to clickup",
  "asana to clickup", "trello to clickup", "clickup data migration",
  "move tasks to clickup", "clickup import".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Migration Deep Dive

## Overview

Migrate project data to ClickUp from external tools or between ClickUp workspaces using API v2. Covers data mapping, batch creation, custom field migration, and validation.

## Migration Types

| Source | Complexity | Key Challenge |
|--------|-----------|---------------|
| Trello | Low | Board -> List mapping, labels -> tags |
| Asana | Medium | Sections -> statuses, custom fields |
| Jira | High | Epics/stories/subtasks, custom fields, workflows |
| Another ClickUp workspace | Medium | Custom field UUIDs differ per workspace |

## ClickUp Hierarchy Mapping

```
External Concept        ClickUp API v2 Target
─────────────────       ──────────────────────
Project/Board       →   Space   (POST /team/{team_id}/space)
Epic/Section        →   Folder  (POST /space/{space_id}/folder)
Sprint/Column       →   List    (POST /folder/{folder_id}/list)
Issue/Card/Task     →   Task    (POST /list/{list_id}/task)
Subtask             →   Task with parent  (parent field)
Label/Tag           →   Tag     (POST /task/{task_id}/tag/{tag_name})
Custom Field        →   Custom Field (POST /task/{task_id}/field/{field_id})
Comment             →   Comment (POST /task/{task_id}/comment)
Attachment          →   Attachment (POST /task/{task_id}/attachment)
```

## Migration Script

```typescript
// src/migrate-to-clickup.ts
interface MigrationItem {
  externalId: string;
  name: string;
  description: string;
  status: string;
  priority?: 'urgent' | 'high' | 'normal' | 'low';
  assigneeEmail?: string;
  dueDate?: string;
  labels?: string[];
  subtasks?: MigrationItem[];
}

const PRIORITY_MAP: Record<string, number> = {
  urgent: 1, high: 2, normal: 3, low: 4,
};

const STATUS_MAP: Record<string, string> = {
  'To Do': 'to do',
  'In Progress': 'in progress',
  'Done': 'complete',
  'Backlog': 'to do',
  // Add your status mappings here
};

async function migrateItems(
  items: MigrationItem[],
  listId: string,
  memberEmails: Map<string, number>, // email -> ClickUp user ID
): Promise<{ migrated: number; errors: Array<{ item: string; error: string }> }> {
  let migrated = 0;
  const errors: Array<{ item: string; error: string }> = [];

  for (const item of items) {
    try {
      const assignees = item.assigneeEmail && memberEmails.has(item.assigneeEmail)
        ? [memberEmails.get(item.assigneeEmail)!]
        : [];

      const task = await clickupRequest(`/list/${listId}/task`, {
        method: 'POST',
        body: JSON.stringify({
          name: item.name,
          markdown_description: item.description,
          status: STATUS_MAP[item.status] ?? 'to do',
          priority: item.priority ? PRIORITY_MAP[item.priority] : null,
          assignees,
          due_date: item.dueDate ? new Date(item.dueDate).getTime() : undefined,
          due_date_time: !!item.dueDate,
          tags: item.labels ?? [],
        }),
      });

      // Migrate subtasks
      if (item.subtasks?.length) {
        for (const subtask of item.subtasks) {
          await clickupRequest(`/list/${listId}/task`, {
            method: 'POST',
            body: JSON.stringify({
              name: subtask.name,
              markdown_description: subtask.description,
              parent: task.id,
              status: STATUS_MAP[subtask.status] ?? 'to do',
            }),
          });
        }
      }

      migrated++;
      console.log(`Migrated: ${item.name} -> ${task.id}`);

      // Rate limit: stay under 100 req/min
      await new Promise(r => setTimeout(r, 700));
    } catch (error) {
      errors.push({ item: item.name, error: String(error) });
    }
  }

  return { migrated, errors };
}
```

## Build Member Lookup

```typescript
// Map external emails to ClickUp user IDs
async function buildMemberLookup(teamId: string): Promise<Map<string, number>> {
  const data = await clickupRequest(`/team/${teamId}`);
  const lookup = new Map<string, number>();

  for (const member of data.team.members) {
    lookup.set(member.user.email, member.user.id);
  }

  return lookup;
}
```

## Workspace-to-Workspace Migration

```typescript
async function cloneListBetweenWorkspaces(
  sourceToken: string,
  sourceListId: string,
  destToken: string,
  destListId: string,
) {
  // Fetch all tasks from source
  const sourceTasks = [];
  let page = 0;
  let hasMore = true;

  while (hasMore) {
    const data = await fetch(
      `https://api.clickup.com/api/v2/list/${sourceListId}/task?page=${page}&subtasks=true&include_closed=true`,
      { headers: { 'Authorization': sourceToken } }
    ).then(r => r.json());

    sourceTasks.push(...data.tasks);
    hasMore = data.tasks.length === 100;
    page++;
  }

  console.log(`Fetched ${sourceTasks.length} tasks from source`);

  // Create tasks in destination
  for (const task of sourceTasks) {
    if (task.parent) continue; // Handle subtasks separately

    const created = await fetch(
      `https://api.clickup.com/api/v2/list/${destListId}/task`,
      {
        method: 'POST',
        headers: { 'Authorization': destToken, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: task.name,
          markdown_description: task.description,
          priority: task.priority?.id ? parseInt(task.priority.id) : null,
          tags: task.tags.map((t: any) => t.name),
        }),
      }
    ).then(r => r.json());

    console.log(`Cloned: ${task.name} -> ${created.id}`);
    await new Promise(r => setTimeout(r, 700)); // Rate limit
  }
}
```

## Validation

```typescript
async function validateMigration(
  sourceItems: MigrationItem[],
  listId: string,
): Promise<{ match: number; missing: string[] }> {
  const tasks = await clickupRequest(`/list/${listId}/task?include_closed=true`);
  const taskNames = new Set(tasks.tasks.map((t: any) => t.name));

  const missing = sourceItems
    .filter(item => !taskNames.has(item.name))
    .map(item => item.name);

  return {
    match: sourceItems.length - missing.length,
    missing,
  };
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited during migration | Too many creates | Add 700ms delay between requests |
| Status not found | Status name mismatch | Map source statuses to ClickUp statuses |
| Assignee not found | Email not in workspace | Invite user first or skip assignment |
| Custom field UUID mismatch | Different workspace | Re-fetch field UUIDs via `/list/{id}/field` |

## Resources

- [ClickUp Create Task](https://developer.clickup.com/reference/createtask)
- [ClickUp Get Tasks](https://developer.clickup.com/reference/gettasks)
- [ClickUp Import Guide](https://help.clickup.com/hc/en-us/categories/6301007545623-Import-Export)

## Next Steps

For advanced troubleshooting during migration, see `clickup-debug-bundle`.
