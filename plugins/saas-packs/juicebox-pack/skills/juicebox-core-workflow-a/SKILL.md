---
name: juicebox-core-workflow-a
description: |
  Execute Juicebox people search workflow.
  Use when building candidate sourcing pipelines, searching for professionals,
  or implementing talent discovery features.
  Trigger with phrases like "juicebox people search", "find candidates juicebox",
  "juicebox talent search", "search professionals juicebox".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox People Search Workflow

## Overview
Implement a complete people search workflow using Juicebox AI for candidate sourcing and talent discovery.

## Prerequisites
- Juicebox SDK configured
- Understanding of search query syntax
- Knowledge of result filtering

## Instructions

### Step 1: Define Search Parameters
```typescript
// types/search.ts
export interface CandidateSearch {
  role: string;
  skills: string[];
  location?: string;
  experienceYears?: { min?: number; max?: number };
  companies?: string[];
  education?: string[];
}

export function buildSearchQuery(params: CandidateSearch): string {
  const parts = [params.role];

  if (params.skills.length > 0) {
    parts.push(`skills:(${params.skills.join(' OR ')})`);
  }

  if (params.location) {
    parts.push(`location:"${params.location}"`);
  }

  return parts.join(' AND ');
}
```

### Step 2: Implement Search Pipeline
```typescript
// workflows/candidate-search.ts
import { JuiceboxService } from '../lib/juicebox-client';

export class CandidateSearchPipeline {
  constructor(private juicebox: JuiceboxService) {}

  async searchCandidates(criteria: CandidateSearch) {
    const query = buildSearchQuery(criteria);

    // Initial broad search
    const results = await this.juicebox.searchPeople(query, {
      limit: 100,
      fields: ['name', 'title', 'company', 'location', 'skills', 'experience']
    });

    // Score and rank candidates
    const scored = results.profiles.map(profile => ({
      ...profile,
      score: this.calculateFitScore(profile, criteria)
    }));

    // Sort by fit score
    return scored.sort((a, b) => b.score - a.score);
  }

  private calculateFitScore(profile: Profile, criteria: CandidateSearch): number {
    let score = 0;

    // Skills match
    const matchedSkills = profile.skills.filter(s =>
      criteria.skills.includes(s.toLowerCase())
    );
    score += matchedSkills.length * 10;

    // Experience match
    if (criteria.experienceYears) {
      const years = profile.experienceYears || 0;
      if (years >= (criteria.experienceYears.min || 0)) {
        score += 20;
      }
    }

    return score;
  }
}
```

### Step 3: Handle Pagination
```typescript
async function* searchAllCandidates(
  juicebox: JuiceboxService,
  query: string
): AsyncGenerator<Profile> {
  let cursor: string | undefined;

  do {
    const results = await juicebox.searchPeople(query, {
      limit: 50,
      cursor
    });

    for (const profile of results.profiles) {
      yield profile;
    }

    cursor = results.nextCursor;
  } while (cursor);
}
```

## Output
- Search query builder
- Candidate scoring system
- Paginated result handling
- Ranked candidate list

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| No Results | Query too restrictive | Broaden criteria |
| Slow Response | Large dataset | Use pagination |
| Score Issues | Missing data | Handle null values |

## Examples

### Full Pipeline Usage
```typescript
const pipeline = new CandidateSearchPipeline(juiceboxService);

const candidates = await pipeline.searchCandidates({
  role: 'Senior Software Engineer',
  skills: ['typescript', 'react', 'node.js'],
  location: 'San Francisco Bay Area',
  experienceYears: { min: 5 }
});

console.log(`Found ${candidates.length} matching candidates`);
candidates.slice(0, 10).forEach(c => {
  console.log(`${c.name} (Score: ${c.score}) - ${c.title} at ${c.company}`);
});
```

## Resources
- [Search Query Syntax](https://juicebox.ai/docs/search/syntax)
- [Filtering Guide](https://juicebox.ai/docs/search/filters)

## Next Steps
After implementing search, explore `juicebox-core-workflow-b` for candidate enrichment.