---
name: customerio-event-tracking
description: |
  Execute Customer.io secondary workflow: Event Tracking & Segmentation.
  Use when tracking product usage events to trigger messages,
  or building behavioral segments for campaign targeting.
  Trigger with phrases like "customerio track events",
  "track user events with customerio".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Event Tracking & Segmentation

## Overview
Track user events and build dynamic segments for targeted messaging.
The data workflow that powers personalized communication.


## Prerequisites
- Completed `customerio-install-auth` setup
- Familiarity with `customerio-campaign-delivery`
- Valid API credentials configured

## Instructions

### Step 1: Track User Events
```typescript
await client.events.track({
  userId: user.id,
  event: 'feature_activated',
  properties: {
    feature: 'advanced-search',
    plan: user.plan,
    timestamp: new Date().toISOString(),
  },
});

```

### Step 2: Build Dynamic Segments
```typescript
const segment = await client.segments.create({
  name: 'Activated Advanced Search',
  filters: [
    { event: 'feature_activated', property: 'feature', value: 'advanced-search' },
    { field: 'created_at', operator: 'after', value: '2026-01-01' },
  ],
});

```

### Step 3: Trigger Automated Flows
```typescript
await client.automations.create({
  trigger: { event: 'feature_activated', property: 'feature', value: 'advanced-search' },
  actions: [
    { type: 'send_email', templateId: 'advanced-search-tips', delay: '1h' },
    { type: 'send_email', templateId: 'advanced-search-power-user', delay: '7d' },
  ],
});

```

## Output
- Completed Event Tracking & Segmentation execution

- Results from Customer.io API

- Success confirmation or error details

## Error Handling
| Aspect | Campaign & Message Delivery | Event Tracking & Segmentation |
|--------|------------|------------|
| Use Case | sending targeted email campaigns to user segments | tracking product usage events to trigger messages |
| Complexity | Medium | Medium |
| Performance | Standard | Events are async (fire-and-forget) |

## Examples

### Complete Workflow
```typescript
// Event-driven messaging pipeline
async function onUserAction(userId: string, action: string, props: Record<string, any>) {
  await client.events.track({ userId, event: action, properties: props });
  // Segments and automations react automatically
}

```

### Error Recovery
```typescript
try {
  await client.events.track(eventData);
} catch (err) {
  if (err.status === 413) {
    console.error('Event payload too large. Max 64KB per event.');
  }
  // Events should be fire-and-forget — log but don't block the user
  console.error('Event tracking failed:', err.message);
}

```

## Resources
- [Customer.io Documentation](https://docs.customerio.com)
- [Customer.io API Reference](https://docs.customerio.com/api)

## Next Steps
For common errors, see `customerio-common-errors`.