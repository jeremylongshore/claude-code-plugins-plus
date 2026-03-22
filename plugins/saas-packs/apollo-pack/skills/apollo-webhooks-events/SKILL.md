---
name: apollo-webhooks-events
description: |
  Implement Apollo.io webhook and event-driven integrations.
  Use when receiving Apollo notifications, syncing data on changes,
  or building event-driven pipelines from Apollo activity.
  Trigger with phrases like "apollo webhooks", "apollo events",
  "apollo notifications", "apollo webhook handler", "apollo triggers".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, webhooks]

---
# Apollo Webhooks & Events

## Overview
Build event-driven integrations with Apollo.io. Apollo does not have a native webhook system like Stripe — instead, you build real-time sync by **polling** the API for changes or using **third-party webhook platforms** (Zapier, Pipedream, Make) that trigger on Apollo events. This skill covers both approaches plus the Contact Stages and Tasks APIs for workflow automation.

## Prerequisites
- Apollo account with master API key
- Node.js 18+ with Express
- For polling: a scheduler (cron, Cloud Scheduler, BullMQ)
- For webhook platforms: Zapier/Pipedream/Make account

## Instructions

### Step 1: Poll for Contact Changes
Since Apollo lacks native webhooks, poll the Contacts Search API for recently updated records.

```typescript
// src/sync/contact-poller.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

interface SyncState {
  lastSyncAt: string;  // ISO timestamp
}

export async function pollContactChanges(state: SyncState) {
  const { data } = await client.post('/contacts/search', {
    sort_by_field: 'contact_updated_at',
    sort_ascending: false,
    per_page: 100,
  });

  const lastSync = new Date(state.lastSyncAt);
  const newChanges = data.contacts.filter(
    (c: any) => new Date(c.updated_at) > lastSync,
  );

  if (newChanges.length > 0) {
    console.log(`Found ${newChanges.length} contact changes since ${state.lastSyncAt}`);
    for (const contact of newChanges) {
      await handleContactChange(contact);
    }
    state.lastSyncAt = new Date().toISOString();
  }

  return newChanges;
}

async function handleContactChange(contact: any) {
  console.log(`Contact updated: ${contact.name} (${contact.email}) — stage: ${contact.contact_stage_id}`);
  // Sync to your CRM, database, or notification system
}
```

### Step 2: Track Contact Stage Changes
Apollo has a Contact Stages system. Use the List Contact Stages endpoint to get stage IDs, then filter contacts by stage.

```typescript
// src/sync/stage-tracker.ts
export async function getContactStages() {
  const { data } = await client.get('/contact_stages');
  return data.contact_stages.map((s: any) => ({
    id: s.id,
    name: s.name,
    order: s.display_order,
  }));
}

// Find contacts that moved to a specific stage
export async function getContactsByStage(stageId: string) {
  const { data } = await client.post('/contacts/search', {
    contact_stage_ids: [stageId],
    sort_by_field: 'contact_updated_at',
    sort_ascending: false,
    per_page: 50,
  });
  return data.contacts;
}

// Update a contact's stage
export async function updateContactStage(contactId: string, stageId: string) {
  await client.put(`/contacts/${contactId}`, {
    contact_stage_id: stageId,
  });
}
```

### Step 3: Monitor Sequence Engagement
Poll sequence data for replies, bounces, and engagement events.

