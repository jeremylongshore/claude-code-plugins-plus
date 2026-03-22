---
name: hubspot-hello-world
description: |
  Create a working HubSpot CRM example with contacts, companies, and deals.
  Use when starting a new HubSpot integration, testing your setup,
  or learning basic CRM API patterns with real endpoints.
  Trigger with phrases like "hubspot hello world", "hubspot example",
  "hubspot quick start", "first hubspot API call", "hubspot contact create".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Hello World

## Overview

Create, read, update, and delete CRM records using the HubSpot API. Covers contacts, companies, and deals with real endpoints and SDK methods.

## Prerequisites

- Completed `hubspot-install-auth` setup
- Private app with scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`
- `@hubspot/api-client` installed

## Instructions

### Step 1: Create a Contact

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
});

// POST /crm/v3/objects/contacts
const contactResponse = await client.crm.contacts.basicApi.create({
  properties: {
    firstname: 'Jane',
    lastname: 'Doe',
    email: 'jane.doe@example.com',
    phone: '(555) 123-4567',
    company: 'Acme Corp',
    lifecyclestage: 'lead',
  },
  associations: [],
});

console.log(`Created contact: ${contactResponse.id}`);
// Output: Created contact: 12345
```

### Step 2: Read a Contact

```typescript
// GET /crm/v3/objects/contacts/{contactId}
const contact = await client.crm.contacts.basicApi.getById(
  contactResponse.id,
  ['firstname', 'lastname', 'email', 'phone', 'lifecyclestage'],
  undefined, // propertiesWithHistory
  ['companies'] // associations to include
);

console.log(`${contact.properties.firstname} ${contact.properties.lastname}`);
console.log(`Email: ${contact.properties.email}`);
console.log(`Stage: ${contact.properties.lifecyclestage}`);
```

### Step 3: Update a Contact

```typescript
// PATCH /crm/v3/objects/contacts/{contactId}
const updated = await client.crm.contacts.basicApi.update(
  contactResponse.id,
  {
    properties: {
      lifecyclestage: 'marketingqualifiedlead',
      phone: '(555) 987-6543',
    },
  }
);

console.log(`Updated at: ${updated.updatedAt}`);
```

### Step 4: Create a Company and Associate

```typescript
// POST /crm/v3/objects/companies
const company = await client.crm.companies.basicApi.create({
  properties: {
    name: 'Acme Corp',
    domain: 'acme.com',
    industry: 'TECHNOLOGY',
    numberofemployees: '150',
    annualrevenue: '5000000',
  },
  associations: [],
});

// Associate contact with company
// PUT /crm/v4/objects/contacts/{contactId}/associations/companies/{companyId}
await client.crm.associations.v4.basicApi.create(
  'contacts',
  contactResponse.id,
  'companies',
  company.id,
  [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 1 }]
);

console.log(`Associated contact ${contactResponse.id} with company ${company.id}`);
```

### Step 5: Create a Deal

```typescript
// POST /crm/v3/objects/deals
const deal = await client.crm.deals.basicApi.create({
  properties: {
    dealname: 'Acme Enterprise License',
    amount: '50000',
    dealstage: 'appointmentscheduled', // default pipeline stage ID
    pipeline: 'default',
    closedate: '2026-06-30T00:00:00.000Z',
    hubspot_owner_id: '12345', // owner user ID
  },
  associations: [
    {
      to: { id: company.id },
      types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 5 }],
    },
    {
      to: { id: contactResponse.id },
      types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 3 }],
    },
  ],
});

console.log(`Created deal: ${deal.properties.dealname} ($${deal.properties.amount})`);
```

## Output

- Created contact with properties and lifecycle stage
- Read contact with specific properties and associations
- Updated contact properties
- Created company and associated it with the contact
- Created deal associated with both contact and company

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `409 Conflict` | 409 | Contact with email already exists | Use `crm.contacts.basicApi.getById` or search first |
| `400 Bad Request` | 400 | Invalid property name or value | Check property names in Settings > Properties |
| `404 Not Found` | 404 | Record ID doesn't exist | Verify ID or check if archived |
| `PROPERTY_DOESNT_EXIST` | 400 | Custom property not created | Create in Settings > Properties first |

## Examples

### Search for Existing Contacts

```typescript
// POST /crm/v3/objects/contacts/search
const searchResults = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [
    {
      filters: [
        {
          propertyName: 'email',
          operator: 'EQ',
          value: 'jane.doe@example.com',
        },
      ],
    },
  ],
  properties: ['firstname', 'lastname', 'email'],
  limit: 10,
  after: 0,
  sorts: [{ propertyName: 'createdate', direction: 'DESCENDING' }],
});

console.log(`Found ${searchResults.total} contact(s)`);
```

### Delete (Archive) a Record

```typescript
// DELETE /crm/v3/objects/contacts/{contactId}
await client.crm.contacts.basicApi.archive(contactResponse.id);
console.log('Contact archived');
```

## Resources

- [Contacts API Guide](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts)
- [Companies API Guide](https://developers.hubspot.com/docs/guides/api/crm/objects/companies)
- [Deals API Guide](https://developers.hubspot.com/docs/guides/api/crm/objects/deals)
- [Associations v4 API](https://developers.hubspot.com/docs/guides/api/crm/associations)

## Next Steps

Proceed to `hubspot-local-dev-loop` for development workflow setup.
