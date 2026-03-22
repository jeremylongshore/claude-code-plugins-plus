---
name: mindtickle-deal-pipeline
description: |
  Execute Mindtickle secondary workflow: Deal Pipeline Management.
  Use when creating deals from qualified leads,
  or updating deal stages as they progress through sales.
  Trigger with phrases like "mindtickle pipeline",
  "manage deal pipeline with mindtickle".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mindtickle]
---

# Mindtickle Deal Pipeline Management

## Overview
Create, update, and track deals through your sales pipeline stages.
The revenue workflow — move deals from qualified to closed-won.


## Prerequisites
- Completed `mindtickle-install-auth` setup
- Familiarity with `mindtickle-contact-sync`
- Valid API credentials configured

## Instructions

### Step 1: Create Deal
```typescript
const deal = await client.deals.create({
  name: `${company.name} - Enterprise License`,
  contactId: contact.id,
  companyId: company.id,
  value: 50000,
  currency: 'USD',
  pipeline: 'enterprise',
  stage: 'discovery',
  closeDate: '2026-06-30',
});

```

### Step 2: Update Deal Stage
```typescript
await client.deals.update(deal.id, {
  stage: 'proposal_sent',
  notes: 'Sent pricing proposal. Decision expected by EOW.',
  nextAction: 'follow_up',
  nextActionDate: '2026-04-05',
});

```

### Step 3: Track Pipeline Metrics
```typescript
const pipeline = await client.pipelines.get('enterprise');
const metrics = pipeline.stages.map(s => ({
  stage: s.name,
  deals: s.dealCount,
  value: s.totalValue,
}));
console.table(metrics);

```

## Output
- Completed Deal Pipeline Management execution

- Deals created and assigned to pipeline stages
- Pipeline metrics updated with stage counts and values

- Success confirmation or error details

## Error Handling
| Aspect | Contact Sync & Enrichment | Deal Pipeline Management |
|--------|------------|------------|
| Use Case | importing leads from a CSV or webhook into the CRM | creating deals from qualified leads |
| Complexity | Medium | Medium |
| Performance | Standard | Standard REST CRUD |

## Examples

### Complete Workflow
```typescript
async function moveDeal(dealId: string, newStage: string, notes: string) {
  const deal = await client.deals.update(dealId, { stage: newStage, notes });
  if (newStage === 'closed_won') {
    await client.contacts.tag(deal.contactId, 'customer');
    await notifySlack(`Deal closed: ${deal.name} — $${deal.value}`);
  }
  return deal;
}

```

### Error Recovery
```typescript
try {
  await client.deals.update(dealId, { stage: newStage });
} catch (err) {
  if (err.code === 'invalid_stage_transition') {
    console.error(`Cannot move from ${currentStage} to ${newStage} directly`);
  } else if (err.code === 'deal_locked') {
    console.error('Deal is locked (closed-won/lost). Reopen before updating.');
  } else {
    throw err;
  }
}

```

## Resources
- [Mindtickle Documentation](https://docs.mindtickle.com)
- [Mindtickle API Reference](https://docs.mindtickle.com/api)

## Next Steps
For common errors, see `mindtickle-common-errors`.