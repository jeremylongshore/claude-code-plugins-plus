---
name: attio-core-workflow-a
description: |
  Full CRUD on Attio records -- create, read, update, delete, and search
  across people, companies, deals, and custom objects.
  Trigger: "attio records", "attio CRUD", "create attio record",
  "update attio person", "search attio companies", "attio objects".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Records CRUD (Core Workflow A)

## Overview

Complete record lifecycle on the Attio REST API. Records are instances of objects (people, companies, deals, custom). Values are keyed by attribute slug and are always arrays (Attio supports multiselect natively).

## Prerequisites

- `attio-install-auth` completed
- Scopes: `object_configuration:read`, `record_permission:read`, `record_permission:read-write`
- Understanding of Attio attribute types (see reference table below)

## Attio Attribute Type Reference

| Type | Slug example | Value format |
|------|-------------|-------------|
| `text` | `description` | `"plain string"` |
| `number` | `revenue` | `123456` |
| `email-address` | `email_addresses` | `"ada@example.com"` (string shortcut) |
| `phone-number` | `phone_numbers` | `{ original_phone_number: "+14155551234" }` |
| `domain` | `domains` | `"acme.com"` (string shortcut) |
| `personal-name` | `name` | `{ first_name, last_name, full_name }` |
| `location` | `primary_location` | `"San Francisco, CA"` (string shortcut) |
| `record-reference` | `company` | `{ target_object: "companies", target_record_id: "..." }` |
| `select` / `status` | `stage` | `{ option: "qualified" }` |
| `currency` | `deal_value` | `{ currency_code: "USD", currency_value: 50000 }` |
| `checkbox` | `is_active` | `true` / `false` |
| `date` | `close_date` | `"2025-06-15"` |
| `timestamp` | `last_contact` | `"2025-06-15T14:30:00.000Z"` |
| `rating` | `priority` | `4` (integer 1-5) |

## Instructions

### Step 1: Create Records

```typescript
// Create a person
const person = await client.post<{ data: AttioRecord }>(
  "/objects/people/records",
  {
    data: {
      values: {
        email_addresses: ["ada@example.com"],
        name: [{ first_name: "Ada", last_name: "Lovelace", full_name: "Ada Lovelace" }],
        phone_numbers: [{ original_phone_number: "+14155551234" }],
        primary_location: ["London, UK"],
        description: ["Mathematician and first programmer"],
      },
    },
  }
);

// Create a company
const company = await client.post<{ data: AttioRecord }>(
  "/objects/companies/records",
  {
    data: {
      values: {
        name: ["Babbage Analytical Engines"],
        domains: ["babbage.io"],
        description: ["Mechanical computing pioneer"],
        primary_location: ["London, UK"],
      },
    },
  }
);
```

### Step 2: Read a Single Record

```typescript
// GET /v2/objects/{object_slug}/records/{record_id}
const record = await client.get<{ data: AttioRecord }>(
  `/objects/people/records/${person.data.id.record_id}`
);

// Access values (always arrays)
const fullName = record.data.values.name?.[0]?.full_name;
const email = record.data.values.email_addresses?.[0]?.email_address;
```

### Step 3: Update Records (PATCH vs PUT)

```typescript
// PATCH: Append to multiselect values
await client.patch<{ data: AttioRecord }>(
  `/objects/people/records/${recordId}`,
  {
    data: {
      values: {
        email_addresses: ["ada.new@example.com"], // Adds to existing emails
      },
    },
  }
);

// PUT: Overwrite (assert) -- replaces all values for specified attributes
await client.put<{ data: AttioRecord }>(
  `/objects/people/records/${recordId}`,
  {
    data: {
      values: {
        email_addresses: ["only-this@example.com"], // Replaces all emails
      },
    },
  }
);
```

### Step 4: Query with Filters and Sorts

```typescript
// POST /v2/objects/{object}/records/query
const results = await client.post<{ data: AttioRecord[] }>(
  "/objects/companies/records/query",
  {
    // Shorthand filter (equality check)
    filter: {
      domains: "acme.com",
    },
    limit: 25,
  }
);

// Verbose filter with operators
const filtered = await client.post<{ data: AttioRecord[] }>(
  "/objects/people/records/query",
  {
    filter: {
      $and: [
        { email_addresses: { email_address: { $contains: "example.com" } } },
        { name: { last_name: { $eq: "Lovelace" } } },
      ],
    },
    sorts: [
      { attribute: "created_at", field: "created_at", direction: "desc" },
    ],
    limit: 50,
    offset: 0,
  }
);
```

**Available filter operators:** `$eq`, `$not_empty`, `$contains`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$and`, `$or`.

### Step 5: Fuzzy Search Across Objects

```typescript
// POST /v2/records/search -- searches across all objects
const search = await client.post<{ data: AttioRecord[] }>(
  "/records/search",
  {
    query: "Ada Lovelace",
    limit: 10,
  }
);
```

### Step 6: Delete a Record

```typescript
// DELETE /v2/objects/{object}/records/{record_id}
await client.delete(`/objects/people/records/${recordId}`);
```

### Step 7: Link Records via Record-Reference

```typescript
// Link a person to a company
await client.patch<{ data: AttioRecord }>(
  `/objects/people/records/${personId}`,
  {
    data: {
      values: {
        company: [{
          target_object: "companies",
          target_record_id: companyId,
        }],
      },
    },
  }
);
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `not_found` | 404 | Invalid object slug or record ID | Verify with `GET /v2/objects` |
| `validation_error` | 422 | Wrong value format for attribute type | Check attribute type table above |
| `rate_limit_exceeded` | 429 | Exceeded 10-second sliding window | Honor `Retry-After` header |
| `conflict` | 409 | Duplicate on unique attribute | Use PUT (assert/upsert) |
| `insufficient_scopes` | 403 | Missing `record_permission:read-write` | Update token scopes |

## Resources

- [Attio Create Record](https://docs.attio.com/rest-api/endpoint-reference/records/create-a-record)
- [Attio List Records](https://docs.attio.com/rest-api/endpoint-reference/records/list-records)
- [Attio Search Records](https://docs.attio.com/rest-api/endpoint-reference/records/search-records)
- [Attio Filtering and Sorting](https://docs.attio.com/rest-api/how-to/filtering-and-sorting)
- [Attio Attribute Types](https://docs.attio.com/docs/attribute-types/attribute-types)

## Next Steps

For list/entry operations (pipelines, boards), see `attio-core-workflow-b`.
