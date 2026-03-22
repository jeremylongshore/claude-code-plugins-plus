---
name: apollo-hello-world
description: |
  Create a minimal working Apollo.io example.
  Use when starting a new Apollo integration, testing your setup,
  or learning basic Apollo API patterns.
  Trigger with phrases like "apollo hello world", "apollo example",
  "apollo quick start", "simple apollo code", "test apollo api".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, api, testing]

---
# Apollo Hello World

## Overview
Minimal working example demonstrating the three core Apollo.io API operations: people search, person enrichment, and organization enrichment. Uses the correct `x-api-key` header and `api.apollo.io/api/v1/` base URL.

## Prerequisites
- Completed `apollo-install-auth` setup
- Valid API key configured in `APOLLO_API_KEY` environment variable

## Instructions

### Step 1: Search for People (No Credits Consumed)
The People API Search endpoint finds contacts in Apollo's 275M+ database. This endpoint is **free** — it does not consume enrichment credits, but it also does not return emails or phone numbers.

```typescript
// hello-apollo.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': process.env.APOLLO_API_KEY!,
  },
});

// People Search — POST /mixed_people/api_search
async function searchPeople() {
  const { data } = await client.post('/mixed_people/api_search', {
    q_organization_domains_list: ['apollo.io'],
    person_titles: ['engineer'],
    person_seniorities: ['senior', 'manager'],
    page: 1,
    per_page: 10,
  });

  console.log(`Found ${data.pagination.total_entries} contacts`);
  data.people.forEach((person: any) => {
    console.log(`  ${person.name} — ${person.title} at ${person.organization?.name}`);
  });
  return data;
}

searchPeople().catch(console.error);
```

### Step 2: Enrich a Single Person (Consumes 1 Credit)
The People Enrichment endpoint returns full contact details including email and phone.

```typescript
// Enrich by email, LinkedIn URL, or name+domain combo
async function enrichPerson() {
  const { data } = await client.post('/people/match', {
    email: 'tim@apollo.io',
    // Alternative identifiers:
    // linkedin_url: 'https://www.linkedin.com/in/...',
    // first_name: 'Tim', last_name: 'Zheng', organization_domain: 'apollo.io',
    reveal_personal_emails: false,
    reveal_phone_number: false,
  });

  if (!data.person) {
    console.log('No match found');
    return;
  }

  const p = data.person;
  console.log(`Name:     ${p.name}`);
  console.log(`Title:    ${p.title}`);
  console.log(`Email:    ${p.email}`);
  console.log(`Company:  ${p.organization?.name}`);
  console.log(`LinkedIn: ${p.linkedin_url}`);
}
```

### Step 3: Enrich an Organization (Consumes 1 Credit)
```typescript
// Organization Enrichment — GET /organizations/enrich
async function enrichOrg() {
  const { data } = await client.get('/organizations/enrich', {
    params: { domain: 'apollo.io' },
  });

  const org = data.organization;
  if (!org) { console.log('No org found'); return; }

  console.log(`Company:    ${org.name}`);
  console.log(`Industry:   ${org.industry}`);
  console.log(`Employees:  ${org.estimated_num_employees}`);
  console.log(`Revenue:    ${org.annual_revenue_printed}`);
  console.log(`HQ:         ${org.city}, ${org.state}, ${org.country}`);
  console.log(`Tech Stack: ${org.current_technologies?.slice(0, 5).map((t: any) => t.name).join(', ')}`);
}
```

### Step 4: Python Equivalent
```python
import os, requests

API_KEY = os.environ['APOLLO_API_KEY']
BASE = 'https://api.apollo.io/api/v1'
HEADERS = {'Content-Type': 'application/json', 'x-api-key': API_KEY}

# People search (free)
resp = requests.post(f'{BASE}/mixed_people/api_search', headers=HEADERS, json={
    'q_organization_domains_list': ['apollo.io'],
    'person_titles': ['engineer'],
    'page': 1, 'per_page': 5,
})
for p in resp.json().get('people', []):
    print(f"  {p['name']} — {p.get('title', 'N/A')}")

# Org enrichment (1 credit)
resp = requests.get(f'{BASE}/organizations/enrich',
    headers=HEADERS, params={'domain': 'apollo.io'})
org = resp.json().get('organization', {})
print(f"Company: {org.get('name')} ({org.get('estimated_num_employees')} employees)")
```

## Output
- People search results (name, title, company — no emails)
- Enriched person with email, phone, LinkedIn URL
- Enriched organization with industry, headcount, revenue, tech stack

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Missing or invalid `x-api-key` header | Check `APOLLO_API_KEY` env var |
| 422 Unprocessable | Malformed request body | Verify JSON payload structure |
| 429 Rate Limited | Exceeded requests/minute | Wait and retry with exponential backoff |
| Empty `people` array | No matches for filters | Broaden titles/seniority or use different domain |

## Resources
- [People API Search](https://docs.apollo.io/reference/people-api-search)
- [People Enrichment](https://docs.apollo.io/reference/people-enrichment)
- [Organization Enrichment](https://docs.apollo.io/reference/organization-enrichment)
- [Find People Using Filters](https://docs.apollo.io/docs/find-people-using-filters)

## Next Steps
Proceed to `apollo-local-dev-loop` for development workflow setup.
