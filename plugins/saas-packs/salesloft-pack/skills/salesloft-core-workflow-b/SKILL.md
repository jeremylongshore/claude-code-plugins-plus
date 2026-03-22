---
name: salesloft-core-workflow-b
description: |
  Track SalesLoft activities, emails, calls, and analytics via the REST API.
  Use when reading email engagement data, logging call dispositions,
  or building sales activity dashboards.
  Trigger: "salesloft activities", "salesloft emails", "salesloft calls", "salesloft analytics".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Core Workflow B: Activities & Analytics

## Overview

Track and analyze sales activities: emails sent/opened/clicked/replied, calls logged, and engagement metrics. Uses REST API v2 endpoints: `/activities/emails.json`, `/activities/calls.json`, `/action_details/sent_emails.json`.

## Prerequisites

- Completed `salesloft-core-workflow-a`
- People and cadences already configured

## Instructions

### Step 1: List Email Activities

```typescript
import axios from 'axios';
const api = axios.create({
  baseURL: 'https://api.salesloft.com/v2',
  headers: { Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}` },
});

// Get email activities for a specific person
const { data: emails } = await api.get('/activities/emails.json', {
  params: {
    person_id: 1234,
    per_page: 50,
    sort_by: 'updated_at',
    sort_direction: 'DESC',
  },
});

emails.data.forEach((email: any) => {
  console.log(`${email.subject} | Status: ${email.status}`);
  console.log(`  Opens: ${email.counts.opens}, Clicks: ${email.counts.clicks}`);
  console.log(`  Replied: ${email.counts.replies > 0 ? 'Yes' : 'No'}`);
});
```

### Step 2: Log Call Activities

```typescript
// List calls with disposition data
const { data: calls } = await api.get('/activities/calls.json', {
  params: { per_page: 50, sort_by: 'created_at', sort_direction: 'DESC' },
});

calls.data.forEach((call: any) => {
  console.log(`${call.to} | Duration: ${call.duration}s`);
  console.log(`  Disposition: ${call.disposition}`);
  console.log(`  Sentiment: ${call.sentiment}`);
  console.log(`  Notes: ${call.notes || '(none)'}`);
});
```

### Step 3: Build Engagement Dashboard

```typescript
// Aggregate email engagement metrics across a cadence
async function cadenceEngagement(cadenceId: number) {
  let page = 1;
  const stats = { sent: 0, opened: 0, clicked: 0, replied: 0 };

  while (true) {
    const { data } = await api.get('/activities/emails.json', {
      params: { cadence_id: cadenceId, per_page: 100, page },
    });
    for (const email of data.data) {
      stats.sent++;
      if (email.counts.opens > 0) stats.opened++;
      if (email.counts.clicks > 0) stats.clicked++;
      if (email.counts.replies > 0) stats.replied++;
    }
    if (page >= data.metadata.paging.total_pages) break;
    page++;
  }

  return {
    ...stats,
    openRate: ((stats.opened / stats.sent) * 100).toFixed(1) + '%',
    clickRate: ((stats.clicked / stats.sent) * 100).toFixed(1) + '%',
    replyRate: ((stats.replied / stats.sent) * 100).toFixed(1) + '%',
  };
}

const metrics = await cadenceEngagement(500);
// { sent: 247, opened: 148, clicked: 32, replied: 19,
//   openRate: '59.9%', clickRate: '13.0%', replyRate: '7.7%' }
```

### Step 4: Track Step-Level Performance

```typescript
// Get steps for a cadence to see per-step analytics
const { data: steps } = await api.get('/steps.json', {
  params: { cadence_id: 500 },
});

steps.data.forEach((step: any) => {
  console.log(`Step ${step.day}: ${step.step_type} (${step.name})`);
  // step_type: 'email', 'phone', 'other', 'integration'
});
```

## Output

```
Q1 Outbound Intro | Status: sent
  Opens: 3, Clicks: 1
  Replied: No
Cadence 500 Engagement:
  Sent: 247, Open: 59.9%, Click: 13.0%, Reply: 7.7%
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Empty `activities/emails` | No emails sent yet | Verify cadence is active with enrolled people |
| `422` filter error | Invalid filter param | Check supported filter params in API docs |
| Slow pagination | Large activity history | Narrow date range with `updated_at[gt]` |

## Resources

- [Email Activities](https://developers.salesloft.com/docs/api/)
- [Call Activities](https://developers.salesloft.com/docs/api/)
- [SalesLoft API Reference](https://api.salesloft.com/swagger/index.html)

## Next Steps

For common errors, see `salesloft-common-errors`.
