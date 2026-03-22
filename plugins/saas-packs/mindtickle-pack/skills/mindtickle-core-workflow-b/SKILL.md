---
name: mindtickle-core-workflow-b
description: |
  Execute MindTickle secondary workflow: Rep Performance & Readiness.
  Trigger: "mindtickle rep performance & readiness", "secondary mindtickle workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle — Rep Performance & Readiness

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: Get Readiness Scores
```typescript
const readiness = await client.readiness.scores({
  team_id: 'team_sales_west',
  period: 'last_quarter'
});
readiness.reps.forEach(r =>
  console.log(`${r.name}: ${r.readiness_score}/100 | Certifications: ${r.certs_complete}/${r.certs_total}`)
);
```

### Step 2: Analyze Call Performance
```typescript
const calls = await client.callai.analyze({
  rep_id: 'rep_123',
  period: 'last_30_days'
});
console.log(`Calls: ${calls.total}`);
console.log(`Avg talk ratio: ${calls.avg_talk_ratio}%`);
console.log(`Key topics: ${calls.top_topics.join(', ')}`);
console.log(`Coaching opportunities: ${calls.coaching_flags.length}`);
```

### Step 3: Generate Coaching Report
```typescript
const report = await client.reports.create({
  type: 'coaching_summary',
  rep_id: 'rep_123',
  period: 'last_quarter',
  include: ['readiness_trend', 'completion_gaps', 'call_analysis']
});
console.log(`Report URL: ${report.url}`);
```

## Resources
- [MindTickle Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-common-errors`.
