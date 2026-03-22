---
name: linktree-core-workflow-b
description: |
  Execute Linktree secondary workflow: Analytics & Insights.
  Trigger: "linktree analytics & insights", "secondary linktree workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree — Analytics & Insights

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: Get Link Analytics
```typescript
const analytics = await client.analytics.get({
  profile_id: profile.id,
  period: 'last_30_days'
});
console.log(`Total views: ${analytics.views}`);
console.log(`Total clicks: ${analytics.clicks}`);
console.log(`CTR: ${(analytics.clicks / analytics.views * 100).toFixed(1)}%`);
```

### Step 2: Per-Link Performance
```typescript
const linkStats = await client.analytics.byLink({
  profile_id: profile.id,
  period: 'last_7_days'
});
linkStats.forEach(s =>
  console.log(`${s.title}: ${s.clicks} clicks (${s.unique_visitors} unique)`)
);
```

### Step 3: Audience Insights
```typescript
const audience = await client.analytics.audience({ profile_id: profile.id });
console.log('Top locations:', audience.locations.slice(0, 5));
console.log('Top referrers:', audience.referrers.slice(0, 5));
console.log('Device split:', audience.devices);
```

## Resources
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-common-errors`.
