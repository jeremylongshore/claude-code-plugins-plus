# Intercom Hello World — Complete Working Script

A single runnable file that verifies your connection, creates a contact, and
lists workspace contacts and conversations. Drop it into a TypeScript project
with `intercom-client` installed and `INTERCOM_ACCESS_TOKEN` set, then run it.
It is the end-to-end smoke test for a fresh Intercom integration.

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

## Expected console output

```
Authenticated as: Jane Admin
Contact: 6657add46abd0167d9419c3a
Total contacts in workspace: 1
Total conversations: 0
```

The exact IDs and counts vary by workspace; the point is that all four calls
return without throwing. A throw on step 1 means the token is wrong (see the
Error Handling table in `SKILL.md`); a throw on later steps means a scope or
permission gap on the access token.
