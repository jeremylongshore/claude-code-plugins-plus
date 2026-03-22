---
name: attio-hello-world
description: |
  Make your first Attio API calls -- list objects, create a person,
  query companies, and read attributes.
  Use when starting a new Attio integration or learning the API.
  Trigger: "attio hello world", "attio example", "first attio call",
  "attio quick start", "try attio API".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Hello World

## Overview

Five progressively deeper API calls that exercise the Attio object/record model. Every call targets `https://api.attio.com/v2` and returns JSON.

## Prerequisites

- Completed `attio-install-auth` (valid `ATTIO_API_KEY` in env)
- Scopes: `object_configuration:read`, `record_permission:read`, `record_permission:read-write`

## Instructions

### Step 1: List Workspace Objects

Every Attio workspace has system objects (people, companies) and optional objects (deals, users, workspaces). Custom objects can be created.

```bash
curl -s https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" | jq '.data[] | {slug: .api_slug, singular: .singular_noun}'
```

```json
{"slug": "people", "singular": "Person"}
{"slug": "companies", "singular": "Company"}
{"slug": "deals", "singular": "Deal"}
```

### Step 2: List Attributes on an Object

Objects have attributes (fields). Use the slug from Step 1.

```bash
curl -s "https://api.attio.com/v2/objects/people/attributes" \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" | jq '.data[] | {slug: .api_slug, type: .type}'
```

Common people attributes: `name` (personal-name), `email_addresses` (email-address), `phone_numbers` (phone-number), `description` (text), `primary_location` (location), `company` (record-reference).

### Step 3: Create a Person Record

```typescript
const person = await attioFetch<{ data: { id: { record_id: string } } }>({
  method: "POST",
  path: "/objects/people/records",
  body: {
    data: {
      values: {
        email_addresses: ["ada@example.com"],
        name: [
          {
            first_name: "Ada",
            last_name: "Lovelace",
            full_name: "Ada Lovelace",
          },
        ],
        description: ["First computer programmer"],
      },
    },
  },
});

console.log("Created person:", person.data.id.record_id);
```

**Key detail:** Values are keyed by attribute slug. Most attributes accept an array (Attio supports multiselect by default). String shortcuts work for emails and domains.

### Step 4: Query Records with Filters

```typescript
// List people whose email contains "example.com"
const results = await attioFetch<{
  data: Array<{ id: { record_id: string }; values: Record<string, any> }>;
}>({
  method: "POST",
  path: "/objects/people/records/query",
  body: {
    filter: {
      email_addresses: {
        email_address: { $contains: "example.com" },
      },
    },
    sorts: [
      {
        attribute: "created_at",
        field: "created_at",
        direction: "desc",
      },
    ],
    limit: 10,
  },
});

console.log(`Found ${results.data.length} people`);
```

### Step 5: Create a Company and Link It

```typescript
// Create company
const company = await attioFetch<{ data: { id: { record_id: string } } }>({
  method: "POST",
  path: "/objects/companies/records",
  body: {
    data: {
      values: {
        name: ["Acme Corp"],
        domains: ["acme.com"],
        description: ["Enterprise widget manufacturer"],
      },
    },
  },
});

// Update person to link to company via record-reference
await attioFetch({
  method: "PATCH",
  path: `/objects/people/records/${person.data.id.record_id}`,
  body: {
    data: {
      values: {
        company: [
          {
            target_object: "companies",
            target_record_id: company.data.id.record_id,
          },
        ],
      },
    },
  },
});
```

## Attio Data Model Quick Reference

```
Workspace
 └── Objects (people, companies, deals, custom)
      ├── Attributes (name, email, phone, custom)
      └── Records (individual people, companies)
           └── Values (attribute data on each record)

 └── Lists (pipelines, boards, custom groupings)
      └── Entries (records added to a list with list-specific attributes)
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `not_found` | 404 | Wrong object slug or record ID | Verify slug with `GET /v2/objects` |
| `validation_error` | 422 | Invalid attribute value format | Check attribute type in docs |
| `insufficient_scopes` | 403 | Token missing write scope | Add `record_permission:read-write` |
| `duplicate_record` | 409 | Record with same unique field exists | Use `PUT` (assert) instead |

## Resources

- [Attio Create Record](https://docs.attio.com/rest-api/endpoint-reference/records/create-a-record)
- [Attio List Records](https://docs.attio.com/rest-api/endpoint-reference/records/list-records)
- [Attio Attribute Types](https://docs.attio.com/docs/attribute-types/attribute-types)
- [Attio Slugs and IDs](https://docs.attio.com/docs/slugs-and-ids)

## Next Steps

Proceed to `attio-local-dev-loop` for development workflow, or `attio-core-workflow-a` for record CRUD patterns.
