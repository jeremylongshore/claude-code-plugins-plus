---
name: intercom-hello-world
description: 'Create a minimal working Intercom example with contacts, conversations,
  and messages.

  Use when starting a new Intercom integration, testing your setup,

  or learning the core Intercom API data model.

  Trigger with phrases like "intercom hello world", "intercom example",

  "intercom quick start", "simple intercom code", "first intercom API call".

  '
allowed-tools: Read, Write, Edit
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
# Intercom Hello World

## Overview

Minimal working examples covering the Intercom core data model: contacts (users and leads), conversations, messages, and tags. This skill gives you the first end-to-end round trip against the Intercom REST API — create a contact, search it, message it, open a conversation, and tag it — so you can confirm your credentials work and internalize how the entities relate before building anything real.

## Prerequisites

Before running any snippet below, make sure the following are in place. Each is verified once during the `intercom-install-auth` setup step:

- Completed the `intercom-install-auth` setup (installs the SDK and stores your token).
- The `intercom-client` npm package installed in your project (`npm install intercom-client`).
- A valid Intercom access token exported as `INTERCOM_ACCESS_TOKEN` in your environment. The SDK reads this token to authenticate every request; there is no separate login call.

## Instructions

The workflow is five short steps against the core data model. The first —
creating a contact — is shown in full here so you can run immediately. Steps 2
through 5 (search, message, conversation, tag) follow the identical
`client.<resource>.<verb>(...)` shape and live in the walkthrough reference.

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
});

console.log(`Created contact: ${user.id} (${user.role})`);
```

### Remaining steps

Continue in [the full walkthrough](references/walkthrough.md), which covers,
with complete code and response shapes:

- **Step 2 — Search for Contacts** (`client.contacts.search`)
- **Step 3 — Send a Message** (`client.messages.create`, admin → contact)
- **Step 4 — Create a Conversation** (`client.conversations.create`)
- **Step 5 — Tag a Contact** (`client.tags.create` + `client.contacts.tag`)

The walkthrough also carries the full **Core Data Model** reference table
(Contact, Conversation, Message, Tag, Company, Admin and their key fields).

## Output

Running the snippets produces:

- A created **contact** object — `id`, `role`, `email`, `external_id`, `custom_attributes`, and timestamps (see the full response shape in the walkthrough).
- Console log lines confirming each operation, e.g. `Created contact: 6657add46abd0167d9419c3a (user)`.
- When you run the end-to-end script, a short report of your authenticated admin name plus workspace contact and conversation counts.

Nothing is written to disk — every result is an in-memory API object plus the
`console.log` lines above. A successful run means every call returned without
throwing.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `not_found` (404) | Contact/conversation ID invalid | Verify the ID exists |
| `parameter_invalid` | Missing required field | Check required params in docs |
| `conflict` (409) | Duplicate `external_id` | Use unique identifiers |
| `unauthorized` (401) | Invalid token | Regenerate access token (re-run `intercom-install-auth`) |

## Examples

- **Full five-step walkthrough** — create, search, message, converse, and tag,
  each with complete code and response shapes:
  [references/walkthrough.md](references/walkthrough.md).
- **Complete working script** — one runnable file that verifies the connection,
  creates a contact, and lists workspace contacts and conversations, with the
  expected console output: [references/complete-script.md](references/complete-script.md).

Both are copy-paste runnable once the Prerequisites above are met.

## Resources

- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Conversations API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations)
- [Messages API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/messages)
- [intercom-node GitHub](https://github.com/intercom/intercom-node)

## Next Steps

Proceed to the `intercom-local-dev-loop` skill to set up a fast local
development workflow (watch mode, sandbox workspace, and safe test data) once
this hello-world round trip succeeds.
