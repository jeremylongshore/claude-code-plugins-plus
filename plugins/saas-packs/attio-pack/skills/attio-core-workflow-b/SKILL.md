---
name: attio-core-workflow-b
description: |
  Manage Attio lists, entries, notes, and tasks via the REST API.
  Use when working with sales pipelines, kanban boards, CRM notes,
  or task assignments in Attio.
  Trigger: "attio lists", "attio entries", "attio pipeline",
  "attio notes", "attio tasks", "add to attio list".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Lists, Notes & Tasks (Core Workflow B)

## Overview

Lists are Attio's pipeline/board primitive -- they contain entries (records added to the list with list-specific attributes like stage or owner). This skill also covers notes and tasks, which attach to records for activity tracking.

## Prerequisites

- `attio-install-auth` completed
- Scopes: `object_configuration:read`, `record_permission:read`, `list_entry:read`, `list_entry:read-write`, `note:read-write`, `task:read-write`, `user_management:read`

## Instructions

### Step 1: List All Lists

```typescript
// GET /v2/lists
const lists = await client.get<{
  data: Array<{
    id: { list_id: string };
    api_slug: string;
    name: string;
    parent_object: string[];  // Which object types can be added
  }>;
}>("/lists");

console.log(lists.data.map((l) => `${l.api_slug}: ${l.name}`));
// Output: ["sales_pipeline: Sales Pipeline", "hiring: Hiring Pipeline"]
```

### Step 2: Query List Entries

```typescript
// POST /v2/lists/{list_slug}/entries/query
const entries = await client.post<{
  data: Array<{
    entry_id: string;
    record_id: string;
    created_at: string;
    values: Record<string, any[]>;
  }>;
}>("/lists/sales_pipeline/entries/query", {
  filter: {
    stage: { status: { $eq: "In Progress" } },
  },
  sorts: [
    { attribute: "created_at", field: "created_at", direction: "desc" },
  ],
  limit: 50,
});
```

### Step 3: Add a Record to a List (Create Entry)

```typescript
// POST /v2/lists/{list_slug}/entries
const entry = await client.post<{ data: { entry_id: string } }>(
  "/lists/sales_pipeline/entries",
  {
    data: {
      // The record to add to the list
      parent_record_id: companyRecordId,
      parent_object: "companies",
      // List-specific attribute values
      values: {
        stage: [{ status: "Qualified" }],
        deal_value: [{ currency_code: "USD", currency_value: 50000 }],
        owner: [{ referenced_actor_id: workspaceMemberId, referenced_actor_type: "workspace-member" }],
      },
    },
  }
);
```

### Step 4: Update an Entry

```typescript
// PATCH /v2/lists/{list_slug}/entries/{entry_id} -- append multiselect
await client.patch(
  `/lists/sales_pipeline/entries/${entryId}`,
  {
    data: {
      values: {
        stage: [{ status: "Won" }],
      },
    },
  }
);

// PUT /v2/lists/{list_slug}/entries/{entry_id} -- overwrite multiselect
await client.put(
  `/lists/sales_pipeline/entries/${entryId}`,
  {
    data: {
      values: {
        stage: [{ status: "Lost" }],
      },
    },
  }
);
```

### Step 5: Delete an Entry (Remove from List)

```typescript
// DELETE /v2/lists/{list_slug}/entries/{entry_id}
await client.delete(`/lists/sales_pipeline/entries/${entryId}`);
// Note: This removes from the list only. The underlying record is not deleted.
```

### Step 6: Create a Note on a Record

```typescript
// POST /v2/notes
const note = await client.post<{
  data: { id: { note_id: string } };
}>("/notes", {
  data: {
    // Link to a parent record
    parent_object: "companies",
    parent_record_id: companyRecordId,
    // Note content
    title: "Q1 Review Meeting",
    format: "plaintext",                     // or "markdown"
    content: "Discussed renewal timeline. Budget approved for next quarter.",
  },
});
```

### Step 7: List Notes on a Record

```typescript
// GET /v2/notes?parent_object=companies&parent_record_id={id}
const notes = await client.get<{
  data: Array<{
    id: { note_id: string };
    title: string;
    content: string;
    created_at: string;
    created_by_actor: { type: string; id: string };
  }>;
}>(`/notes?parent_object=companies&parent_record_id=${companyRecordId}`);
```

### Step 8: Create and Manage Tasks

```typescript
// POST /v2/tasks
const task = await client.post<{
  data: { id: { task_id: string } };
}>("/tasks", {
  data: {
    content: "Send renewal proposal to Acme Corp",
    deadline: "2025-07-15T17:00:00.000Z",
    is_completed: false,
    // Link to records
    linked_records: [
      { target_object: "companies", target_record_id: companyRecordId },
    ],
    // Assign to workspace members
    assignees: [
      { referenced_actor_id: memberId, referenced_actor_type: "workspace-member" },
    ],
  },
});

// Complete a task
await client.patch(`/tasks/${taskId}`, {
  data: { is_completed: true },
});

// List tasks (sorted oldest to newest by default)
const tasks = await client.get<{
  data: Array<{
    id: { task_id: string };
    content: string;
    deadline: string | null;
    is_completed: boolean;
  }>;
}>("/tasks");
```

## Attio Lists vs Records Mental Model

```
Objects (people, companies, deals)
 └── Records  ← individual CRM entries (Step 1-7 of core-workflow-a)
      └── Notes, Tasks  ← activity attached to records

Lists (pipelines, boards)
 └── Entries  ← a record placed in a list context
      └── List-specific values (stage, owner, custom columns)
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `not_found` | 404 | Invalid list slug or entry ID | Verify with `GET /v2/lists` |
| `insufficient_scopes` | 403 | Missing `list_entry:read-write` | Update token scopes |
| `validation_error` | 422 | Wrong parent_object for list | Check list's `parent_object` array |
| `insufficient_scopes` | 403 | Missing `note:read-write` for notes | Add note scope to token |
| `insufficient_scopes` | 403 | Missing `task:read-write` + `user_management:read` | Tasks need both scopes |

## Resources

- [Attio List Entries](https://docs.attio.com/rest-api/endpoint-reference/entries/list-entries)
- [Attio Create Note](https://docs.attio.com/rest-api/endpoint-reference/notes/create-a-note)
- [Attio Create Task](https://docs.attio.com/rest-api/endpoint-reference/tasks/create-a-task)
- [Attio Objects and Lists](https://docs.attio.com/docs/objects-and-lists)

## Next Steps

For error diagnosis, see `attio-common-errors`. For webhooks on list/record changes, see `attio-webhooks-events`.
