---
name: intercom-upgrade-migration
description: |
  Upgrade intercom-client SDK versions and handle API version changes.
  Use when upgrading the SDK, migrating between API versions,
  or detecting breaking changes in Intercom releases.
  Trigger with phrases like "upgrade intercom", "intercom migration",
  "intercom breaking changes", "update intercom SDK", "intercom API version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Upgrade & Migration

## Overview

Guide for upgrading the `intercom-client` npm package and handling Intercom API version changes. The SDK was rewritten in TypeScript starting at v6, which introduced significant breaking changes from the v5 CommonJS API.

## Prerequisites

- Current `intercom-client` installed
- Git for version control
- Test suite available

## Instructions

### Step 1: Check Current Versions

```bash
# Current SDK version
npm list intercom-client

# Latest available
npm view intercom-client version

# Current API version (check response headers)
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i intercom-version
```

### Step 2: SDK v5 to v6 Migration (Major Breaking Change)

The v6 SDK is a full TypeScript rewrite with a new API surface.

**Client Initialization:**

```typescript
// v5 (CommonJS)
const Intercom = require("intercom-client");
const client = new Intercom.Client({ token: "xxx" });

// v6+ (TypeScript ESM)
import { IntercomClient } from "intercom-client";
const client = new IntercomClient({ token: "xxx" });
```

**Contact Operations:**

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

**Conversation Operations:**

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

**Error Handling:**

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

**Pagination:**

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

### Step 3: API Version Pinning

Intercom API versions control response shapes. The SDK defaults to a compatible version, but you can pin explicitly.

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

### Step 4: Upgrade Procedure

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

### Step 5: Type Import Changes

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

## v5 to v6 Migration Cheat Sheet

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

## Error Handling

| Issue | Detection | Solution |
|-------|-----------|----------|
| `Cannot find module 'intercom-client'` | Import fails | `npm install intercom-client` |
| `Property 'users' does not exist` | TypeScript error | Migrate `users`/`leads` to `contacts` |
| `Property 'id' does not exist` | Changed param names | Use `contactId`, `conversationId` |
| Response shape changed | Runtime errors | Check API version headers |

## Resources

- [intercom-node GitHub](https://github.com/intercom/intercom-node)
- [SDK v6 Release Notes](https://github.com/intercom/intercom-node/discussions/416)
- [API Versioning](https://developers.intercom.com/docs/references/introduction)
- [intercom-client npm](https://www.npmjs.com/package/intercom-client)

## Next Steps

For CI integration during upgrades, see `intercom-ci-integration`.
