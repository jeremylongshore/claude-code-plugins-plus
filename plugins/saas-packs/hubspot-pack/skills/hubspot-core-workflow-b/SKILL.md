---
name: hubspot-core-workflow-b
description: |
  Build HubSpot marketing automation with emails, forms, lists, and tickets.
  Use when implementing marketing email campaigns, form submissions,
  contact list management, or support ticket workflows.
  Trigger with phrases like "hubspot marketing", "hubspot email campaign",
  "hubspot forms", "hubspot lists", "hubspot tickets", "hubspot automation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Core Workflow B: Marketing & Tickets

## Overview

Marketing automation workflow: manage contact lists, process form submissions, send marketing emails, and create support tickets. Complements the sales pipeline in Workflow A.

## Prerequisites

- Completed `hubspot-install-auth` setup
- Scopes: `crm.lists.read`, `crm.lists.write`, `content`, `forms`, `crm.objects.marketing.emails.read`
- Marketing Hub subscription (Starter+ for emails)

## Instructions

### Step 1: Create and Manage Contact Lists

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

// Create a static contact list
// POST /crm/v3/lists/
async function createStaticList(name: string): Promise<string> {
  const response = await client.apiRequest({
    method: 'POST',
    path: '/crm/v3/lists/',
    body: {
      name,
      objectTypeId: '0-1', // contacts
      processingType: 'MANUAL', // static list
    },
  });
  const data = await response.json();
  return data.listId;
}

// Add contacts to a static list
// PUT /crm/v3/lists/{listId}/memberships/add
async function addToList(listId: string, contactIds: string[]): Promise<void> {
  await client.apiRequest({
    method: 'PUT',
    path: `/crm/v3/lists/${listId}/memberships/add`,
    body: contactIds.map(Number),
  });
}

// Create a dynamic list with filter criteria
async function createDynamicList(name: string): Promise<string> {
  const response = await client.apiRequest({
    method: 'POST',
    path: '/crm/v3/lists/',
    body: {
      name,
      objectTypeId: '0-1',
      processingType: 'DYNAMIC',
      filterBranch: {
        filterBranchType: 'AND',
        filters: [
          {
            filterType: 'PROPERTY',
            property: 'lifecyclestage',
            operation: {
              operationType: 'MULTISTRING',
              operator: 'IS_ANY_OF',
              values: ['lead', 'marketingqualifiedlead'],
            },
          },
        ],
      },
    },
  });
  const data = await response.json();
  return data.listId;
}
```

### Step 2: Process Form Submissions

```typescript
// Handle a HubSpot form submission via the Forms API
// POST /submissions/v3/integration/secure/submit/{portalId}/{formGuid}
async function submitForm(
  portalId: string,
  formGuid: string,
  fields: Record<string, string>,
  context: { pageUri?: string; ipAddress?: string }
): Promise<void> {
  await client.apiRequest({
    method: 'POST',
    path: `/submissions/v3/integration/secure/submit/${portalId}/${formGuid}`,
    body: {
      submittedAt: Date.now(),
      fields: Object.entries(fields).map(([name, value]) => ({
        objectTypeId: '0-1',
        name,
        value,
      })),
      context: {
        pageUri: context.pageUri || '',
        ipAddress: context.ipAddress || '',
      },
    },
  });
}

// Retrieve form submissions
// GET /form-integrations/v1/submissions/forms/{formGuid}
async function getFormSubmissions(formGuid: string, limit = 50) {
  const response = await client.apiRequest({
    method: 'GET',
    path: `/form-integrations/v1/submissions/forms/${formGuid}?limit=${limit}`,
  });
  return response.json();
}
```

### Step 3: Create Support Tickets

```typescript
// POST /crm/v3/objects/tickets
async function createTicket(
  contactId: string,
  subject: string,
  description: string,
  priority: 'LOW' | 'MEDIUM' | 'HIGH'
): Promise<string> {
  // Get support pipeline
  const pipelines = await client.crm.pipelines.pipelinesApi.getAll('tickets');
  const supportPipeline = pipelines.results[0];
  const newStage = supportPipeline.stages.find(s => s.label === 'New')
    || supportPipeline.stages[0];

  const ticket = await client.crm.tickets.basicApi.create({
    properties: {
      subject,
      content: description,
      hs_pipeline: supportPipeline.id,
      hs_pipeline_stage: newStage.id,
      hs_ticket_priority: priority,
      source_type: 'API',
    },
    associations: [
      {
        to: { id: contactId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 16 }],
      },
    ],
  });

  console.log(`Created ticket ${ticket.id}: ${subject}`);
  return ticket.id;
}

