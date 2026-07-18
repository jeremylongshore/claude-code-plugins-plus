# Intercom Contacts — Full Implementation Walkthrough

Complete, step-by-step code for every contact operation. SKILL.md carries the lean
skeleton and the first example; this file is the full depth you drill into for each step.

## Step 1: Create Contacts

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

## Step 2: Search Contacts

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

## Step 3: Update a Contact

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

## Step 4: Merge a Lead into a User

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

## Step 5: List Segments for a Contact

```typescript
const segments = await client.contacts.listSegments({
  contactId: user.id,
});

for (const segment of segments.data) {
  console.log(`Segment: ${segment.name} (${segment.id})`);
}
```

## Step 6: Paginate All Contacts

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
