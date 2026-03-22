---
name: clickup-reference-architecture
description: |
  Production architecture for ClickUp API v2 integrations with layered design,
  custom fields, time tracking, goals, and two-way sync patterns.
  Trigger: "clickup architecture", "clickup design", "clickup project structure",
  "clickup custom fields", "clickup time tracking", "clickup goals API".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Reference Architecture

## Overview

Production-ready architecture for ClickUp API v2 integrations covering custom fields, time tracking, goals, and two-way sync with external systems.

## Architecture Layers

```
┌──────────────────────────────────────────┐
│          Application Layer               │
│   (Routes, Controllers, Webhooks)        │
├──────────────────────────────────────────┤
│          Service Layer                   │
│   (Business Logic, Orchestration)        │
├──────────────────────────────────────────┤
│          ClickUp Client Layer            │
│   (API Wrapper, Types, Cache, Retry)     │
├──────────────────────────────────────────┤
│          Infrastructure                  │
│   (Queue, Cache, Monitoring, Secrets)    │
└──────────────────────────────────────────┘
          │
          ▼
  api.clickup.com/api/v2/
```

## Custom Fields API

Custom fields let you extend tasks beyond built-in fields. Each field has a UUID and a type.

```
GET  /api/v2/list/{list_id}/field          Get accessible custom fields
POST /api/v2/task/{task_id}/field/{field_id}  Set custom field value
DELETE /api/v2/task/{task_id}/field/{field_id}  Remove custom field value
```

### Custom Field Types and Value Formats

| Type | `value` Format | Example |
|------|---------------|---------|
| `text` | string | `"Release v2.1"` |
| `number` | number | `42` |
| `money` / `currency` | number (in smallest unit) | `9999` (= $99.99) |
| `date` | Unix ms timestamp | `1695000000000` |
| `drop_down` | option UUID from `type_config.options` | `"opt_uuid_123"` |
| `labels` | array of label UUIDs | `["lbl_uuid_1", "lbl_uuid_2"]` |
| `checkbox` | boolean | `true` |
| `email` | string | `"user@example.com"` |
| `phone` | string | `"+1-555-0100"` |
| `url` | string | `"https://example.com"` |
| `rating` | number (0-5) | `4` |
| `location` | object | `{ "lat": 33.749, "lng": -84.388 }` |

```typescript
// Get custom fields for a list
const fields = await clickupRequest(`/list/${listId}/field`);
// Response: { fields: [{ id: "uuid", name: "Sprint", type: "drop_down", type_config: { options: [...] } }] }

// Set a dropdown custom field
const sprintField = fields.fields.find((f: any) => f.name === 'Sprint');
const nextSprint = sprintField.type_config.options.find((o: any) => o.name === 'Sprint 24');

await clickupRequest(`/task/${taskId}/field/${sprintField.id}`, {
  method: 'POST',
  body: JSON.stringify({ value: nextSprint.orderindex }),
});

// Set a date custom field
await clickupRequest(`/task/${taskId}/field/${dateFieldId}`, {
  method: 'POST',
  body: JSON.stringify({ value: Date.now() + 604800000 }), // 1 week from now
});
```

## Time Tracking API

```
POST   /api/v2/team/{team_id}/time_entries     Create time entry
GET    /api/v2/team/{team_id}/time_entries     Get time entries (date range)
GET    /api/v2/team/{team_id}/time_entries/current  Get running timer
GET    /api/v2/task/{task_id}/time             Get tracked time on task
PUT    /api/v2/team/{team_id}/time_entries/{timer_id}  Update entry
DELETE /api/v2/team/{team_id}/time_entries/{timer_id}  Delete entry
```

```typescript
// Create a time entry (logged time)
await clickupRequest(`/team/${teamId}/time_entries`, {
  method: 'POST',
  body: JSON.stringify({
    task_id: 'abc123',
    description: 'Worked on auth module',
    start: Date.now() - 3600000, // 1 hour ago
    duration: 3600000,           // 1 hour in ms
    assignee: 183,               // user ID
    billable: true,
  }),
});

// Get entries for a date range (default: last 30 days)
const entries = await clickupRequest(
  `/team/${teamId}/time_entries?start_date=${startMs}&end_date=${endMs}`
);
// Note: negative duration means timer is currently running
```

## Goals API

```
POST   /api/v2/team/{team_id}/goal         Create goal
GET    /api/v2/team/{team_id}/goal         Get goals
GET    /api/v2/goal/{goal_id}              Get goal
PUT    /api/v2/goal/{goal_id}              Update goal
DELETE /api/v2/goal/{goal_id}              Delete goal
POST   /api/v2/goal/{goal_id}/key_result   Create key result
PUT    /api/v2/key_result/{key_result_id}  Update key result
DELETE /api/v2/key_result/{key_result_id}  Delete key result
```

```typescript
// Create a goal with key results
const goal = await clickupRequest(`/team/${teamId}/goal`, {
  method: 'POST',
  body: JSON.stringify({
    name: 'Q1 2026 Engineering OKRs',
    due_date: 1711929600000,
    description: 'Engineering team quarterly objectives',
    multiple_owners: true,
    owners: [183, 456],
    color: '#05a1f5',
  }),
});

// Add a key result (target)
await clickupRequest(`/goal/${goal.goal.id}/key_result`, {
  method: 'POST',
  body: JSON.stringify({
    name: 'Reduce P95 latency to <200ms',
    type: 'number',
    steps_start: 500,
    steps_end: 200,
    unit: 'ms',
    owners: [183],
  }),
});
```

## Two-Way Sync Pattern

```typescript
// Sync ClickUp tasks to external system and vice versa
class ClickUpSyncService {
  async syncToExternal(listId: string) {
    const { tasks } = await clickupRequest(`/list/${listId}/task?archived=false`);

    for (const task of tasks) {
      await externalSystem.upsert({
        externalId: task.id,
        title: task.name,
        status: this.mapStatus(task.status.status),
        assignee: task.assignees[0]?.email,
        updatedAt: parseInt(task.date_updated),
      });
    }
  }

  async syncFromExternal(externalItem: ExternalItem) {
    if (externalItem.clickupTaskId) {
      await clickupRequest(`/task/${externalItem.clickupTaskId}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: externalItem.title,
          status: this.reverseMapStatus(externalItem.status),
        }),
      });
    }
  }

  private mapStatus(clickupStatus: string): string {
    const map: Record<string, string> = {
      'to do': 'backlog', 'in progress': 'active',
      'review': 'in_review', 'complete': 'done',
    };
    return map[clickupStatus] ?? 'backlog';
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Custom field UUID not found | Field removed or renamed | Re-fetch fields via `/list/{id}/field` |
| Time entry negative duration | Timer still running | Stop timer before reading duration |
| Goal permission denied | User not goal owner | Add user to goal owners |
| Sync conflict | Both sides updated | Last-write-wins or manual merge |

## Resources

- [Custom Fields Docs](https://developer.clickup.com/docs/customfields)
- [Set Custom Field Value](https://developer.clickup.com/reference/setcustomfieldvalue)
- [Time Tracking Endpoints](https://developer.clickup.com/reference/createatimeentry)
- [ClickUp Developer Portal](https://developer.clickup.com/)

## Next Steps

For multi-environment setup, see `clickup-multi-env-setup`.