```typescript
// src/sync/sequence-monitor.ts
export async function checkSequenceEngagement(sequenceId: string) {
  const { data } = await client.post('/emailer_campaigns/search', {
    ids: [sequenceId],
    per_page: 1,
  });

  const seq = data.emailer_campaigns?.[0];
  if (!seq) return null;

  return {
    name: seq.name,
    active: seq.active,
    metrics: {
      scheduled: seq.unique_scheduled ?? 0,
      delivered: seq.unique_delivered ?? 0,
      opened: seq.unique_opened ?? 0,
      replied: seq.unique_replied ?? 0,
      bounced: seq.unique_bounced ?? 0,
      unsubscribed: seq.unique_unsubscribed ?? 0,
    },
    rates: {
      openRate: pct(seq.unique_opened, seq.unique_delivered),
      replyRate: pct(seq.unique_replied, seq.unique_delivered),
      bounceRate: pct(seq.unique_bounced, seq.unique_scheduled),
    },
  };
}

function pct(num?: number, denom?: number): string {
  if (!denom) return '0%';
  return `${(((num ?? 0) / denom) * 100).toFixed(1)}%`;
}
```

### Step 4: Create Tasks for Follow-Up Actions
Use Apollo's Tasks API to create actionable follow-ups triggered by your polling logic.

```typescript
// src/sync/task-creator.ts
export async function createFollowUpTask(params: {
  contactId: string;
  type: 'call' | 'action_item' | 'email';
  dueDate: string;
  note: string;
  assigneeId?: string;
}) {
  const { data } = await client.post('/tasks', {
    contact_id: params.contactId,
    type: params.type,
    due_date: params.dueDate,
    note: params.note,
    user_id: params.assigneeId,  // Apollo user ID to assign to
    priority: 'high',
    status: 'open',
  });

  return { taskId: data.task.id, type: data.task.type, dueDate: data.task.due_date };
}

// Example: auto-create call task when a sequence reply is detected
async function onSequenceReply(contactId: string, sequenceName: string) {
  await createFollowUpTask({
    contactId,
    type: 'call',
    dueDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    note: `Reply detected on sequence "${sequenceName}". Follow up immediately.`,
  });
}
```

### Step 5: Set Up a Cron-Based Sync Service
```typescript
// src/sync/scheduler.ts
import cron from 'node-cron';
import { pollContactChanges } from './contact-poller';
import { checkSequenceEngagement } from './sequence-monitor';

const syncState = { lastSyncAt: new Date(Date.now() - 60 * 60 * 1000).toISOString() };

// Poll every 5 minutes for contact changes
cron.schedule('*/5 * * * *', async () => {
  try {
    const changes = await pollContactChanges(syncState);
    console.log(`Sync complete: ${changes.length} changes`);
  } catch (err) {
    console.error('Contact sync failed:', err);
  }
});

// Check sequence engagement every 15 minutes
cron.schedule('*/15 * * * *', async () => {
  const activeSequenceIds = ['seq-1', 'seq-2'];  // from your config
  for (const id of activeSequenceIds) {
    const stats = await checkSequenceEngagement(id);
    if (stats && parseInt(stats.rates.replyRate) > 10) {
      console.log(`High reply rate on "${stats.name}": ${stats.rates.replyRate}`);
    }
  }
});

console.log('Apollo sync scheduler started');
```

## Output
- Contact change poller with timestamp-based incremental sync
- Contact stage tracking and updates via the Stages API
- Sequence engagement monitoring with reply/bounce/open rates
- Task creation API for automated follow-ups
- Cron-based scheduler for periodic sync

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missed changes between polls | Reduce poll interval or use `sort_by_field: contact_updated_at` |
| Rate limited during polling | Add backoff, reduce `per_page`, increase poll interval |
| Duplicate task creation | Track processed contact IDs in a Set or database |
| Third-party webhook delays | Zapier/Pipedream polling intervals vary (1-15 min on free tiers) |

## Resources
- [List Contact Stages](https://docs.apollo.io/reference/list-contact-stages)
- [Search for Contacts](https://docs.apollo.io/reference/search-for-contacts)
- [Create a Task](https://docs.apollo.io/reference/create-task)
- [Search for Sequences](https://docs.apollo.io/reference/search-for-sequences)
- [Apollo + Zapier Integration](https://zapier.com/apps/apollo/integrations)

## Next Steps
Proceed to `apollo-performance-tuning` for optimization.