// Update ticket stage
async function closeTicket(ticketId: string): Promise<void> {
  const ticket = await client.crm.tickets.basicApi.getById(
    ticketId, ['hs_pipeline']
  );
  const pipelines = await client.crm.pipelines.pipelinesApi.getAll('tickets');
  const pipeline = pipelines.results.find(p => p.id === ticket.properties.hs_pipeline);
  const closedStage = pipeline?.stages.find(
    s => s.label === 'Closed' || s.label === 'Done'
  );

  if (closedStage) {
    await client.crm.tickets.basicApi.update(ticketId, {
      properties: { hs_pipeline_stage: closedStage.id },
    });
  }
}
```

### Step 4: Create Tasks for Follow-up

```typescript
// POST /crm/v3/objects/tasks
async function createFollowUpTask(
  contactId: string,
  subject: string,
  dueDate: Date,
  ownerId: string
): Promise<string> {
  const task = await client.crm.objects.tasks.basicApi.create({
    properties: {
      hs_task_subject: subject,
      hs_task_body: `Follow up with contact ${contactId}`,
      hs_task_status: 'NOT_STARTED',
      hs_task_priority: 'MEDIUM',
      hs_timestamp: dueDate.toISOString(),
      hubspot_owner_id: ownerId,
    },
    associations: [
      {
        to: { id: contactId },
        types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 204 }],
      },
    ],
  });

  return task.id;
}
```

### Step 5: Search Across CRM Objects

```typescript
// POST /crm/v3/objects/{objectType}/search
async function searchCRM(
  objectType: 'contacts' | 'companies' | 'deals' | 'tickets',
  query: string,
  properties: string[]
) {
  const searchRequest = {
    filterGroups: [{
      filters: [{
        propertyName: objectType === 'contacts' ? 'email' : 'name',
        operator: 'CONTAINS_TOKEN' as const,
        value: `*${query}*`,
      }],
    }],
    properties,
    limit: 20,
    after: 0,
    sorts: [{ propertyName: 'createdate', direction: 'DESCENDING' as const }],
  };

  switch (objectType) {
    case 'contacts':
      return client.crm.contacts.searchApi.doSearch(searchRequest);
    case 'companies':
      return client.crm.companies.searchApi.doSearch(searchRequest);
    case 'deals':
      return client.crm.deals.searchApi.doSearch(searchRequest);
    case 'tickets':
      return client.crm.tickets.searchApi.doSearch(searchRequest);
  }
}
```

## Output

- Static and dynamic contact lists created
- Form submissions processed and retrieved
- Support tickets with pipeline stages
- Follow-up tasks created and assigned
- Cross-object CRM search

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `LIST_NOT_FOUND` | 404 | Invalid list ID | Verify list exists in HubSpot |
| `FORM_NOT_FOUND` | 404 | Invalid form GUID | Check form ID in Marketing > Forms |
| `INVALID_PIPELINE_STAGE` | 400 | Stage not in pipeline | Fetch pipeline stages first |
| `SCOPE_MISSING` | 403 | Missing `forms` or `content` scope | Add scope to private app |

## Examples

### Complete Marketing Workflow

```typescript
async function onNewSignup(email: string, name: string) {
  // 1. Submit to HubSpot form
  await submitForm(portalId, signupFormGuid, { email, firstname: name }, {});

  // 2. Find the created contact
  const contact = await findContactByEmail(email);

  // 3. Add to nurture list
  await addToList(nurtureListId, [contact.id]);

  // 4. Create follow-up task
  await createFollowUpTask(
    contact.id,
    `Welcome call: ${name}`,
    new Date(Date.now() + 2 * 86400000), // 2 days
    salesRepOwnerId
  );
}
```

## Resources

- [Lists API Guide](https://developers.hubspot.com/docs/guides/api/crm/lists/overview)
- [Forms API Guide](https://developers.hubspot.com/docs/reference/api/marketing/forms/v3)
- [Tickets API Guide](https://developers.hubspot.com/docs/guides/api/crm/objects/tickets)
- [Tasks API Guide](https://developers.hubspot.com/docs/guides/api/crm/engagements/tasks)

## Next Steps

For common errors, see `hubspot-common-errors`.
