# Apollo Core Workflow B: Email Sequences & Outreach - Implementation Guide

> Full implementation details and code examples for the `apollo-core-workflow-b` skill.

# Apollo Core Workflow B: Email Sequences & Outreach

## Overview
Implement Apollo.io's email sequencing and outreach automation capabilities for B2B sales campaigns.

## Prerequisites
- Completed `apollo-core-workflow-a` (lead search)
- Apollo account with Sequences feature enabled
- Connected email account in Apollo

## Workflow Components

### 1. List Existing Sequences

```typescript
// src/services/apollo/sequences.ts
import { apollo } from '../../lib/apollo/client';

export async function listSequences() {
  const response = await apollo.request({
    method: 'GET',
    url: '/emailer_campaigns',
  });

  return response.emailer_campaigns.map((campaign: any) => ({
    id: campaign.id,
    name: campaign.name,
    status: campaign.active ? 'active' : 'paused',
    stepsCount: campaign.num_steps,
    contactsCount: campaign.contact_count,
    createdAt: campaign.created_at,
    stats: {
      sent: campaign.emails_sent_count,
      opened: campaign.emails_opened_count,
      replied: campaign.emails_replied_count,
      bounced: campaign.emails_bounced_count,
    },
  }));
}
```

### 2. Create Email Sequence

```typescript
// src/services/apollo/create-sequence.ts
interface SequenceStep {
  type: 'auto_email' | 'manual_email' | 'call' | 'task';
  subject?: string;
  body?: string;
  waitDays: number;
}

interface CreateSequenceParams {
  name: string;
  steps: SequenceStep[];
  sendingSchedule?: {
    timezone: string;
    days: string[];
    startHour: number;
    endHour: number;
  };
}

export async function createSequence(params: CreateSequenceParams) {
  const sequence = await apollo.request({
    method: 'POST',
    url: '/emailer_campaigns',
    data: {
      name: params.name,
      permissions: 'team',
      active: false, // Start paused
      emailer_schedule: params.sendingSchedule ? {
        timezone: params.sendingSchedule.timezone,
        days_of_week: params.sendingSchedule.days,
        start_hour: params.sendingSchedule.startHour,
        end_hour: params.sendingSchedule.endHour,
      } : undefined,
    },
  });

  // Add steps to sequence
  for (const step of params.steps) {
    await addSequenceStep(sequence.emailer_campaign.id, step);
  }

  return sequence.emailer_campaign;
}

async function addSequenceStep(sequenceId: string, step: SequenceStep) {
  return apollo.request({
    method: 'POST',
    url: `/emailer_campaigns/${sequenceId}/emailer_steps`,
    data: {
      emailer_step: {
        type: step.type,
        wait_time: step.waitDays * 24 * 60, // Convert to minutes
        email_template: step.subject ? {
          subject: step.subject,
          body_html: step.body,
        } : undefined,
      },
    },
  });
}
```

### 3. Add Contacts to Sequence

```typescript
// src/services/apollo/sequence-contacts.ts
interface AddToSequenceParams {
  sequenceId: string;
  contactIds: string[];
  sendEmailFromId?: string;
}

export async function addContactsToSequence(params: AddToSequenceParams) {
  const results = await Promise.allSettled(
    params.contactIds.map(async (contactId) => {
      return apollo.request({
        method: 'POST',
        url: '/emailer_campaigns/add_contact_ids',
        data: {
          emailer_campaign_id: params.sequenceId,
          contact_ids: [contactId],
          send_email_from_user_id: params.sendEmailFromId,
        },
      });
    })
  );

  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  return {
    added: succeeded,
    failed,
    total: params.contactIds.length,
  };
}

export async function removeContactFromSequence(
  sequenceId: string,
  contactId: string
) {
  return apollo.request({
    method: 'POST',
    url: '/emailer_campaigns/remove_contact_ids',
    data: {
      emailer_campaign_id: sequenceId,
      contact_ids: [contactId],
    },
  });
}
```

### 4. Sequence Analytics

