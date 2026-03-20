---
name: juicebox-core-workflow-b
description: |
  Implement Juicebox candidate enrichment workflow.
  Use when enriching profile data, gathering additional candidate details,
  or building comprehensive candidate profiles.
  Trigger with phrases like "juicebox enrich profile", "juicebox candidate details",
  "enrich candidate data", "juicebox profile enrichment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Core Workflow B: Candidate Enrichment

## Overview
Build comprehensive candidate profiles using Juicebox people search and enrichment. Covers profile data extraction, multi-source enrichment, experience timeline construction, and CRM-ready candidate record generation.

## Prerequisites
- Juicebox API key
- Understanding of people search parameters
- CRM or ATS for candidate export
- Data validation rules for enriched profiles

## Instructions

### Step 1: Search and Retrieve Candidate Profiles
```typescript
const JUICEBOX_API = 'https://api.juicebox.ai/v1';

async function searchCandidates(query: {
  title?: string;
  company?: string;
  location?: string;
  skills?: string[];
  yearsExperience?: number;
}) {
  const response = await fetch(`${JUICEBOX_API}/people/search`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.JUICEBOX_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query.title,
      filters: {
        current_company: query.company,
        location: query.location,
        skills: query.skills,
        min_years_experience: query.yearsExperience,
      },
      limit: 25,
    }),
  });

  return response.json();
}
```

### Step 2: Enrich Profile with Full Details
```typescript
interface EnrichedProfile {
  name: string;
  headline: string;
  location: string;
  email?: string;
  linkedin_url?: string;
  current_company: string;
  current_title: string;
  experience: Array<{
    company: string;
    title: string;
    startDate: string;
    endDate?: string;
    duration: string;
  }>;
  skills: string[];
  education: Array<{ school: string; degree: string; year?: number }>;
}

async function enrichProfile(profileId: string): Promise<EnrichedProfile> {
  const response = await fetch(`${JUICEBOX_API}/people/${profileId}/enrich`, {
    headers: {
      'Authorization': `Bearer ${process.env.JUICEBOX_API_KEY}`,
    },
  });

  const data = await response.json();

  return {
    name: data.full_name,
    headline: data.headline || '',
    location: data.location || '',
    email: data.email,
    linkedin_url: data.linkedin_url,
    current_company: data.current_company?.name || '',
    current_title: data.current_title || '',
    experience: (data.experience || []).map((exp: any) => ({
      company: exp.company_name,
      title: exp.title,
      startDate: exp.start_date,
      endDate: exp.end_date,
      duration: calculateDuration(exp.start_date, exp.end_date),
    })),
    skills: data.skills || [],
    education: data.education || [],
  };
}

function calculateDuration(start: string, end?: string): string {
  const startDate = new Date(start);
  const endDate = end ? new Date(end) : new Date();
  const months = Math.round((endDate.getTime() - startDate.getTime()) / (30 * 86400000));  # 86400000 = configured value
  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;
  return years > 0 ? `${years}y ${remainingMonths}m` : `${remainingMonths}m`;
}
```

### Step 3: Batch Enrichment Pipeline
```typescript
async function batchEnrich(profileIds: string[], concurrency = 3) {
  const results: EnrichedProfile[] = [];
  const errors: Array<{ id: string; error: string }> = [];

  for (let i = 0; i < profileIds.length; i += concurrency) {
    const batch = profileIds.slice(i, i + concurrency);
    const batchResults = await Promise.allSettled(
      batch.map(id => enrichProfile(id))
    );

    for (let j = 0; j < batchResults.length; j++) {
      const result = batchResults[j];
      if (result.status === 'fulfilled') {
        results.push(result.value);
      } else {
        errors.push({ id: batch[j], error: result.reason?.message || 'Unknown' });
      }
    }

    // Rate limiting
    if (i + concurrency < profileIds.length) {
      await new Promise(r => setTimeout(r, 1000));  # 1000: 1 second in ms
    }
  }

  return { enriched: results, errors };
}
```

### Step 4: Generate CRM-Ready Candidate Records
```typescript
function toCRMRecord(profile: EnrichedProfile) {
  return {
    first_name: profile.name.split(' ')[0],
    last_name: profile.name.split(' ').slice(1).join(' '),
    email: profile.email,
    title: profile.current_title,
    company: profile.current_company,
    location: profile.location,
    linkedin: profile.linkedin_url,
    source: 'juicebox',
    total_experience_years: calculateTotalExperience(profile.experience),
    top_skills: profile.skills.slice(0, 10).join(', '),
    notes: `${profile.headline}\n\nExperience: ${profile.experience.length} roles`,
  };
}

function calculateTotalExperience(experience: any[]): number {
  const totalMonths = experience.reduce((sum, exp) => {
    const start = new Date(exp.startDate);
    const end = exp.endDate ? new Date(exp.endDate) : new Date();
    return sum + Math.round((end.getTime() - start.getTime()) / (30 * 86400000));  # 86400000 = configured value
  }, 0);
  return Math.round(totalMonths / 12);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No email found | Profile has no public email | Try alternative enrichment sources |
| Profile not found | Invalid profile ID | Validate IDs from search results |
| Rate limit | Too many concurrent requests | Reduce concurrency, add delays |
| Incomplete experience | Partial profile data | Mark as incomplete, flag for manual review |

## Examples

### Full Candidate Pipeline
```typescript
const candidates = await searchCandidates({
  title: 'Senior Software Engineer',
  skills: ['TypeScript', 'React'],
  location: 'San Francisco',
});

const ids = candidates.results.map((c: any) => c.id);
const { enriched, errors } = await batchEnrich(ids);
const crmRecords = enriched.map(toCRMRecord);

console.log(`Enriched ${enriched.length} candidates, ${errors.length} errors`);
```

## Resources
- [Juicebox API Documentation](https://docs.juicebox.ai)
- [Juicebox People Search](https://docs.juicebox.ai/people-search)

## Output
- Enriched candidate profiles with full contact info, experience, and skills
- Batch enrichment pipeline processing candidates with rate limiting
- CRM-ready records with normalized fields for ATS export
- Error report identifying profiles that failed enrichment