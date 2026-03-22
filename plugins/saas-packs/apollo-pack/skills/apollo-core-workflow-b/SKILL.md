---
name: apollo-core-workflow-b
description: |
  Implement Apollo.io email sequences and outreach workflow.
  Use when building automated email campaigns, creating sequences,
  or managing outreach through Apollo.
  Trigger with phrases like "apollo email sequence", "apollo outreach",
  "apollo campaign", "apollo sequences", "apollo automated emails".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, workflow]

---
# Apollo Core Workflow B: Email Sequences & Outreach

## Overview
Build Apollo.io email sequencing and outreach automation via the REST API. Sequences in Apollo are called "emailer_campaigns" in the API. This covers listing, searching, adding contacts, tracking engagement, and managing sequence lifecycle. All endpoints require a **master API key**.

## Prerequisites
- Completed `apollo-core-workflow-a` (lead search)
- Apollo account with Sequences feature enabled
- Connected email account in Apollo (Settings > Channels > Email)
- Master API key (not standard)

## Instructions

### Step 1: Search for Existing Sequences
```typescript
// src/workflows/sequences.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

export async function searchSequences(query?: string) {
  const { data } = await client.post('/emailer_campaigns/search', {
    q_name: query,       // optional name filter
    page: 1,
    per_page: 25,
  });

  return data.emailer_campaigns.map((seq: any) => ({
    id: seq.id,
    name: seq.name,
    active: seq.active,
    numSteps: seq.num_steps ?? seq.emailer_steps?.length ?? 0,
    stats: {
      totalContacts: seq.unique_scheduled ?? 0,
      delivered: seq.unique_delivered ?? 0,
      opened: seq.unique_opened ?? 0,
      replied: seq.unique_replied ?? 0,
      bounced: seq.unique_bounced ?? 0,
    },
    createdAt: seq.created_at,
  }));
}
```

### Step 2: Get Email Accounts for Sending
Before adding contacts to a sequence, you need the email account ID that will send the messages.

```typescript
export async function getEmailAccounts() {
  const { data } = await client.get('/email_accounts');

  return data.email_accounts.map((acct: any) => ({
    id: acct.id,
    email: acct.email,
    sendingEnabled: acct.active,
    provider: acct.type,  // "gmail", "outlook", "smtp"
    dailySendLimit: acct.daily_email_limit,
  }));
}
```

### Step 3: Add Contacts to a Sequence
The `add_contact_ids` endpoint enrolls contacts into an existing sequence. You must specify which email account sends the messages.

```typescript
export async function addContactsToSequence(
  sequenceId: string,
  contactIds: string[],
  emailAccountId: string,
) {
  const { data } = await client.post(
    `/emailer_campaigns/${sequenceId}/add_contact_ids`,
    {
      contact_ids: contactIds,
      emailer_campaign_id: sequenceId,
      send_email_from_email_account_id: emailAccountId,
      sequence_active_in_other_campaigns: false,  // skip if already in another sequence
    },
  );

  return {
    added: data.contacts?.length ?? 0,
    alreadyInCampaign: data.contacts_already_in_campaign ?? 0,
    errors: data.not_added_contact_ids ?? [],
  };
}
```

### Step 4: Update Contact Status in a Sequence
```typescript
// Mark contacts as finished or remove them from a sequence
export async function removeContactsFromSequence(
  sequenceId: string,
  contactIds: string[],
  action: 'finished' | 'removed' = 'finished',
) {
  const { data } = await client.post('/emailer_campaigns/remove_or_stop_contact_ids', {
    emailer_campaign_id: sequenceId,
    contact_ids: contactIds,
    // "finished" marks contact as completed; "removed" fully removes
  });

  return {
    updated: data.contacts?.length ?? 0,
  };
}
```

### Step 5: Create and Manage Contacts for Sequences
Contacts must exist in your Apollo CRM before adding to sequences. Use the Contacts API to create them.

```typescript
// Create a contact in your Apollo CRM
export async function createContact(params: {
  firstName: string;
  lastName: string;
  email: string;
  title?: string;
  organizationName?: string;
  websiteUrl?: string;
}) {
  const { data } = await client.post('/contacts', {
    first_name: params.firstName,
    last_name: params.lastName,
    email: params.email,
    title: params.title,
    organization_name: params.organizationName,
    website_url: params.websiteUrl,
  });

  return {
    id: data.contact.id,
    email: data.contact.email,
    name: `${data.contact.first_name} ${data.contact.last_name}`,
  };
}

// Search your CRM contacts (not the Apollo database)
export async function searchCrmContacts(query: string) {
  const { data } = await client.post('/contacts/search', {
    q_keywords: query,
    page: 1,
    per_page: 25,
  });

  return data.contacts.map((c: any) => ({
    id: c.id,
    name: c.name,
    email: c.email,
    title: c.title,
    company: c.organization_name,
  }));
}
```

### Step 6: Full Outreach Pipeline
```typescript
async function launchOutreach(
  sequenceId: string,
  leads: Array<{ firstName: string; lastName: string; email: string; title?: string; company?: string }>,
) {
  // 1. Get a sending email account
  const accounts = await getEmailAccounts();
  const sender = accounts.find((a: any) => a.sendingEnabled);
  if (!sender) throw new Error('No active email account found');

  // 2. Create contacts in Apollo CRM (or find existing)
  const contactIds: string[] = [];
  for (const lead of leads) {
    try {
      const contact = await createContact({
        firstName: lead.firstName,
        lastName: lead.lastName,
        email: lead.email,
        title: lead.title,
        organizationName: lead.company,
      });
      contactIds.push(contact.id);
    } catch (err: any) {
      // Contact may already exist — search for them
      const existing = await searchCrmContacts(lead.email);
      if (existing.length > 0) contactIds.push(existing[0].id);
    }
  }

  // 3. Add contacts to the sequence
  const result = await addContactsToSequence(sequenceId, contactIds, sender.id);
  console.log(`Added ${result.added} contacts, ${result.alreadyInCampaign} already enrolled`);

  return result;
}
```

## Output
- Sequence search via `POST /emailer_campaigns/search`
- Email account listing via `GET /email_accounts`
- Contact enrollment via `POST /emailer_campaigns/{id}/add_contact_ids`
- Contact removal via `POST /emailer_campaigns/remove_or_stop_contact_ids`
- Contact creation via `POST /contacts` and search via `POST /contacts/search`
- Full outreach pipeline: create contacts, find sender, enroll in sequence

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Standard API key used | Sequence endpoints require a master API key |
| No email accounts | Inbox not connected | Connect email at Settings > Channels > Email in Apollo UI |
| Contact already enrolled | Duplicate enrollment | Check `contacts_already_in_campaign` in response |
| Contact not found | ID does not exist in CRM | Create via `POST /contacts` first |

## Resources
- [Search for Sequences](https://docs.apollo.io/reference/search-for-sequences)
- [Add Contacts to Sequence](https://docs.apollo.io/reference/add-contacts-to-sequence)
- [Update Contact Status](https://docs.apollo.io/reference/update-contact-status-sequence)
- [Get Email Accounts](https://docs.apollo.io/reference/get-a-list-of-email-accounts)
- [Create a Contact](https://docs.apollo.io/reference/create-a-contact)
- [Search for Contacts](https://docs.apollo.io/reference/search-for-contacts)

## Next Steps
Proceed to `apollo-common-errors` for error handling patterns.
