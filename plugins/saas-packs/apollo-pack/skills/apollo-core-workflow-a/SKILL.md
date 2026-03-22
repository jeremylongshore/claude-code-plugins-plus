---
name: apollo-core-workflow-a
description: |
  Implement Apollo.io lead search and enrichment workflow.
  Use when building lead generation features, searching for contacts,
  or enriching prospect data from Apollo.
  Trigger with phrases like "apollo lead search", "search apollo contacts",
  "find leads in apollo", "apollo people search", "enrich contacts apollo".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, workflow]

---
# Apollo Core Workflow A: Lead Search & Enrichment

## Overview
Build the core Apollo.io prospecting pipeline: search for people and organizations, then enrich the best leads. Key distinction — **search is free** (no credits), **enrichment costs credits**. This skill uses the correct endpoints and `x-api-key` header authentication.

## Prerequisites
- Completed `apollo-install-auth` setup
- Valid Apollo API key with search + enrichment permissions
- Understanding of your Ideal Customer Profile (ICP)

## Instructions

### Step 1: Search for People (Free — No Credits)
The People API Search endpoint (`POST /mixed_people/api_search`) searches Apollo's 275M+ database. It does **not** return emails or phone numbers — use enrichment for that.

```typescript
// src/workflows/lead-search.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

interface PersonSearchParams {
  domains: string[];
  titles?: string[];
  seniorities?: string[];    // "c_suite", "vp", "director", "manager", "senior"
  locations?: string[];       // "United States", "San Francisco, California"
  page?: number;
  perPage?: number;
}

export async function searchPeople(params: PersonSearchParams) {
  const { data } = await client.post('/mixed_people/api_search', {
    q_organization_domains_list: params.domains,
    person_titles: params.titles,
    person_seniorities: params.seniorities,
    person_locations: params.locations,
    include_similar_titles: true,
    page: params.page ?? 1,
    per_page: params.perPage ?? 25,
  });

  return {
    people: data.people,
    total: data.pagination.total_entries,
    totalPages: data.pagination.total_pages,
    page: data.pagination.page,
  };
}
```

### Step 2: Search for Organizations (Free)
```typescript
// src/workflows/org-search.ts
interface OrgSearchParams {
  keywords?: string;
  locations?: string[];
  employeeRanges?: string[];  // ["1,10", "11,50", "51,200", "201,500"]
  industries?: string[];
  revenueRanges?: string[];   // ["0,1000000", "1000000,10000000"]
}

export async function searchOrganizations(params: OrgSearchParams) {
  const { data } = await client.post('/mixed_companies/search', {
    q_organization_keyword_tags: params.keywords ? [params.keywords] : undefined,
    organization_locations: params.locations,
    organization_num_employees_ranges: params.employeeRanges,
    organization_industry_tag_ids: params.industries,
    organization_revenue_ranges: params.revenueRanges,
    page: 1,
    per_page: 25,
  });

  return data.organizations.map((org: any) => ({
    id: org.id,
    name: org.name,
    domain: org.primary_domain,
    industry: org.industry,
    employees: org.estimated_num_employees,
    revenue: org.annual_revenue_printed,
    city: org.city,
    state: org.state,
  }));
}
```

### Step 3: Enrich a Single Person (1 Credit)
```typescript
// src/workflows/enrich.ts
export async function enrichPerson(params: {
  email?: string;
  linkedinUrl?: string;
  firstName?: string;
  lastName?: string;
  domain?: string;
}) {
  const { data } = await client.post('/people/match', {
    email: params.email,
    linkedin_url: params.linkedinUrl,
    first_name: params.firstName,
    last_name: params.lastName,
    organization_domain: params.domain,
    reveal_personal_emails: false,
    reveal_phone_number: true,
  });

  if (!data.person) return null;
  const p = data.person;

  return {
    id: p.id,
    name: p.name,
    title: p.title,
    email: p.email,
    phone: p.phone_numbers?.[0]?.sanitized_number,
    company: p.organization?.name,
    companyDomain: p.organization?.primary_domain,
    linkedinUrl: p.linkedin_url,
    seniority: p.seniority,
    city: p.city,
    state: p.state,
  };
}
```

