---
name: intercom-core-workflow-a
description: 'Manage Intercom contacts: create, search, update, merge leads into users.

  Use when building contact management features, syncing user data, or implementing
  contact search and segmentation against the Intercom REST API.

  Trigger with phrases like "intercom contacts", "intercom users",
  "intercom leads", "create intercom contact", "search intercom contacts",
  "merge intercom lead".

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
# Intercom Contacts & Contact Management

## Overview

Primary workflow for managing Intercom contacts. Covers creating users and leads, searching with filters, updating custom attributes, merging leads into users, and listing segments. This SKILL.md gives you the high-level workflow and the first example; drill into [references/implementation.md](references/implementation.md) for the full step-by-step code and [references/examples.md](references/examples.md) for end-to-end flows.

## Prerequisites

- Completed `intercom-install-auth` setup
- Understanding of Intercom contact model (users vs leads)
- Valid API credentials with contacts read/write scope

## Instructions

The contact workflow is six operations against the `intercom-client` SDK. Instantiate the client once, then call the operation you need:

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// Create an identified user (has external_id)
const user = await client.contacts.create({
  role: "user",
  externalId: "customer-9001",
  email: "alice@acme.com",
  name: "Alice Johnson",
  customAttributes: { plan: "enterprise" },
});
```

The six operations, in the order you typically reach for them:

1. **Create contacts** — `contacts.create` with `role: "user"` (identified, needs `externalId`) or `role: "lead"` (anonymous).
2. **Search contacts** — `contacts.search` with a single filter or a compound `AND`/`OR` query, plus pagination and sort.
3. **Update a contact** — `contacts.update` by `contactId` to change name or custom attributes.
4. **Merge a lead into a user** — `contacts.merge({ from: leadId, into: userId })`; the lead's conversations, events, and tags transfer to the user.
5. **List segments** — `contacts.listSegments({ contactId })` to see which segments a contact belongs to.
6. **Paginate all contacts** — `contacts.list` with `startingAfter` cursor to stream the full contact base.

Full code for every step, including compound-search filters and the async-generator pagination helper, is in [references/implementation.md](references/implementation.md).

## Output

Each operation returns a typed response from the SDK:

- **`create` / `update`** — a single `contact` object: `{ type: "contact", id, role, email, name, customAttributes, created_at, ... }`. The `id` is the Intercom-generated handle you pass to later calls.
- **`search`** — `{ data: Contact[], totalCount, pages }`. Iterate `data`; read `totalCount` for the match count; use `pages.next.startingAfter` to page.
- **`merge`** — the surviving `user` contact (the `into` target); the `from` lead is deleted.
- **`listSegments`** — `{ data: Segment[] }`, each `{ id, name }`.
- **`list`** — one page `{ data: Contact[], pages }`; follow `pages.next.startingAfter` until it is absent.

### Contact Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Intercom-generated unique ID |
| `external_id` | string | Your system's user ID |
| `role` | `"user"` or `"lead"` | Contact type |
| `email` | string | Email address |
| `name` | string | Full name |
| `phone` | string | Phone number |
| `custom_attributes` | object | Custom key-value data |
| `created_at` | number | Unix timestamp |
| `last_seen_at` | number | Last activity timestamp |
| `signed_up_at` | number | Signup timestamp |
| `tags` | object | Applied tags list |
| `companies` | object | Associated companies |
| `location` | object | GeoIP location data |

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `not_found` | 404 | Contact ID doesn't exist | Verify with search first |
| `conflict` | 409 | Duplicate `external_id` or `email` | Search before creating |
| `parameter_invalid` | 422 | Bad field value or missing required field | Check field types and names |
| `rate_limit_exceeded` | 429 | Over 10,000 req/min (private apps) | Add backoff, batch operations |
| `merge_not_possible` | 400 | Merging user into lead (reversed) | `from` must be lead, `into` must be user |

## Examples

Quick create-then-search flow:

```typescript
const user = await client.contacts.create({
  role: "user",
  externalId: "customer-9001",
  email: "alice@acme.com",
  name: "Alice Johnson",
});

const found = await client.contacts.search({
  query: { field: "email", operator: "=", value: "alice@acme.com" },
});
console.log(`Found ${found.totalCount} match(es)`);
```

Three fuller worked flows — lead-to-user lifecycle, segmenting recent enterprise signups, and streaming every contact for an export — are in [references/examples.md](references/examples.md).

## Resources

- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)
- [Merge Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/mergecontact)
- [Contact Guides](https://developers.intercom.com/docs/guides/contacts)

## Next Steps

For conversation management (creating, replying to, and searching conversations), see the companion skill `intercom-core-workflow-b`, which builds on the contact IDs produced by this workflow.