```typescript
// src/services/apollo/sequence-analytics.ts
export async function getSequenceAnalytics(sequenceId: string) {
  const response = await apollo.request({
    method: 'GET',
    url: `/emailer_campaigns/${sequenceId}`,
  });

  const campaign = response.emailer_campaign;

  return {
    id: campaign.id,
    name: campaign.name,
    metrics: {
      totalContacts: campaign.contact_count,
      activeContacts: campaign.active_contact_count,
      completedContacts: campaign.finished_contact_count,
    },
    emailMetrics: {
      sent: campaign.emails_sent_count,
      delivered: campaign.emails_sent_count - campaign.emails_bounced_count,
      opened: campaign.emails_opened_count,
      clicked: campaign.emails_clicked_count,
      replied: campaign.emails_replied_count,
      bounced: campaign.emails_bounced_count,
    },
    rates: {
      deliveryRate: calculateRate(
        campaign.emails_sent_count - campaign.emails_bounced_count,
        campaign.emails_sent_count
      ),
      openRate: calculateRate(
        campaign.emails_opened_count,
        campaign.emails_sent_count
      ),
      clickRate: calculateRate(
        campaign.emails_clicked_count,
        campaign.emails_opened_count
      ),
      replyRate: calculateRate(
        campaign.emails_replied_count,
        campaign.emails_sent_count
      ),
    },
  };
}

function calculateRate(numerator: number, denominator: number): number {
  if (denominator === 0) return 0;
  return Math.round((numerator / denominator) * 100 * 10) / 10;
}
```

### 5. Complete Outreach Pipeline

```typescript
// src/services/apollo/outreach-pipeline.ts
import { searchPeople } from './people-search';
import { createSequence } from './create-sequence';
import { addContactsToSequence } from './sequence-contacts';

interface OutreachCampaign {
  name: string;
  targetCriteria: {
    domains: string[];
    titles: string[];
  };
  emailSteps: Array<{
    subject: string;
    body: string;
    waitDays: number;
  }>;
}

export async function launchOutreachCampaign(campaign: OutreachCampaign) {
  // Step 1: Find matching leads
  const leads = await searchPeople({
    domains: campaign.targetCriteria.domains,
    titles: campaign.targetCriteria.titles,
    perPage: 100,
  });

  console.log(`Found ${leads.contacts.length} matching contacts`);

  // Step 2: Create sequence
  const sequence = await createSequence({
    name: campaign.name,
    steps: campaign.emailSteps.map((step, index) => ({
      type: 'auto_email' as const,
      subject: step.subject,
      body: step.body,
      waitDays: index === 0 ? 0 : step.waitDays,
    })),
    sendingSchedule: {
      timezone: 'America/New_York',
      days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
      startHour: 9,
      endHour: 17,
    },
  });

  console.log(`Created sequence: ${sequence.id}`);

  // Step 3: Add contacts to sequence
  const contactIds = leads.contacts.map(c => c.id);
  const result = await addContactsToSequence({
    sequenceId: sequence.id,
    contactIds,
  });

  console.log(`Added ${result.added} contacts to sequence`);

  return {
    sequenceId: sequence.id,
    contactsAdded: result.added,
    contactsFailed: result.failed,
  };
}
```

## Usage Example

```typescript
// Launch a cold outreach campaign
const result = await launchOutreachCampaign({
  name: 'Q1 2025 Engineering Leaders Outreach',
  targetCriteria: {
    domains: ['stripe.com', 'plaid.com', 'square.com'],
    titles: ['VP Engineering', 'Director of Engineering'],
  },
  emailSteps: [
    {
      subject: 'Quick question about {{company}}',
      body: 'Hi {{first_name}}, ...',
      waitDays: 0,
    },
    {
      subject: 'Following up',
      body: 'Hi {{first_name}}, wanted to follow up...',
      waitDays: 3,
    },
    {
      subject: 'Last attempt',
      body: 'Hi {{first_name}}, one last note...',
      waitDays: 5,
    },
  ],
});
```

## Output
- List of available sequences with stats
- New sequence creation with steps
- Contacts added to sequences
- Campaign analytics and metrics

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Email Not Connected | No sending account | Connect email in Apollo UI |
| Contact Already in Sequence | Duplicate enrollment | Check before adding |
| Invalid Email Template | Missing variables | Validate template syntax |
| Sequence Limit Reached | Plan limits | Upgrade plan or archive sequences |

## Resources
- [Apollo Sequences API](https://apolloio.github.io/apollo-api-docs/#emailer-campaigns)
- [Apollo Email Templates](https://knowledge.apollo.io/hc/en-us/articles/4415154183053)
- [Sequence Best Practices](https://knowledge.apollo.io/hc/en-us/articles/4405955284621)

## Next Steps
Proceed to `apollo-common-errors` for error handling patterns.
