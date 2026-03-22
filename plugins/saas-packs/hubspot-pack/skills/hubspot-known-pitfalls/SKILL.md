---
name: hubspot-known-pitfalls
description: |
  Identify and avoid HubSpot API anti-patterns and common integration mistakes.
  Use when reviewing HubSpot code, onboarding developers to HubSpot integrations,
  or auditing existing CRM integrations for best practice violations.
  Trigger with phrases like "hubspot mistakes", "hubspot anti-patterns",
  "hubspot pitfalls", "hubspot code review", "hubspot gotchas".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Known Pitfalls

## Overview

Ten real-world HubSpot API anti-patterns with correct alternatives, covering authentication, rate limits, search, associations, and data handling.

## Prerequisites

- Access to HubSpot integration codebase
- Understanding of HubSpot CRM v3 API

## Instructions

### Pitfall 1: Using Deprecated API Keys

```typescript
// BAD: API keys were deprecated in 2022 and removed from SDK v10+
const client = new hubspot.Client({ apiKey: 'your-api-key' }); // REMOVED

// GOOD: Use private app access token
const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!, // pat-na1-xxxxx
  numberOfApiCallRetries: 3,
});
```

---

### Pitfall 2: Not Using Batch Operations

```typescript
// BAD: N API calls to read N contacts (hits rate limit fast)
for (const id of contactIds) {
  const contact = await client.crm.contacts.basicApi.getById(id, ['email']);
  // 100 contacts = 100 API calls
}

// GOOD: 1 API call for up to 100 contacts
const batch = await client.crm.contacts.batchApi.read({
  inputs: contactIds.map(id => ({ id })),
  properties: ['email', 'firstname'],
  propertiesWithHistory: [],
});
// 100 contacts = 1 API call
```

---

### Pitfall 3: Ignoring Search Limits

```typescript
// BAD: Search API has a hard limit of 10,000 results total
// You cannot page past this limit with `after`
const allResults = [];
let after = 0;
do {
  const page = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [], properties: ['email'], limit: 100, after, sorts: [],
  });
  allResults.push(...page.results);
  after = page.paging?.next?.after;
} while (after); // STOPS at 10,000 regardless

// GOOD: Use getPage for full exports (no 10K limit)
async function* getAllContacts(properties: string[]) {
  let after: string | undefined;
  do {
    const page = await client.crm.contacts.basicApi.getPage(100, after, properties);
    yield* page.results;
    after = page.paging?.next?.after;
  } while (after); // No upper limit
}
```

---

### Pitfall 4: Wrong Association Type IDs

```typescript
// BAD: Guessing association type IDs
await client.crm.associations.v4.basicApi.create(
  'contacts', contactId, 'companies', companyId,
  [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 999 }] // wrong ID!
);
// Error: "association type id 999 doesn't exist between contact and company"

// GOOD: Use documented default type IDs
const ASSOC_TYPES = {
  CONTACT_TO_COMPANY: 1,    // Primary company
  CONTACT_TO_DEAL: 3,
  COMPANY_TO_DEAL: 5,
  CONTACT_TO_TICKET: 16,
  NOTE_TO_CONTACT: 202,
  TASK_TO_CONTACT: 204,
  NOTE_TO_DEAL: 214,
};

await client.crm.associations.v4.basicApi.create(
  'contacts', contactId, 'companies', companyId,
  [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: ASSOC_TYPES.CONTACT_TO_COMPANY }]
);

// Or look up dynamically:
// GET /crm/v4/associations/contacts/companies/labels
```

---

### Pitfall 5: Creating Duplicate Contacts

```typescript
// BAD: Create without checking if contact exists
await client.crm.contacts.basicApi.create({
  properties: { email: 'jane@example.com', firstname: 'Jane' },
  associations: [],
});
// If jane@example.com exists: 409 Conflict error

// GOOD: Search first, then create or update
async function upsertContact(email: string, props: Record<string, string>) {
  const existing = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
    }],
    properties: ['email'], limit: 1, after: 0, sorts: [],
  });

  if (existing.results.length > 0) {
    return client.crm.contacts.basicApi.update(existing.results[0].id, { properties: props });
  }
  return client.crm.contacts.basicApi.create({
    properties: { email, ...props },
    associations: [],
  });
}

// BETTER: Use batch upsert (single API call)
await client.apiRequest({
  method: 'POST',
  path: '/crm/v3/objects/contacts/batch/upsert',
  body: {
    inputs: [{ properties: { email: 'jane@example.com', firstname: 'Jane' }, idProperty: 'email', id: 'jane@example.com' }],
  },
});
```

---

### Pitfall 6: Requesting All Properties

```typescript
// BAD: No properties specified = returns ALL default properties
const contact = await client.crm.contacts.basicApi.getById('123');
// Returns ~50+ properties you don't need, slower response

// GOOD: Request only what you need
const contact = await client.crm.contacts.basicApi.getById('123', [
  'email', 'firstname', 'lastname', 'lifecyclestage',
]);
// Returns only 4 properties, faster response
```

