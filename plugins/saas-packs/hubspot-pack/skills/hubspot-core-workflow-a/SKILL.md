---
name: hubspot-core-workflow-a
description: |
  Build a complete HubSpot CRM contact-to-deal pipeline workflow.
  Use when implementing lead capture, contact management, deal creation,
  or end-to-end sales pipeline automation with HubSpot.
  Trigger with phrases like "hubspot sales pipeline", "hubspot lead workflow",
  "hubspot contact to deal", "hubspot CRM automation", "hubspot pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Core Workflow A: Contact-to-Deal Pipeline

## Overview

End-to-end workflow: capture a lead, create/update contact, create company, create deal in pipeline, advance deal stages, and log activities. The primary money-path workflow for HubSpot CRM.

## Prerequisites

- Completed `hubspot-install-auth` setup
- Scopes: `crm.objects.contacts.write`, `crm.objects.companies.write`, `crm.objects.deals.write`
- Understanding of your HubSpot deal pipeline and stages

## Instructions

### Step 1: Capture and Upsert Contact

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

interface LeadInput {
  email: string;
  firstName: string;
  lastName: string;
  company: string;
  phone?: string;
  source?: string;
}

async function upsertContact(lead: LeadInput): Promise<string> {
  // Search for existing contact by email
  // POST /crm/v3/objects/contacts/search
  const existing = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{ propertyName: 'email', operator: 'EQ', value: lead.email }],
    }],
    properties: ['firstname', 'lastname', 'email'],
    limit: 1,
    after: 0,
    sorts: [],
  });

  if (existing.results.length > 0) {
    // Update existing contact
    const contactId = existing.results[0].id;
    await client.crm.contacts.basicApi.update(contactId, {
      properties: {
        firstname: lead.firstName,
        lastname: lead.lastName,
        phone: lead.phone || '',
        hs_lead_status: 'NEW',
      },
    });
    console.log(`Updated existing contact: ${contactId}`);
    return contactId;
  }

  // Create new contact
  const contact = await client.crm.contacts.basicApi.create({
    properties: {
      email: lead.email,
      firstname: lead.firstName,
      lastname: lead.lastName,
      company: lead.company,
      phone: lead.phone || '',
      lifecyclestage: 'lead',
      hs_lead_status: 'NEW',
    },
    associations: [],
  });
  console.log(`Created new contact: ${contact.id}`);
  return contact.id;
}
```

### Step 2: Find or Create Company

```typescript
async function findOrCreateCompany(
  domain: string,
  name: string
): Promise<string> {
  // Search by domain
  const existing = await client.crm.companies.searchApi.doSearch({
    filterGroups: [{
      filters: [{ propertyName: 'domain', operator: 'EQ', value: domain }],
    }],
    properties: ['name', 'domain'],
    limit: 1,
    after: 0,
    sorts: [],
  });

  if (existing.results.length > 0) {
    return existing.results[0].id;
  }

  const company = await client.crm.companies.basicApi.create({
    properties: { name, domain },
    associations: [],
  });
  return company.id;
}
```

### Step 3: Create Deal in Pipeline

```typescript
async function createDeal(
  contactId: string,
  companyId: string,
  dealName: string,
  amount: number
): Promise<string> {
  // First, get pipeline stages to find the right stage ID
  // GET /crm/v3/pipelines/deals
  const pipelines = await client.crm.pipelines.pipelinesApi.getAll('deals');
  const defaultPipeline = pipelines.results.find(p => p.label === 'Sales Pipeline')
    || pipelines.results[0];
  const firstStage = defaultPipeline.stages.sort(
    (a, b) => Number(a.displayOrder) - Number(b.displayOrder)
  )[0];

  // POST /crm/v3/objects/deals
  const deal = await client.crm.deals.basicApi.create({
    properties: {
      dealname: dealName,
      amount: String(amount),
      pipeline: defaultPipeline.id,
      dealstage: firstStage.id,
      closedate: new Date(Date.now() + 30 * 86400000).toISOString(),
    },
    associations: [
      {
        to: { id: contactId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 3 }],
      },
      {
        to: { id: companyId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 5 }],
      },
    ],
  });

  console.log(`Created deal: ${deal.id} in stage "${firstStage.label}"`);
  return deal.id;
}
```

### Step 4: Advance Deal Stage

```typescript
async function advanceDealStage(dealId: string, stageName: string): Promise<void> {
  // Look up stage ID from pipeline
  const deal = await client.crm.deals.basicApi.getById(dealId, ['pipeline', 'dealstage']);
  const pipelines = await client.crm.pipelines.pipelinesApi.getAll('deals');
  const pipeline = pipelines.results.find(p => p.id === deal.properties.pipeline);
  const targetStage = pipeline?.stages.find(s => s.label === stageName);

  if (!targetStage) {
    throw new Error(`Stage "${stageName}" not found in pipeline "${pipeline?.label}"`);
  }

  await client.crm.deals.basicApi.update(dealId, {
    properties: { dealstage: targetStage.id },
  });
  console.log(`Deal ${dealId} moved to "${stageName}"`);
}
```

### Step 5: Log Activity (Note)

```typescript
async function logNote(contactId: string, dealId: string, body: string): Promise<void> {
  // POST /crm/v3/objects/notes
  await client.crm.objects.notes.basicApi.create({
    properties: {
      hs_note_body: body,
      hs_timestamp: new Date().toISOString(),
    },
    associations: [
      {
        to: { id: contactId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 202 }],
      },
      {
        to: { id: dealId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 214 }],
      },
    ],
  });
}
```

### Complete Pipeline Example

```typescript
async function processLead(lead: LeadInput) {
  const contactId = await upsertContact(lead);
  const domain = lead.email.split('@')[1];
  const companyId = await findOrCreateCompany(domain, lead.company);

  // Associate contact with company
  await client.crm.associations.v4.basicApi.create(
    'contacts', contactId, 'companies', companyId,
    [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 1 }]
  );

  const dealId = await createDeal(
    contactId, companyId,
    `${lead.company} - New Opportunity`,
    10000
  );

  await logNote(contactId, dealId, `Lead captured from ${lead.source || 'website'}`);

  return { contactId, companyId, dealId };
}
```

## Output

- Contact upserted (create or update based on email)
- Company found or created by domain
- Deal created in the correct pipeline stage with associations
- Deal stage advanced through the pipeline
- Activity note logged on contact and deal

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `409 Conflict` | 409 | Duplicate email on create | Use search-then-create pattern above |
| `PIPELINE_STAGE_NOT_FOUND` | 400 | Invalid stage ID | Fetch pipeline stages first |
| `INVALID_ASSOCIATION_TYPE` | 400 | Wrong `associationTypeId` | Check default association types |
| `PROPERTY_DOESNT_EXIST` | 400 | Custom property not created | Create in HubSpot Settings > Properties |

## Resources

- [Deals API Guide](https://developers.hubspot.com/docs/guides/api/crm/objects/deals)
- [Pipelines API](https://developers.hubspot.com/docs/reference/api/crm/pipelines)
- [Associations v4 Default Types](https://developers.hubspot.com/docs/guides/api/crm/associations)
- [Engagements (Notes) API](https://developers.hubspot.com/docs/guides/api/crm/engagements/notes)

## Next Steps

For marketing automation workflows, see `hubspot-core-workflow-b`.
