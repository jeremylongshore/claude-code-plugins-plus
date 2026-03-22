---
name: hubspot-data-handling
description: |
  Implement HubSpot GDPR compliance, data export, and contact privacy operations.
  Use when handling GDPR/CCPA data subject requests, implementing data export,
  contact deletion, or privacy-compliant HubSpot integrations.
  Trigger with phrases like "hubspot GDPR", "hubspot data export",
  "hubspot delete contact", "hubspot privacy", "hubspot CCPA", "hubspot PII".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Data Handling

## Overview

Handle GDPR/CCPA compliance with HubSpot's built-in privacy APIs: GDPR delete, data export, consent management, and PII handling for CRM data.

## Prerequisites

- HubSpot account with GDPR features enabled
- Scope: `crm.objects.contacts.write` (for GDPR delete)
- Understanding of GDPR/CCPA requirements

## Instructions

### Step 1: GDPR Contact Deletion

HubSpot provides a dedicated GDPR delete endpoint that permanently removes all contact data and communications:

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
});

// GDPR delete: permanently removes contact and all associated data
// POST /crm/v3/objects/contacts/gdpr-delete
async function gdprDeleteContact(email: string): Promise<void> {
  // First, find the contact
  const search = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
    }],
    properties: ['email'],
    limit: 1, after: 0, sorts: [],
  });

  if (search.results.length === 0) {
    console.log(`Contact not found: ${email}`);
    return;
  }

  const contactId = search.results[0].id;

  // GDPR delete via API
  await client.apiRequest({
    method: 'POST',
    path: '/crm/v3/objects/contacts/gdpr-delete',
    body: {
      objectId: contactId,
      idProperty: 'hs_object_id',
    },
  });

  // Also delete from your local systems
  await deleteLocalContactData(email);

  // Audit log (keep for compliance -- do NOT delete audit records)
  await auditLog({
    action: 'GDPR_DELETE',
    email: '[REDACTED]', // don't store the email in audit
    contactId,
    timestamp: new Date().toISOString(),
    reason: 'Data subject deletion request',
  });

  console.log(`GDPR deleted contact ${contactId}`);
}
```

### Step 2: Data Subject Access Request (DSAR)

Export all data HubSpot holds about a contact:

```typescript
async function exportContactData(email: string): Promise<ContactDataExport> {
  // Find contact
  const search = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
    }],
    properties: [], // get all default properties
    limit: 1, after: 0, sorts: [],
  });

  if (search.results.length === 0) {
    return { found: false, data: null };
  }

  const contact = search.results[0];

  // Get all properties for complete export
  const fullContact = await client.crm.contacts.basicApi.getById(
    contact.id,
    undefined, // all properties
    undefined,
    ['companies', 'deals', 'tickets'] // include associations
  );

  // Get associated deals
  const deals = await client.crm.deals.searchApi.doSearch({
    filterGroups: [{
      filters: [{
        propertyName: 'associations.contact',
        operator: 'EQ',
        value: contact.id,
      }],
    }],
    properties: ['dealname', 'amount', 'dealstage', 'createdate'],
    limit: 100, after: 0, sorts: [],
  });

  // Get engagement history (notes, emails, calls)
  const notes = await client.crm.objects.notes.basicApi.getPage(
    100, undefined, ['hs_note_body', 'hs_timestamp']
  );

  return {
    found: true,
    data: {
      exportedAt: new Date().toISOString(),
      source: 'HubSpot CRM',
      contact: fullContact.properties,
      associations: fullContact.associations,
      deals: deals.results.map(d => d.properties),
      notes: notes.results.map(n => n.properties),
    },
  };
}

interface ContactDataExport {
  found: boolean;
  data: {
    exportedAt: string;
    source: string;
    contact: Record<string, string>;
    associations?: any;
    deals: Record<string, string>[];
    notes: Record<string, string>[];
  } | null;
}
```

### Step 3: PII Redaction for Logging

```typescript
// Never log PII from HubSpot responses
const PII_FIELDS = new Set([
  'email', 'firstname', 'lastname', 'phone', 'mobilephone',
  'address', 'city', 'state', 'zip', 'country',
  'date_of_birth', 'ip_city', 'ip_state', 'ip_country',
]);

function redactContactForLogging(properties: Record<string, string>): Record<string, string> {
  const redacted: Record<string, string> = {};
  for (const [key, value] of Object.entries(properties)) {
    redacted[key] = PII_FIELDS.has(key) ? '[REDACTED]' : value;
  }
  return redacted;
}

// Usage
const contact = await client.crm.contacts.basicApi.getById(id, ['email', 'lifecyclestage']);
console.log('Contact data:', redactContactForLogging(contact.properties));
// Output: { email: "[REDACTED]", lifecyclestage: "customer" }
```

### Step 4: Consent Tracking

```typescript
// Track consent using HubSpot's communication preferences
// POST /crm/v3/objects/contacts (with consent properties)
async function createContactWithConsent(
  email: string,
  properties: Record<string, string>,
  consent: { marketing: boolean; sales: boolean }
): Promise<void> {
  await client.crm.contacts.basicApi.create({
    properties: {
      ...properties,
      email,
      hs_legal_basis: consent.marketing
        ? 'Legitimate interest - existing customer'
        : 'Not applicable',
    },
    associations: [],
  });

  // Set communication preferences via the subscriptions API
  if (consent.marketing) {
    await client.apiRequest({
      method: 'POST',
      path: `/communication-preferences/v3/subscribe`,
      body: {
        emailAddress: email,
        subscriptionId: process.env.HUBSPOT_MARKETING_SUBSCRIPTION_ID!,
        legalBasis: 'CONSENT_WITH_NOTICE',
        legalBasisExplanation: 'User opted in via signup form',
      },
    });
  }
}
```

### Step 5: Data Minimization

```typescript
// Only request the properties you actually need
// BAD: Fetches all default properties including PII
const bad = await client.crm.contacts.basicApi.getById(id);

// GOOD: Only fetch non-PII fields for analytics
const good = await client.crm.contacts.basicApi.getById(id, [
  'lifecyclestage',      // not PII
  'hs_lead_status',      // not PII
  'createdate',          // not PII
  'num_associated_deals', // not PII
]);
```

## Output

- GDPR delete endpoint permanently removing contact data
- Data export for Subject Access Requests
- PII redaction utility for safe logging
- Consent tracking with communication preferences
- Data minimization patterns for non-PII analytics

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| GDPR delete returns 404 | Contact already deleted | Idempotent -- log and continue |
| Export missing associations | Scope not granted | Add `crm.objects.deals.read` scope |
| Consent API returns 400 | Invalid subscription ID | Check Settings > Marketing > Email > Subscriptions |
| PII in logs | Missing redaction | Wrap all logging with `redactContactForLogging` |

## Resources

- [HubSpot GDPR Compliance](https://developers.hubspot.com/docs/guides/api/crm/gdpr)
- [Communication Preferences API](https://developers.hubspot.com/docs/reference/api/marketing/subscriptions-preferences)
- [GDPR Developer Guide](https://gdpr.eu/developers/)

## Next Steps

For enterprise access control, see `hubspot-enterprise-rbac`.
