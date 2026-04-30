---
name: juicebox-core-workflow-b
description: 'Execute Juicebox enrichment and outreach workflow.

  Trigger: "juicebox enrich", "candidate enrichment", "talent pool".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox — Advanced Analysis

## Overview

Build custom queries, apply multi-dimensional filters, and run cross-dataset analysis
on your Juicebox people-intelligence data. Use this workflow when you need to go beyond
standard search — comparing candidate pools across roles, analyzing skill density by
geography, or identifying talent trends over time. This is the secondary workflow;
for basic search and enrichment, see `juicebox-core-workflow-a`.

## Instructions

### Step 1: Build a Custom Query with Filters

```typescript
const query = await client.analysis.query({
  dataset: 'candidates',
  filters: [
    { field: 'skills', operator: 'contains_any', value: ['TypeScript', 'Rust', 'Go'] },
    { field: 'experience_years', operator: 'gte', value: 5 },
    { field: 'location.country', operator: 'eq', value: 'US' },
  ],
  sort: { field: 'relevance_score', order: 'desc' },
  limit: 100,
});
console.log(`Found ${query.total} candidates matching filters`);
query.results.forEach(c =>
  console.log(`  ${c.name} — ${c.title} (${c.relevance_score}/100)`)
);
```

### Step 2: Run Cross-Dataset Comparison

```typescript
const comparison = await client.analysis.compare({
  datasets: ['candidates_q1_2026', 'candidates_q4_2025'],
  group_by: 'primary_skill',
  metrics: ['count', 'avg_experience', 'avg_salary_estimate'],
});
comparison.groups.forEach(g =>
  console.log(`${g.skill}: Q1=${g.datasets[0].count} vs Q4=${g.datasets[1].count} (${g.delta > 0 ? '+' : ''}${g.delta}%)`)
);
```

### Step 3: Aggregate Skill Density by Region

```typescript
const density = await client.analysis.aggregate({
  dataset: 'candidates',
  group_by: 'location.metro_area',
  metric: 'skill_density',
  skill_filter: ['ML Engineering', 'Data Science'],
  top_n: 10,
});
density.regions.forEach(r =>
  console.log(`${r.metro}: ${r.candidate_count} candidates, density=${r.density_score}`)
);
```

### Step 4: Export Analysis Results

```typescript
const exportJob = await client.analysis.export({
  query_id: query.id,
  format: 'csv',
  fields: ['name', 'email', 'primary_skill', 'experience_years', 'location'],
});
console.log(`Export ready: ${exportJob.download_url} (${exportJob.row_count} rows)`);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `400 Invalid filter` | Unsupported operator for field type | Check field schema with `client.schema.fields()` |
| `404 Dataset not found` | Stale dataset ID or typo | List datasets with `client.datasets.list()` |
| `408 Query timeout` | Too many filters on large dataset | Add `limit` or narrow date range |
| `429 Rate limited` | Exceeded analysis quota | Implement backoff; check plan limits |
| Partial comparison data | One dataset has sparse coverage | Expected — use `include_nulls: true` for completeness |

## Output

A successful workflow produces filtered candidate lists with relevance scores,
cross-dataset comparison tables showing talent market shifts, and regional
skill-density rankings. Results can be exported as CSV for downstream reporting.

## Resources

- [Juicebox API Docs](https://docs.juicebox.work/api)

## Next Steps

See `juicebox-sdk-patterns` for authentication and query builder helpers.
