---
name: instantly-reference-architecture
description: |
  Implement Instantly reference architecture with best-practice project layout.
  Use when designing new Instantly integrations, reviewing project structure,
  or establishing architecture standards for Instantly applications.
  Trigger with phrases like "instantly architecture", "instantly best practices",
  "instantly project structure", "how to organize instantly", "instantly layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Reference Architecture

## Overview
Production architecture for cold outreach automation with Instantly. Covers campaign orchestration, lead management pipelines, multi-account warmup strategies, and reply handling with CRM synchronization.

## Prerequisites
- Instantly API key (v1 REST)
- Email accounts configured with warmup
- CRM for lead status tracking
- Webhook endpoint for reply/bounce handling

## Architecture Diagram

```
set -euo pipefail
┌──────────────────────────────────────────────────────┐
│              Lead Sources                             │
│  Clay │ Apollo │ CSV Import │ CRM Export │ API       │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│              Instantly Platform                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐   │
│  │ Email        │  │ Campaigns    │  │ Lead      │   │
│  │ Accounts     │  │ & Sequences  │  │ Lists     │   │
│  │ (warmup)     │  │ (A/B test)   │  │ (import)  │   │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘   │
│         │                 │                │          │
│         ▼                 ▼                ▼          │
│  ┌──────────────────────────────────────────────┐     │
│  │         Sending Engine                        │     │
│  │  Throttling │ Rotation │ Tracking │ Warmup   │     │
│  └──────────────────────┬───────────────────────┘     │
└─────────────────────────┼───────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
   ┌──────────────┐ ┌────────┐ ┌──────────────┐
   │ Replies      │ │ Opens  │ │ Bounces      │
   │ (webhook)    │ │ Clicks │ │ Unsubscribes │
   └──────┬───────┘ └────────┘ └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ CRM Sync     │
   │ (HubSpot/SF) │
   └──────────────┘
```

## Instructions

### Step 1: Campaign Management Service
```typescript
const INSTANTLY_API = 'https://api.instantly.ai/api/v1';

async function instantlyRequest(endpoint: string, options?: RequestInit) {
  const url = new URL(`${INSTANTLY_API}${endpoint}`);
  url.searchParams.set('api_key', process.env.INSTANTLY_API_KEY!);

  const response = await fetch(url.toString(), {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });

  if (!response.ok) throw new Error(`Instantly API error: ${response.status}`);
  return response.json();
}

async function listCampaigns() {
  return instantlyRequest('/campaign/list');
}

async function getCampaignStatus(campaignId: string) {
  return instantlyRequest(`/campaign/get?campaign_id=${campaignId}`);
}
```

### Step 2: Lead Upload Pipeline
```typescript
interface Lead {
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  personalization?: string;
  custom_variables?: Record<string, string>;
}

async function uploadLeads(campaignId: string, leads: Lead[]) {
  const BATCH_SIZE = 100;
  let totalUploaded = 0;

  for (let i = 0; i < leads.length; i += BATCH_SIZE) {
    const batch = leads.slice(i, i + BATCH_SIZE);
    await instantlyRequest('/lead/add', {
      method: 'POST',
      body: JSON.stringify({
        campaign_id: campaignId,
        skip_if_in_workspace: true,
        leads: batch,
      }),
    });
    totalUploaded += batch.length;
    await new Promise(r => setTimeout(r, 200)); // Rate limit  # HTTP 200 OK
  }

  return { uploaded: totalUploaded };
}
```

### Step 3: Multi-Sequence Campaign Structure
```typescript
// Campaign sequence design for cold outreach
const CAMPAIGN_SEQUENCE = {
  name: 'Q1 Outreach - {ICP Segment}',
  sequences: [
    {
      step: 1,
      delay: 0,
      subject: 'Quick question about {{company_name}}',
      body: 'Hi {{first_name}},\n\n{{personalization}}\n\n...',
      variant: 'A',
    },
    {
      step: 1,
      delay: 0,
      subject: '{{first_name}} - saw something interesting',
      body: 'Hi {{first_name}},\n\n...',
      variant: 'B', // A/B test variant
    },
    {
      step: 2,
      delay: 3, // 3 days after step 1
      subject: 'Re: Quick question',
      body: 'Hi {{first_name}},\n\nJust following up...',
    },
    {
      step: 3,
      delay: 5, // 5 days after step 2
      subject: 'Last try',
      body: 'Hi {{first_name}},\n\nI know you\'re busy...',
    },
  ],
};
```

### Step 4: Reply Handling Webhook
```typescript
app.post('/webhooks/instantly', express.json(), async (req, res) => {
  const { event_type, lead_email, campaign_id, reply_text } = req.body;

  switch (event_type) {
    case 'reply_received':
      await syncToCRM({ email: lead_email, status: 'replied', note: reply_text });
      break;
    case 'email_bounced':
      await syncToCRM({ email: lead_email, status: 'bounced' });
      break;
    case 'unsubscribed':
      await addToSuppressionList(lead_email);
      break;
  }

  res.json({ processed: true });
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Low deliverability | Accounts not warmed | Run warmup 2+ weeks before campaigns |
| High bounce rate | Bad lead data | Verify emails before upload |
| Duplicate sends | Lead in multiple campaigns | Use `skip_if_in_workspace` flag |
| Rate limit | Too many API calls | Add 200ms delay between requests |

## Examples

### Campaign Analytics Dashboard
```typescript
async function getCampaignMetrics() {
  const campaigns = await listCampaigns();
  return Promise.all(campaigns.map(async (c: any) => ({
    name: c.name,
    status: c.status,
    analytics: await instantlyRequest(
      `/analytics/campaign/summary?campaign_id=${c.id}`
    ),
  })));
}
```

## Resources
- [Instantly API Documentation](https://developer.instantly.ai/)
- [Instantly Campaign Guide](https://instantly.ai/resources)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale