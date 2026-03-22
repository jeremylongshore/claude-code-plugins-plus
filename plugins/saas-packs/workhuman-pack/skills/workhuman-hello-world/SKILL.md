---
name: workhuman-hello-world
description: |
  Workhuman hello world for employee recognition and rewards API.
  Use when integrating Workhuman Social Recognition,
  or building recognition workflows with HRIS systems.
  Trigger: "workhuman hello world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, recognition, workhuman]
compatible-with: claude-code
---

# Workhuman Hello World

## Overview

Create a recognition nomination and list recent recognitions -- the two fundamental Workhuman API operations. Workhuman Social Recognition enables peer-to-peer and manager-to-employee recognition with points-based rewards.

## Instructions

### Step 1: List Recent Recognitions

```typescript
const { data: recognitions } = await api.get('/api/v1/recognitions', {
  params: { limit: 10, sort: '-created_at' },
});

recognitions.data.forEach((rec: any) => {
  console.log(`${rec.nominator.name} recognized ${rec.recipient.name}`);
  console.log(`  Award: ${rec.award_level} | Points: ${rec.points}`);
  console.log(`  Message: ${rec.message}`);
  console.log(`  Value: ${rec.company_value}`);
});
```

### Step 2: Create a Recognition Nomination

```typescript
const nomination = await api.post('/api/v1/recognitions', {
  recipient_id: 'emp-12345',
  award_level: 'silver',
  company_value: 'innovation',
  message: 'Outstanding work on the Q1 product launch. Your innovative approach to the deployment pipeline saved the team 3 days of work.',
  points: 500,
  visibility: 'public',  // 'public', 'team', 'private'
});

console.log(`Recognition created: ${nomination.data.id}`);
console.log(`Status: ${nomination.data.status}`); // pending_approval or approved
```

### Step 3: Check Recognition Status

```typescript
const { data: status } = await api.get(`/api/v1/recognitions/${nomination.data.id}`);
console.log(`Status: ${status.status}`);
// Status: pending_approval -> approved -> delivered
```

### Step 4: List Reward Catalog

```typescript
const { data: catalog } = await api.get('/api/v1/rewards/catalog', {
  params: { category: 'gift_cards', country: 'US' },
});

catalog.items.forEach((item: any) => {
  console.log(`${item.name} - ${item.points_required} points`);
});
```

## Output

```
Jane Smith recognized Alex Johnson
  Award: Silver | Points: 500
  Message: Outstanding work on the Q1 product launch...
  Value: Innovation
Recognition created: rec-67890
Status: pending_approval
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422` on nomination | Missing required field | Include recipient, award_level, message |
| `404` recipient | Invalid employee ID | Verify against HRIS sync |
| `403` award level | Insufficient budget | Check recognition budget limits |

## Resources

- [Workhuman Social Recognition](https://www.workhuman.com/platform/social-recognition/)
- [Workhuman API](https://apitracker.io/a/workhuman)

## Next Steps

Proceed to `workhuman-local-dev-loop` for development workflow.
