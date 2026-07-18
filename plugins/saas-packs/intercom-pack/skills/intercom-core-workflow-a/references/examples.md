# Intercom Contacts — Worked Examples

End-to-end flows composed from the operations documented in
[implementation.md](implementation.md). Each example chains the same client calls
covered step-by-step there.

## Example 1: Lead-to-user lifecycle

An anonymous visitor lands on `/pricing`, is captured as a lead, later signs up,
and is merged into an identified user so their pre-signup history carries over.

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });

// 1. Capture the anonymous visitor as a lead
const lead = await client.contacts.create({
  role: "lead",
  email: "visitor@example.com",
  name: "Website Visitor",
  customAttributes: { landing_page: "/pricing", utm_source: "google" },
});

// 2. They sign up — create the identified user
const user = await client.contacts.create({
  role: "user",
  externalId: "customer-9001",
  email: "visitor@example.com",
  name: "Alice Johnson",
  customAttributes: { plan: "enterprise", signed_up_at: Math.floor(Date.now() / 1000) },
});

// 3. Merge the lead in — conversations, events, and tags transfer to the user
const merged = await client.contacts.merge({ from: lead.id, into: user.id });
console.log(`Merged lead into user: ${merged.id}`);
```

## Example 2: Segment enterprise signups from the last 30 days

Compound search + pagination to build a report of recent enterprise users.

```typescript
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

console.log(`Found ${filtered.totalCount} enterprise signups in the last 30 days`);
for (const contact of filtered.data) {
  console.log(`  ${contact.name} (${contact.email})`);
}
```

## Example 3: Stream every contact for an export

```typescript
async function* allContacts(client: IntercomClient) {
  let startingAfter: string | undefined;
  do {
    const page = await client.contacts.list({ perPage: 50, startingAfter });
    for (const contact of page.data) yield contact;
    startingAfter = page.pages?.next?.startingAfter ?? undefined;
  } while (startingAfter);
}

let count = 0;
for await (const contact of allContacts(client)) {
  count++;
  if (count % 100 === 0) console.log(`Processed ${count} contacts`);
}
```
