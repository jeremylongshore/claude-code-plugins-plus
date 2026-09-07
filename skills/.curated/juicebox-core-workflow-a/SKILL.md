---
name: juicebox-core-workflow-a
description: 'Execute Juicebox people search with power filters and ATS export.

  Trigger: "find candidates", "people search", "juicebox search".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.16.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox People Search Workflow

## Overview

Complete candidate sourcing: natural language search with power filters, scoring, and export to 41+ ATS systems.

## Instructions

### Step 1: Power Filter Search

```typescript
const results = await client.search({
  query: 'backend engineer distributed systems',
  filters: {
    location: ['San Francisco', 'Seattle', 'Remote'],
    experience_years: { min: 3, max: 10 },
    skills: ['Go', 'Kubernetes', 'distributed systems'],
    company_size: '100-1000',
    exclude_companies: ['CurrentEmployer']
  },
  sort: 'relevance', limit: 50
});
```

### Step 2: Score Candidates

```typescript
function scoreCandidate(profile, targetSkills: string[]) {
  let score = 0;
  const matched = profile.skills.filter(s =>
    targetSkills.some(t => s.toLowerCase().includes(t.toLowerCase()))
  );
  score += matched.length * 20;
  if (profile.experience_years >= 5) score += 30;
  return { profile, score, matchedSkills: matched };
}

const ranked = results.profiles
  .map(p => scoreCandidate(p, ['Go', 'Kubernetes']))
  .sort((a, b) => b.score - a.score);
```

### Step 3: Export to ATS

```typescript
await client.export({
  profiles: ranked.slice(0, 20).map(r => r.profile.id),
  destination: 'greenhouse',  // lever, ashby, recruiterflow, etc.
  job_id: 'job_abc123'
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Low results | Filters too strict | Relax experience or location |
| Duplicates | Overlapping searches | Deduplicate by LinkedIn URL |

## Prerequisites

- An approved hiring workflow, a sandbox workspace, documented source authority, a suppression list, and an allowlisted ATS test destination.

## Output

Produce a redacted workflow receipt with the sandbox query scope, aggregate result count, suppression outcome, destination approval, `contacts_exported=0` test assertion, owner approval, retention window, and rollback reference. Do not retain candidate records, contact details, or credentials.

## Examples

`workspace=sandbox-hiring; source=approved; query=synthetic-go-k8s; matched=20; suppression=pass; contacts_exported=0; retention=24h` is a valid pre-production receipt.

## Resources

- Search Filters
- [ATS Integrations](https://juicebox.ai/integrations)

## Next Steps

For enrichment, see `juicebox-core-workflow-b`.
