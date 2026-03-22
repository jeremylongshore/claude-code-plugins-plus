---
name: juicebox-core-workflow-b
description: |
  Execute Juicebox enrichment and outreach workflow.
  Trigger: "juicebox enrich", "candidate enrichment", "talent pool".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Enrichment & Outreach

## Overview
Enrich profiles with AI Skills Maps, tech profiles, contact data. Build talent pools and automated outreach sequences.

## Instructions

### Step 1: Bulk Enrichment
```typescript
const enriched = await Promise.all(
  profiles.map(p => client.enrich({
    profile_id: p.id,
    fields: ['skills_map', 'tech_profile', 'research_profile', 'contact']
  }))
);
enriched.forEach(ep => {
  console.log(`${ep.name} — ${ep.skills_map.top_skills.join(', ')}`);
  if (ep.tech_profile?.github) console.log(`  GitHub: ${ep.tech_profile.github.repos} repos`);
});
```

### Step 2: Talent Pool
```typescript
const pool = await client.pools.create({
  name: 'Senior Backend Q1 2026',
  profiles: enriched.map(p => p.id),
  tags: ['backend', 'senior']
});
```

### Step 3: Outreach Sequence
```typescript
await client.outreach.create({
  pool_id: pool.id,
  steps: [
    { type: 'email', delay_days: 0, subject: 'Opportunity at {{company}}',
      body: 'Hi {{first_name}}, I saw your work on {{top_skill}}...' },
    { type: 'email', delay_days: 3, subject: 'Following up' },
    { type: 'linkedin', delay_days: 5, message: 'Hi {{first_name}}...' }
  ]
});
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Partial enrichment | Limited profile data | Expected for some profiles |
| Email bounce | Invalid address | Use verified contacts only |

## Resources
- [Enrichment API](https://docs.juicebox.work/api/enrich)

## Next Steps
For errors, see `juicebox-common-errors`.