---

### Pitfall 7: Hardcoding Pipeline Stage IDs

```typescript
// BAD: Stage IDs are portal-specific, not universal
const deal = await client.crm.deals.basicApi.create({
  properties: {
    dealname: 'New Deal',
    dealstage: 'appointmentscheduled', // this default ID might not exist
    pipeline: 'default',               // might not be called "default"
  },
  associations: [],
});

// GOOD: Fetch pipelines first, then use IDs
const pipelines = await client.crm.pipelines.pipelinesApi.getAll('deals');
const salesPipeline = pipelines.results[0]; // or find by label
const firstStage = salesPipeline.stages.sort(
  (a, b) => Number(a.displayOrder) - Number(b.displayOrder)
)[0];

const deal = await client.crm.deals.basicApi.create({
  properties: {
    dealname: 'New Deal',
    dealstage: firstStage.id,
    pipeline: salesPipeline.id,
  },
  associations: [],
});
```

---

### Pitfall 8: Not Handling 409 Conflict on Associations

```typescript
// BAD: Creating association without checking if it exists
// (Some association types allow only one, e.g., primary company)
try {
  await client.crm.associations.v4.basicApi.create(
    'contacts', contactId, 'companies', companyId,
    [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 1 }]
  );
} catch (error) {
  // 409: Association already exists -- this is actually OK!
  // Don't treat as error
}

// GOOD: Catch 409 gracefully
async function ensureAssociation(
  fromType: string, fromId: string, toType: string, toId: string, typeId: number
) {
  try {
    await client.crm.associations.v4.basicApi.create(
      fromType, fromId, toType, toId,
      [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: typeId }]
    );
  } catch (error: any) {
    if (error?.code !== 409) throw error;
    // Association already exists -- idempotent success
  }
}
```

---

### Pitfall 9: Polling Instead of Using Webhooks

```typescript
// BAD: Polling for changes wastes API calls
setInterval(async () => {
  const updated = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{
        propertyName: 'lastmodifieddate',
        operator: 'GTE',
        value: String(Date.now() - 60000),
      }],
    }],
    properties: ['email'], limit: 100, after: 0, sorts: [],
  });
  processChanges(updated.results);
}, 60000); // 1,440 API calls/day just for polling

// GOOD: Use webhooks (0 API calls for change detection)
// Set up webhook subscription in your HubSpot public app for:
// - contact.propertyChange
// - deal.propertyChange
// - contact.creation
// See hubspot-webhooks-events skill
```

---

### Pitfall 10: Using the Wrong API Endpoint Version

```typescript
// BAD: Using legacy v1/v2 endpoints
const response = await fetch(
  `https://api.hubapi.com/contacts/v1/contact/email/${email}/profile`,
  { headers: { Authorization: `Bearer ${token}` } }
);
// Legacy endpoints may be deprecated and have different auth requirements

// GOOD: Use CRM v3 API with the SDK
const result = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
  }],
  properties: ['firstname', 'lastname', 'email'],
  limit: 1, after: 0, sorts: [],
});
```

## Quick Scan Commands

```bash
# Detect these pitfalls in your codebase
grep -rn "apiKey:" src/ --include="*.ts"                    # Pitfall 1
grep -rn "basicApi.getById" src/ | wc -l                   # Pitfall 2 (if > 10, use batch)
grep -rn "contacts/v1\|deals/v1\|companies/v2" src/        # Pitfall 10
grep -rn "setInterval.*hubspot\|setInterval.*crm" src/     # Pitfall 9
grep -rn "pat-na1-" src/ --include="*.ts" --include="*.js" # Token leak
```

## Quick Reference Card

| Pitfall | Detection | Fix |
|---------|-----------|-----|
| Deprecated API keys | `grep "apiKey:"` | Use `accessToken` |
| No batching | Many `getById` calls | Use `batchApi.read` |
| Search > 10K | Search with `after` past 10K | Use `getPage` |
| Wrong association IDs | 400 errors on associate | Use documented type IDs |
| Duplicate contacts | 409 on create | Search first or batch upsert |
| All properties | No `properties` param | Specify needed fields |
| Hardcoded stage IDs | Stage not found errors | Fetch pipelines dynamically |
| Association conflict | 409 on associate | Catch and ignore 409 |
| Polling for changes | High API call volume | Use webhooks |
| Legacy API versions | `/v1/` or `/v2/` URLs | Use CRM v3 SDK |

## Resources

- [CRM API Guide](https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm)
- [Batch Operations](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts)
- [Search API Limits](https://developers.hubspot.com/docs/guides/api/crm/search)
- [Association Types](https://developers.hubspot.com/docs/guides/api/crm/associations)