### Step 4: Bulk Enrich People (Up to 10 per Call)
```typescript
export async function bulkEnrichPeople(details: Array<{
  email?: string;
  linkedin_url?: string;
  first_name?: string;
  last_name?: string;
  organization_domain?: string;
}>) {
  const { data } = await client.post('/people/bulk_match', {
    details,
    reveal_personal_emails: false,
    reveal_phone_number: false,
  });

  return (data.matches ?? []).map((match: any) => ({
    id: match.id,
    name: match.name,
    email: match.email,
    title: match.title,
    company: match.organization?.name,
  }));
}
```

### Step 5: Build a Combined Lead Pipeline
```typescript
export async function buildLeadPipeline(targetDomains: string[]) {
  const leads: any[] = [];

  for (const domain of targetDomains) {
    // Step A: Search for decision-makers (free)
    const { people } = await searchPeople({
      domains: [domain],
      seniorities: ['vp', 'director', 'c_suite'],
    });

    // Step B: Score leads before enriching (save credits)
    const worthEnriching = people.filter((p: any) => scoreLead(p) >= 50);

    // Step C: Bulk enrich top leads (costs credits)
    if (worthEnriching.length > 0) {
      const enriched = await bulkEnrichPeople(
        worthEnriching.map((p: any) => ({
          first_name: p.first_name,
          last_name: p.last_name,
          organization_domain: domain,
        })),
      );
      leads.push(...enriched);
    }
  }

  return leads.sort((a, b) => scoreLead(b) - scoreLead(a));
}

function scoreLead(person: any): number {
  let score = 0;
  if (person.email) score += 30;
  if (person.phone_numbers?.length) score += 20;
  if (['c_suite', 'vp', 'founder', 'owner'].includes(person.seniority)) score += 30;
  else if (['director'].includes(person.seniority)) score += 20;
  if (person.linkedin_url) score += 10;
  if (person.city) score += 10;
  return score;
}
```

## Output
- People search via `POST /mixed_people/api_search` (free, no credits)
- Organization search via `POST /mixed_companies/search` (free)
- Single person enrichment via `POST /people/match` (1 credit)
- Bulk enrichment via `POST /people/bulk_match` (up to 10 per call)
- Lead scoring to minimize credit spend before enriching

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty `people` array | Too narrow criteria | Broaden seniority levels, add `include_similar_titles: true` |
| `null` from enrichment | Person not in Apollo database | Try enriching via LinkedIn URL instead of name+domain |
| 429 Rate Limited | Too many requests/minute | Batch requests with 500ms delays between calls |
| 403 Forbidden | Standard key used for enrichment | Upgrade to master API key in Apollo dashboard |

## Examples

### Quick ICP Search
```typescript
// Find Series B SaaS companies with 50-500 employees
const companies = await searchOrganizations({
  keywords: 'SaaS',
  employeeRanges: ['51,200', '201,500'],
  locations: ['United States'],
});

// Find VPs of Sales at those companies
for (const company of companies.slice(0, 10)) {
  const { people, total } = await searchPeople({
    domains: [company.domain],
    titles: ['VP Sales', 'Head of Sales', 'VP Revenue'],
  });
  console.log(`${company.name} (${company.domain}): ${total} contacts`);
}
```

## Resources
- [People API Search](https://docs.apollo.io/reference/people-api-search)
- [Organization Search](https://docs.apollo.io/reference/organization-search)
- [People Enrichment](https://docs.apollo.io/reference/people-enrichment)
- [Bulk People Enrichment](https://docs.apollo.io/reference/bulk-people-enrichment)
- [Find People Using Filters](https://docs.apollo.io/docs/find-people-using-filters)

## Next Steps
Proceed to `apollo-core-workflow-b` for email sequences and outreach.
