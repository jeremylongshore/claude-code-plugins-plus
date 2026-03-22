---
name: intercom-hello-world
description: |
  Create a minimal working Intercom example with contacts, conversations, and messages.
  Use when starting a new Intercom integration, testing your setup,
  or learning the core Intercom API data model.
  Trigger with phrases like "intercom hello world", "intercom example",
  "intercom quick start", "simple intercom code", "first intercom API call".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Hello World

## Overview

Minimal working examples covering the Intercom core data model: contacts (users and leads), conversations, messages, and tags.

## Prerequisites

- Completed `intercom-install-auth` setup
- `intercom-client` package installed
- Valid access token in environment

## Instructions

### Step 1: Create a Contact

Contacts are the core entity. They have a `role` of either `user` (identified) or `lead` (anonymous).

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// Create a user contact
const user = await client.contacts.create({
  role: "user",
  externalId: "user-12345",
  email: "jane@example.com",
  name: "Jane Smith",
  customAttributes: {
    plan: "pro",
    signup_date: Math.floor(Date.now() / 1000),
  },
});

console.log(`Created contact: ${user.id} (${user.role})`);

// Response shape:
// {
//   type: "contact",
//   id: "6657add46abd0167d9419c3a",
//   workspace_id: "abc123",
//   external_id: "user-12345",
//   role: "user",
//   email: "jane@example.com",
//   name: "Jane Smith",
//   custom_attributes: { plan: "pro", signup_date: 1711100000 },
//   created_at: 1711100000,
//   updated_at: 1711100000,
//   ...
// }
```

### Step 2: Search for Contacts

```typescript
// Search contacts by email
const results = await client.contacts.search({
  query: {
    field: "email",
    operator: "=",
    value: "jane@example.com",
  },
});

console.log(`Found ${results.totalCount} contacts`);
for (const contact of results.data) {
  console.log(`  ${contact.name} - ${contact.email} (${contact.role})`);
}
```

### Step 3: Send a Message

Messages are outbound communications from admins to contacts.

```typescript
// Send an in-app message
const message = await client.messages.create({
  messageType: "inapp",
  body: "Welcome to our platform! Need help getting started?",
  from: {
    type: "admin",
    id: "12345", // Admin ID from client.admins.list()
  },
  to: {
    type: "user",
    id: user.id,
  },
});

console.log(`Sent message: ${message.id}`);
```

### Step 4: Create a Conversation

Conversations are created when a contact replies or an admin initiates.

```typescript
// Create a conversation (as a contact)
const conversation = await client.conversations.create({
  from: {
    type: "user",
    id: user.id,
  },
  body: "Hi, I have a question about billing.",
});

console.log(`Conversation created: ${conversation.conversationId}`);
```

### Step 5: Tag a Contact

```typescript
// Create a tag
const tag = await client.tags.create({ name: "vip-customer" });

// Tag a contact
await client.contacts.tag({
  contactId: user.id,
  id: tag.id,
});

console.log(`Tagged contact ${user.id} with "${tag.name}"`);
```

## Core Data Model

| Entity | Description | Key Fields |
|--------|-------------|------------|
| Contact | Users and leads | `id`, `role`, `email`, `external_id`, `custom_attributes` |
| Conversation | Threaded exchanges | `id`, `state`, `contacts`, `conversation_parts` |
| Message | Outbound from admin | `id`, `message_type`, `body`, `from`, `to` |
| Tag | Labels for entities | `id`, `name`, `applied_to` |
| Company | Organization grouping | `id`, `company_id`, `name`, `plan` |
| Admin | Workspace team member | `id`, `name`, `email`, `type` |

## Complete Working Script

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

async function main() {
  // 1. Verify connection
  const me = await client.admins.list();
  const admin = me.admins[0];
  console.log(`Authenticated as: ${admin.name}`);

  // 2. Create or find a contact
  const contact = await client.contacts.create({
    role: "user",
    externalId: `hello-world-${Date.now()}`,
    email: `test-${Date.now()}@example.com`,
    name: "Hello World User",
  });
  console.log(`Contact: ${contact.id}`);

  // 3. List all contacts (paginated)
  const contacts = await client.contacts.list();
  console.log(`Total contacts in workspace: ${contacts.totalCount}`);

  // 4. List conversations
  const conversations = await client.conversations.list();
  console.log(`Total conversations: ${conversations.totalCount}`);
}

main().catch(console.error);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `not_found` (404) | Contact/conversation ID invalid | Verify the ID exists |
| `parameter_invalid` | Missing required field | Check required params in docs |
| `conflict` (409) | Duplicate `external_id` | Use unique identifiers |
| `unauthorized` (401) | Invalid token | Regenerate access token |

## Resources

- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Conversations API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations)
- [Messages API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/messages)
- [intercom-node GitHub](https://github.com/intercom/intercom-node)

## Next Steps

Proceed to `intercom-local-dev-loop` for development workflow setup.
