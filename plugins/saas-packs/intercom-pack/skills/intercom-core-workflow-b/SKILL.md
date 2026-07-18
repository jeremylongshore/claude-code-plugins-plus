---
name: intercom-core-workflow-b
description: 'Manage Intercom conversations: create, reply, close, snooze, assign,
  and tag.

  Use when building conversation management features, automating replies,

  or implementing support workflow automation.

  Trigger with phrases like "intercom conversations", "intercom reply",

  "intercom assign conversation", "intercom close conversation",

  "intercom snooze", "manage intercom conversations".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Conversations & Messaging

## Overview

Manage the full conversation lifecycle: create, reply (as admin or contact), assign to teams, close, snooze, and tag. Conversations contain threaded "parts" including messages, notes, and assignments.

This SKILL.md gives you the high-level workflow and the essential skeleton. The complete step-by-step code for all seven operations lives in [references/implementation.md](references/implementation.md); realistic end-to-end scenarios are in [references/examples.md](references/examples.md).

## Prerequisites

- Completed `intercom-install-auth` setup (provides the `INTERCOM_ACCESS_TOKEN`)
- Admin ID (from `client.admins.list()`)
- Contact IDs for conversation participants

## Authentication

All calls authenticate with a bearer access token supplied to the SDK client — see `intercom-install-auth` for how to obtain and store it. Read it from the environment, never hard-code it:

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});
```

The raw `run_assignment_rules` endpoint (Step 3) uses the same token as an `Authorization: Bearer` header.

## Instructions

The workflow is seven operations against `client.conversations.*`. Reach for the one you need — they are independent once you have a conversation ID.

1. **Create** — `conversations.create({ from, body })` opens a conversation from a contact and returns its `conversationId`.
2. **Reply** — `conversations.reply(...)` adds a part. `type: "admin"` is customer-visible, `type: "note"` is internal-only, `type: "user"` is a contact reply.
3. **Assign** — `conversations.assign(...)` routes to an admin (`type: "admin"`) or team (`type: "team"`); or POST `run_assignment_rules` for auto-routing.
4. **Close / snooze / reopen** — `conversations.close(...)`, `conversations.snooze({ snoozedUntil })` (Unix seconds), and `conversations.open(...)`.
5. **Tag** — `conversations.attachTag(...)` / `detachTag(...)`.
6. **Retrieve** — `conversations.find(...)` returns state, assignee, and the `conversationParts` thread.
7. **List / search** — `conversations.list()` or `conversations.search({ query, pagination, sort })` with AND/OR field filters.

Essential skeleton (create then reply); see [references/implementation.md](references/implementation.md) for every step in full:

```typescript
const conversation = await client.conversations.create({
  from: { type: "user", id: "6657add46abd0167d9419c3a" }, // Contact ID
  body: "Hi, I'm having trouble with my billing. Can you help?",
});

await client.conversations.reply({
  conversationId: conversation.conversationId,
  body: "Hi there! I'd be happy to help. What's the issue?",
  type: "admin",
  adminId: "12345",
});
```

## Output

Each operation returns the affected conversation (or acknowledges the mutation):

- `create` → a conversation object exposing `conversationId` (use it for every follow-up call).
- `reply` / `assign` / `close` / `snooze` / `open` → the updated conversation with its new `state` and appended part.
- `find` → the full conversation: `state` (`"open" | "closed" | "snoozed"`), `adminAssigneeId`, and `conversationParts` (`totalCount` + the ordered thread of `comment` / `note` / `assignment` / `close` / `open` parts).
- `search` / `list` → a paginated collection of matching conversations, ordered by your `sort` clause.

### Conversation States

| State | Description | Transitions |
|-------|-------------|-------------|
| `open` | Active, awaiting action | close, snooze |
| `closed` | Resolved | open |
| `snoozed` | Deferred until timestamp | open (auto or manual) |

### Conversation Part Types

| Part Type | Description | Who Creates |
|-----------|-------------|------------|
| `comment` | Visible message | Admin or contact |
| `note` | Internal-only note | Admin |
| `assignment` | Reassignment record | System or admin |
| `close` | Conversation closed | Admin |
| `open` | Conversation reopened | Admin or contact |

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `not_found` | 404 | Invalid conversation or admin ID | Verify IDs exist |
| `conversation_not_found` | 404 | Conversation deleted | Handle gracefully |
| `admin_not_found` | 404 | Admin ID invalid | Use `client.admins.list()` |
| `parameter_invalid` | 422 | Missing body or type | Include required fields |
| `conversation_closed` | 400 | Action on closed conversation | Reopen first |

For common errors and debugging, see `intercom-common-errors`.

## Examples

Three end-to-end scenarios are worked in full in [references/examples.md](references/examples.md):

1. **Handle a billing complaint end-to-end** — create → reply → assign to team → close.
2. **Tag, snooze, and follow up** — attach a tag, leave an internal note, snooze 24h, reopen.
3. **Audit an open queue** — search open conversations for an admin, then inspect a thread's parts.

The billing flow, in brief:

```typescript
const conversation = await client.conversations.create({
  from: { type: "user", id: "6657add46abd0167d9419c3a" },
  body: "Hi, I'm having trouble with my billing. Can you help?",
});
await client.conversations.assign({
  conversationId: conversation.conversationId,
  type: "team",
  adminId: "12345",
  assigneeId: "team-billing-123",
  body: "Routing to billing team",
});
await client.conversations.close({
  conversationId: conversation.conversationId,
  adminId: "12345",
  body: "Issue resolved! Let us know if you need anything else.",
});
```

## Resources

- [references/implementation.md](references/implementation.md) — full seven-step walkthrough with every code block
- [references/examples.md](references/examples.md) — three end-to-end worked scenarios
- [Conversations API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations)
- [Reply to Conversation](https://developers.intercom.com/docs/references/2.2/rest-api/conversations/reply-to-a-conversation)
- [Manage Conversation](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations/manageconversation)
