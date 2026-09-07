# intercom-client v5 → v6 Migration Guide

The v6 SDK is a full TypeScript rewrite with a new API surface. This reference
holds the complete code diffs for every changed operation, plus the upgrade
procedure and type-import changes. Work through it after the high-level workflow
in `SKILL.md`.

## Client Initialization

```typescript
// v5 (CommonJS)
const Intercom = require("intercom-client");
const client = new Intercom.Client({ token: "xxx" });

// v6+ (TypeScript ESM)
import { IntercomClient } from "intercom-client";
const client = new IntercomClient({ token: "xxx" });
```

## Contact Operations

```typescript
// v5
await client.users.create({ email: "test@example.com" });
await client.leads.create({ email: "lead@example.com" });
await client.users.find({ id: "abc" });
await client.users.list();

// v6+ (unified contacts API)
await client.contacts.create({ role: "user", email: "test@example.com" });
await client.contacts.create({ role: "lead", email: "lead@example.com" });
await client.contacts.find({ contactId: "abc" });
await client.contacts.list();
```

## Conversation Operations

```typescript
// v5
await client.conversations.reply({ id: "123", body: "Hello", type: "admin", admin_id: "456" });

// v6+
await client.conversations.reply({
  conversationId: "123",
  body: "Hello",
  type: "admin",
  adminId: "456",
});
```

## Error Handling

```typescript
// v5
try { ... } catch (e) { console.log(e.statusCode, e.body); }

// v6+
import { IntercomError } from "intercom-client";
try { ... } catch (e) {
  if (e instanceof IntercomError) {
    console.log(e.statusCode, e.message, e.body);
  }
}
```

## Pagination

```typescript
// v5 - callback style
client.users.scroll.each({}, (users) => { /* ... */ });

// v6+ - async iteration
const response = await client.contacts.list();
for await (const contact of response) {
  // Auto-paginates
}

// Or manual cursor-based pagination
let startingAfter: string | undefined;
do {
  const page = await client.contacts.list({ perPage: 50, startingAfter });
  // process page.data
  startingAfter = page.pages?.next?.startingAfter ?? undefined;
} while (startingAfter);
```

## API Version Pinning

Intercom API versions control response shapes. The SDK defaults to a compatible
version, but you can pin explicitly.

```typescript
// Current stable version: 2.11
// SDK handles version headers automatically
// To use specific version via raw requests:
const response = await fetch("https://api.intercom.io/contacts", {
  headers: {
    Authorization: `Bearer ${token}`,
    "Intercom-Version": "2.11",
    "Content-Type": "application/json",
  },
});
```

## Upgrade Procedure

```bash
# 1. Create upgrade branch
git checkout -b upgrade/intercom-client-v6

# 2. Install new version
npm install intercom-client@latest

# 3. Run type checks (will surface breaking changes)
npx tsc --noEmit 2>&1 | grep "intercom"

# 4. Run tests
npm test

# 5. Fix breaking changes identified by TypeScript and tests

# 6. Test against dev workspace
INTERCOM_ACCESS_TOKEN=$DEV_TOKEN npm run test:integration

# 7. Commit and PR
git add -A && git commit -m "chore: upgrade intercom-client to v6"
```

## Type Import Changes

```typescript
// v6+ exports types under Intercom namespace
import { Intercom } from "intercom-client";

// Use typed request/response interfaces
const request: Intercom.CreateContactRequest = {
  role: "user",
  email: "test@example.com",
};

const contact: Intercom.Contact = await client.contacts.create(request);
```

## v5 → v6 Method Cheat Sheet

| v5 Method | v6 Method |
|-----------|-----------|
| `client.users.create()` | `client.contacts.create({ role: "user" })` |
| `client.leads.create()` | `client.contacts.create({ role: "lead" })` |
| `client.users.find({ id })` | `client.contacts.find({ contactId })` |
| `client.users.update({ id })` | `client.contacts.update({ contactId })` |
| `client.users.list()` | `client.contacts.list()` |
| `client.conversations.reply({ id })` | `client.conversations.reply({ conversationId })` |
| `client.events.create()` | `client.dataEvents.create()` |
| `client.tags.tag()` | `client.contacts.tag()` |
| `new Intercom.Client({ token })` | `new IntercomClient({ token })` |
| `e.statusCode` | `e instanceof IntercomError ? e.statusCode : ...` |
