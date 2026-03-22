---
name: intercom-core-workflow-a
description: |
  Manage Intercom contacts: create, search, update, merge leads into users.
  Use when building contact management features, syncing user data,
  or implementing contact search and segmentation.
  Trigger with phrases like "intercom contacts", "intercom users",
  "intercom leads", "create intercom contact", "search intercom contacts",
  "merge intercom lead".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Contacts & Contact Management

## Overview

Primary workflow for managing Intercom contacts. Covers creating users and leads, searching with filters, updating custom attributes, merging leads into users, and managing tags and segments.

## Prerequisites

- Completed `intercom-install-auth` setup
- Understanding of Intercom contact model (users vs leads)
- Valid API credentials with contacts read/write scope

## Instructions

### Step 1: Create Contacts

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
  phone: "+1-555-0100",
  customAttributes: {
    plan: "enterprise",
    company_size: 500,
    signed_up_at: Math.floor(Date.now() / 1000),
  },
});
// Response: { type: "contact", id: "6657add46abd...", role: "user", ... }

// Create an anonymous lead (no external_id required)
const lead = await client.contacts.create({
  role: "lead",
  email: "visitor@example.com",
  name: "Website Visitor",
  customAttributes: {
    landing_page: "/pricing",
    utm_source: "google",
  },
});
```

### Step 2: Search Contacts

POST to `https://api.intercom.io/contacts/search` with query filters.

```typescript
// Simple search by email
const byEmail = await client.contacts.search({
  query: {
    field: "email",
    operator: "=",
    value: "alice@acme.com",
  },
});

// Compound search: users on enterprise plan who signed up recently
const filtered = await client.contacts.search({
  query: {
    operator: "AND",
    value: [
      { field: "role", operator: "=", value: "user" },
      { field: "custom_attributes.plan", operator: "=", value: "enterprise" },
      { field: "signed_up_at", operator: ">", value: Math.floor(Date.now() / 1000) - 86400 * 30 },
    ],
  },
  pagination: { per_page: 50 },
  sort: { field: "created_at", order: "descending" },
});

console.log(`Found ${filtered.totalCount} contacts`);
for (const contact of filtered.data) {
  console.log(`  ${contact.name} (${contact.email}) - plan: ${contact.customAttributes?.plan}`);
}
```

### Step 3: Update a Contact

```typescript
const updated = await client.contacts.update({
  contactId: user.id,
  name: "Alice Johnson-Smith",
  customAttributes: {
    plan: "enterprise_plus",
    upgraded_at: Math.floor(Date.now() / 1000),
  },
});
```

### Step 4: Merge a Lead into a User

When an anonymous lead is identified, merge them into a user contact. The lead's conversation history transfers to the user.

```typescript
// Lead must have role "lead", user must have role "user"
const merged = await client.contacts.merge({
  from: lead.id,  // Lead ID (will be deleted)
  into: user.id,  // User ID (will absorb lead data)
});

console.log(`Merged lead into user: ${merged.id}`);
// The lead's conversations, events, and tags are now on the user
```

### Step 5: List Segments for a Contact

```typescript
const segments = await client.contacts.listSegments({
  contactId: user.id,
});

for (const segment of segments.data) {
  console.log(`Segment: ${segment.name} (${segment.id})`);
}
```

### Step 6: Paginate All Contacts

```typescript
async function* allContacts(client: IntercomClient) {
  let startingAfter: string | undefined;

  do {
    const page = await client.contacts.list({
      perPage: 50,
      startingAfter,
    });

    for (const contact of page.data) {
      yield contact;
    }

    startingAfter = page.pages?.next?.startingAfter ?? undefined;
  } while (startingAfter);
}

// Stream all contacts
let count = 0;
for await (const contact of allContacts(client)) {
  count++;
  if (count % 100 === 0) console.log(`Processed ${count} contacts`);
}
```

## Contact Data Model

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

## Resources

- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)
- [Merge Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/mergecontact)
- [Contact Guides](https://developers.intercom.com/docs/guides/contacts)

## Next Steps

For conversation management, see `intercom-core-workflow-b`.
