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
---
# Apollo Core Workflow A: Lead Search & Enrichment

## Overview
Implement the primary Apollo.io workflow for searching leads and enriching contact/company data via the REST API (`https://api.apollo.io/v1`). This is the core use case for B2B sales intelligence — find decision-makers at target companies and enrich their profiles.

## Prerequisites
- Completed `apollo-install-auth` setup
- Valid Apollo API credentials with search permissions
- Understanding of your Ideal Customer Profile (ICP)

## Instructions

### Step 1: Search for People by Company Domain
```typescript
// src/workflows/lead-search.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  headers: { 'Content-Type': 'application/json' },
  params: { api_key: process.env.APOLLO_API_KEY },
});

interface PersonSearchParams {
  domains: string[];
  titles?: string[];
  seniorityLevels?: string[];
  page?: number;
  perPage?: number;
}

async function searchPeople(params: PersonSearchParams) {
  const { data } = await client.post('/people/search', {
    q_organization_domains: params.domains,
    person_titles: params.titles,
    person_seniorities: params.seniorityLevels,  // "vp", "director", "c_suite"
    page: params.page ?? 1,
    per_page: params.perPage ?? 25,
  });

  return {
    people: data.people,
    total: data.pagination.total_entries,
    page: data.pagination.page,
  };
}
```

### Step 2: Search for Organizations
```typescript
// src/workflows/org-search.ts
interface OrgSearchParams {
  keywords?: string[];
  locations?: string[];       // e.g., ["United States"]
  employeeRange?: [number, number];  // e.g., [50, 500]
  industries?: string[];
}

async function searchOrganizations(params: OrgSearchParams) {
  const { data } = await client.post('/organizations/search', {
    q_keywords: params.keywords?.join(' '),
    organization_locations: params.locations,
    organization_num_employees_ranges: params.employeeRange
      ? [`${params.employeeRange[0]},${params.employeeRange[1]}`]
      : undefined,
    organization_industry_tag_ids: params.industries,
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
  }));
}
```

### Step 3: Enrich a Person by Email or LinkedIn
```typescript
// src/workflows/enrich.ts
async function enrichPerson(params: {
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
  });

  if (!data.person) return null;

  return {
    id: data.person.id,
    name: data.person.name,
    title: data.person.title,
    email: data.person.email,
    phone: data.person.phone_numbers?.[0]?.sanitized_number,
    company: data.person.organization?.name,
    linkedinUrl: data.person.linkedin_url,
    city: data.person.city,
    state: data.person.state,
  };
}
```

### Step 4: Enrich an Organization by Domain
```typescript
async function enrichOrganization(domain: string) {
  const { data } = await client.get('/organizations/enrich', {
    params: { domain },
  });

  if (!data.organization) return null;

  return {
    id: data.organization.id,
    name: data.organization.name,
    industry: data.organization.industry,
    employees: data.organization.estimated_num_employees,
    revenue: data.organization.annual_revenue_printed,
    techStack: data.organization.current_technologies?.map((t: any) => t.name),
    headquarters: `${data.organization.city}, ${data.organization.state}`,
    description: data.organization.short_description,
  };
}
```

### Step 5: Build a Combined Lead Pipeline
```typescript
async function buildLeadPipeline(targetDomains: string[]) {
  const leads: any[] = [];

  for (const domain of targetDomains) {
    // Enrich the company
    const org = await enrichOrganization(domain);
    if (!org) continue;

    // Find decision-makers
    const { people } = await searchPeople({
      domains: [domain],
      seniorityLevels: ['vp', 'director', 'c_suite'],
    });

    for (const person of people) {
      leads.push({
        ...person,
        company: org,
        score: scoreLead(person, org),
      });
    }
  }

  return leads.sort((a, b) => b.score - a.score);
}

function scoreLead(person: any, org: any): number {
  let score = 0;
  if (person.email) score += 30;
  if (person.phone_numbers?.length) score += 20;
  if (['c_suite', 'vp'].includes(person.seniority)) score += 25;
  if (org.employees >= 50 && org.employees <= 1000) score += 15;
  if (person.linkedin_url) score += 10;
  return score;
}
```

## Output
- Paginated people search results with filtering by title and seniority
- Organization search with firmographic filters (size, industry, location)
- Person enrichment returning email, phone, title, and company
- Organization enrichment returning tech stack, revenue, and headcount
- Combined lead pipeline with scoring and ranking

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty results | Too narrow criteria | Broaden seniority levels or remove title filter |
| Missing emails | Contact not in Apollo database | Try enrichment via LinkedIn URL instead |
| 429 Rate Limited | Too many enrichment calls | Batch requests with delays between calls |
| Invalid domain | Domain does not resolve | Validate domains before searching |

## Examples

### Quick ICP Search
```typescript
// Find Series B SaaS companies with 50-500 employees
const companies = await searchOrganizations({
  keywords: ['SaaS', 'B2B'],
  employeeRange: [50, 500],
  locations: ['United States'],
});

// Find VPs of Sales at those companies
for (const company of companies.slice(0, 10)) {
  const { people } = await searchPeople({
    domains: [company.domain],
    titles: ['VP Sales', 'Head of Sales', 'VP Revenue'],
  });
  console.log(`${company.name}: ${people.length} contacts found`);
}
```

## Resources
- [Apollo People Search API](https://apolloio.github.io/apollo-api-docs/#search-for-people)
- [Apollo Organization Enrichment](https://apolloio.github.io/apollo-api-docs/#enrich-organization)
- [Apollo Person Match/Enrichment](https://apolloio.github.io/apollo-api-docs/#people-enrichment)

## Next Steps
Proceed to `apollo-core-workflow-b` for email sequences and outreach.
