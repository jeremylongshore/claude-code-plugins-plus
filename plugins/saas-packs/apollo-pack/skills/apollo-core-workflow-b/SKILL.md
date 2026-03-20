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
---
# Apollo Core Workflow B: Email Sequences & Outreach

## Overview
Implement Apollo.io email sequencing and outreach automation via the REST API (`https://api.apollo.io/v1`). Build automated multi-step campaigns, add contacts to sequences, and track engagement metrics.

## Prerequisites
- Completed `apollo-core-workflow-a` (lead search)
- Apollo account with Sequences feature enabled
- Connected email account in Apollo (Settings > Email)

## Instructions

### Step 1: List Available Sequences
```typescript
// src/workflows/sequences.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  headers: { 'Content-Type': 'application/json' },
  params: { api_key: process.env.APOLLO_API_KEY },
});

async function listSequences() {
  const { data } = await client.get('/emailer_campaigns');

  return data.emailer_campaigns.map((seq: any) => ({
    id: seq.id,
    name: seq.name,
    active: seq.active,
    numSteps: seq.emailer_steps?.length ?? 0,
    stats: {
      totalContacts: seq.num_contacts_with_status ?? 0,
      replied: seq.unique_replied ?? 0,
      bounced: seq.unique_bounced ?? 0,
      opened: seq.unique_opened ?? 0,
    },
  }));
}
```

### Step 2: Create a New Sequence
```typescript
async function createSequence(name: string, steps: SequenceStep[]) {
  // Create the sequence shell
  const { data } = await client.post('/emailer_campaigns', {
    name,
    permissions: 'team_can_use',
    active: false,  // activate after adding steps
  });

  const sequenceId = data.emailer_campaign.id;

  // Add steps to the sequence
  for (const step of steps) {
    await client.post('/emailer_steps', {
      emailer_campaign_id: sequenceId,
      type: step.type,         // "auto_email", "manual_email", "call", "task"
      wait_time: step.waitDays, // days to wait before this step
      priority: step.priority ?? 'medium',
      emailer_template: step.type.includes('email') ? {
        subject: step.subject,
        body_html: step.bodyHtml,
      } : undefined,
      note: step.type === 'call' ? step.callScript : undefined,
    });
  }

  return sequenceId;
}

interface SequenceStep {
  type: 'auto_email' | 'manual_email' | 'call' | 'task';
  waitDays: number;
  priority?: 'high' | 'medium' | 'low';
  subject?: string;
  bodyHtml?: string;
  callScript?: string;
}
```

### Step 3: Add Contacts to a Sequence
```typescript
async function addContactsToSequence(
  sequenceId: string,
  contactIds: string[],
) {
  const { data } = await client.post('/emailer_campaigns/add_contact_ids', {
    contact_ids: contactIds,
    emailer_campaign_id: sequenceId,
    send_email_from_email_account_id: process.env.APOLLO_EMAIL_ACCOUNT_ID,
  });

  return {
    added: data.contacts?.length ?? 0,
    alreadyInSequence: data.already_in_campaign ?? 0,
    errors: data.errors ?? [],
  };
}
```

### Step 4: Track Sequence Analytics
```typescript
async function getSequenceStats(sequenceId: string) {
  const { data } = await client.get(
    `/emailer_campaigns/${sequenceId}`,
  );

  const campaign = data.emailer_campaign;
  return {
    name: campaign.name,
    active: campaign.active,
    totalContacts: campaign.num_contacts_with_status,
    metrics: {
      sent: campaign.unique_sent ?? 0,
      delivered: campaign.unique_delivered ?? 0,
      opened: campaign.unique_opened ?? 0,
      clicked: campaign.unique_clicked ?? 0,
      replied: campaign.unique_replied ?? 0,
      bounced: campaign.unique_bounced ?? 0,
      unsubscribed: campaign.unique_unsubscribed ?? 0,
    },
    rates: {
      openRate: safePercent(campaign.unique_opened, campaign.unique_delivered),
      replyRate: safePercent(campaign.unique_replied, campaign.unique_delivered),
      bounceRate: safePercent(campaign.unique_bounced, campaign.unique_sent),
    },
  };
}

function safePercent(num?: number, denom?: number): string {
  if (!denom) return '0%';
  return `${((num ?? 0) / denom * 100).toFixed(1)}%`;
}
```

### Step 5: Activate the Sequence
```typescript
async function activateSequence(sequenceId: string) {
  await client.put(`/emailer_campaigns/${sequenceId}`, {
    active: true,
  });
  console.log(`Sequence ${sequenceId} activated`);
}
```

## Output
- List of available sequences with engagement stats
- New multi-step sequence (auto emails, calls, tasks)
- Contacts enrolled in the sequence
- Real-time engagement metrics (open, reply, bounce rates)
- Sequence activation toggle

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Email Not Connected | No sending account linked | Connect email in Apollo UI (Settings > Email) |
| Contact Already in Sequence | Duplicate enrollment attempt | Check `already_in_campaign` in response |
| Invalid Template Variables | Missing `{{first_name}}` etc. | Validate template before creating step |
| Sequence Limit Reached | Plan limit on active sequences | Archive old sequences or upgrade plan |

## Examples

### Build a 3-Step Outreach Sequence
```typescript
const sequenceId = await createSequence('Q1 Outbound - VP Sales', [
  {
    type: 'auto_email',
    waitDays: 0,
    subject: 'Quick question about {{company}}',
    bodyHtml: '<p>Hi {{first_name}},</p><p>I noticed {{company}} is scaling...</p>',
  },
  {
    type: 'auto_email',
    waitDays: 3,
    subject: 'Re: Quick question about {{company}}',
    bodyHtml: '<p>{{first_name}}, wanted to follow up on my last note...</p>',
  },
  {
    type: 'call',
    waitDays: 2,
    callScript: 'Reference the email sequence. Ask about current tools.',
  },
]);

// Add leads from search results
const result = await addContactsToSequence(sequenceId, contactIds);
console.log(`Added ${result.added} contacts, ${result.alreadyInSequence} skipped`);

// Go live
await activateSequence(sequenceId);
```

## Resources
- [Apollo Sequences API](https://apolloio.github.io/apollo-api-docs/#emailer-campaigns)
- [Apollo Emailer Steps API](https://apolloio.github.io/apollo-api-docs/#emailer-steps)
- [Sequence Best Practices](https://knowledge.apollo.io/hc/en-us/articles/4405955284621)

## Next Steps
Proceed to `apollo-common-errors` for error handling patterns.
