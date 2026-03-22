---
name: attio-upgrade-migration
description: |
  Migrate between Attio API versions, handle breaking changes in the
  v1-to-v2 transition, and plan for future deprecations.
  Trigger: "upgrade attio", "attio migration", "attio v1 to v2",
  "attio breaking changes", "attio API version", "attio deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Upgrade & Migration

## Overview

Attio has two API generations: v1 (legacy, deprecated) and v2 (current). This skill covers the v1-to-v2 migration, community SDK upgrade paths, and how to detect and adapt to API changes since Attio does not publish a traditional SDK changelog.

## V1 to V2 Migration Reference

### Endpoint Changes

| Operation | V1 Endpoint | V2 Endpoint |
|-----------|------------|------------|
| List objects | `GET /v1/objects` | `GET /v2/objects` |
| Query records | `GET /v1/objects/{id}/records` | `POST /v2/objects/{slug}/records/query` |
| Create record | `POST /v1/objects/{id}/records` | `POST /v2/objects/{slug}/records` |
| Get record | `GET /v1/objects/{id}/records/{rid}` | `GET /v2/objects/{slug}/records/{rid}` |
| List entries | `GET /v1/lists/{id}/entries` | `POST /v2/lists/{slug}/entries/query` |
| Create webhook | `POST /v1/webhooks` | `POST /v2/webhooks` |
| Search | N/A | `POST /v2/records/search` |

### Key Differences

| Aspect | V1 | V2 |
|--------|----|----|
| Identifiers | UUIDs only | Slugs (preferred) or UUIDs |
| Record query | GET with query params | POST with JSON body (filters, sorts) |
| Filtering | Basic query params | Rich operators (`$eq`, `$contains`, `$gt`, `$and`, `$or`) |
| Pagination | `page` + `per_page` | `limit` + `offset` or cursor-based |
| Webhook payloads | Custom format | Consistent with v2 response shapes |
| Webhook filtering | None | Event-type and attribute-level filters |

### Step 1: Update Base URL

```typescript
// Before
const BASE = "https://api.attio.com/v1";

// After
const BASE = "https://api.attio.com/v2";
```

### Step 2: Migrate Record Queries

```typescript
// V1: GET with query params
const v1 = await fetch(
  `${BASE}/objects/${objectId}/records?page=1&per_page=50`,
  { headers: { Authorization: `Bearer ${token}` } }
);

// V2: POST with filter body, using slug instead of UUID
const v2 = await fetch(
  `${BASE}/objects/people/records/query`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filter: {
        email_addresses: { email_address: { $contains: "@example.com" } },
      },
      sorts: [{ attribute: "created_at", field: "created_at", direction: "desc" }],
      limit: 50,
      offset: 0,
    }),
  }
);
```

### Step 3: Update Record Creation

```typescript
// V1: values as flat key-value pairs
const v1Body = {
  name: "Ada Lovelace",
  email: "ada@example.com",
};

// V2: values nested under data.values, always arrays
const v2Body = {
  data: {
    values: {
      name: [{ first_name: "Ada", last_name: "Lovelace", full_name: "Ada Lovelace" }],
      email_addresses: ["ada@example.com"],
    },
  },
};
```

### Step 4: Migrate Webhooks from V1 to V2

```typescript
// V1 webhook event types
"object.record.created"

// V2 webhook event types
"record.created"
"record.updated"
"record.deleted"
"record.merged"
"list-entry.created"
"note.created"
"task.created"
// ... plus filtering support
```

V2 webhooks support event filtering to reduce volume:
```typescript
await client.post("/webhooks", {
  target_url: "https://yourapp.com/webhooks/attio",
  subscriptions: [
    {
      event_type: "record.updated",
      filter: {
        // Only trigger for updates to the "stage" attribute on deals
        $and: [
          { object: { $eq: "deals" } },
          { attribute: { $eq: "stage" } },
        ],
      },
    },
  ],
});
```

## Community SDK Migration

Since there is no official Attio SDK, you may be using community packages:

### attio-js (most popular community SDK)

```bash
# Check current version
npm list attio-js

# Upgrade
npm install attio-js@latest
```

```typescript
// attio-js uses the v2 API natively
import { AttioClient } from "attio-js";

const client = new AttioClient({ accessToken: process.env.ATTIO_API_KEY });
const people = await client.records.query("people", { limit: 10 });
```

### Direct fetch (recommended for control)

No upgrade risk -- you control the endpoint URLs directly. See `attio-sdk-patterns` for a typed wrapper.

## Detecting API Changes

Attio does not publish a traditional changelog for the REST API. Monitor for changes:

```typescript
// Save the OpenAPI spec hash and check periodically
import crypto from "crypto";

async function checkForApiChanges(): Promise<boolean> {
  const spec = await fetch("https://docs.attio.com/openapi.json").then(r => r.text());
  const hash = crypto.createHash("sha256").update(spec).digest("hex");

  const previousHash = await readStoredHash(); // From file or DB
  if (previousHash && hash !== previousHash) {
    console.warn("Attio OpenAPI spec changed! Review for breaking changes.");
    await storeHash(hash);
    return true;
  }
  await storeHash(hash);
  return false;
}
```

## Migration Checklist

```
[ ] Base URL updated to /v2
[ ] Object references use slugs instead of UUIDs where possible
[ ] Record queries migrated from GET to POST with filter body
[ ] Record creation uses data.values wrapper with arrays
[ ] Webhook subscriptions recreated with v2 event types
[ ] Webhook handlers updated for v2 payload format
[ ] Pagination migrated from page/per_page to limit/offset
[ ] Error handling updated for v2 error response format
[ ] Tests updated and passing against v2 endpoints
[ ] OpenAPI spec monitoring configured for future changes
```

## Error Handling

| Migration issue | Symptom | Fix |
|----------------|---------|-----|
| Old v1 URL | 404 on all calls | Update base URL to `/v2` |
| UUID instead of slug | 404 on object endpoints | Use `api_slug` from `GET /v2/objects` |
| Flat values (v1 format) | 422 validation error | Wrap in `{ data: { values: { ... } } }` |
| Old webhook event types | Webhook never fires | Recreate with v2 event types |
| Old pagination params | Ignored, only first page returned | Switch to `limit` + `offset` |

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio OpenAPI Spec](https://docs.attio.com/rest-api/endpoint-reference/openapi)
- [Attio Slugs and IDs](https://docs.attio.com/docs/slugs-and-ids)
- [attio-js on GitHub](https://github.com/d-stoll/attio-js)

## Next Steps

For CI integration during upgrades, see `attio-ci-integration`.
