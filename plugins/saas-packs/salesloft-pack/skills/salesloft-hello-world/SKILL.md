---
name: salesloft-hello-world
description: |
  Create a minimal working SalesLoft example — list people and create a person.
  Use when starting a new SalesLoft integration, testing your setup,
  or learning the People and Cadences API patterns.
  Trigger: "salesloft hello world", "salesloft example", "salesloft quick start".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Hello World

## Overview

List people and create a new person — the two fundamental SalesLoft API operations. Uses the REST API v2 at `https://api.salesloft.com/v2/`. All endpoints return JSON with a `data` wrapper and support pagination via `page` and `per_page` params.

## Prerequisites

- Valid OAuth token or API key (see `salesloft-install-auth`)
- `SALESLOFT_API_KEY` environment variable set

## Instructions

### Step 1: List People

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.salesloft.com/v2',
  headers: { Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}` },
});

// List people — returns paginated results
const { data } = await api.get('/people.json', {
  params: { per_page: 25, page: 1 },
});

console.log(`Total people: ${data.metadata.paging.total_count}`);
data.data.forEach((person: any) => {
  console.log(`  ${person.display_name} <${person.email_address}>`);
});
```

### Step 2: Create a Person

```typescript
// Create a new person record
const { data: created } = await api.post('/people.json', {
  email_address: 'prospect@example.com',
  first_name: 'Alex',
  last_name: 'Johnson',
  title: 'VP Engineering',
  company_name: 'Acme Corp',
  phone: '+1-555-0100',
  city: 'Austin',
  state: 'TX',
  custom_fields: {
    lead_source: 'website',
  },
});

console.log(`Created person: ${created.data.id} — ${created.data.display_name}`);
```

### Step 3: Add Person to a Cadence

```typescript
// First, list available cadences
const { data: cadences } = await api.get('/cadences.json', {
  params: { per_page: 10 },
});
const cadenceId = cadences.data[0].id;

// Add person to cadence
const { data: membership } = await api.post('/cadence_memberships.json', {
  person_id: created.data.id,
  cadence_id: cadenceId,
});
console.log(`Added to cadence: ${membership.data.cadence.name}`);
```

## Output

```
Total people: 1,247
  Alex Johnson <prospect@example.com>
Created person: 98765 — Alex Johnson
Added to cadence: Q1 Outbound Sequence
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422 Unprocessable Entity` | Missing required field (email) | Ensure `email_address` is provided |
| `409 Conflict` | Duplicate email address | Search existing people first with `?email_addresses[]=` |
| `401 Unauthorized` | Invalid/expired token | Refresh OAuth token |
| `429 Too Many Requests` | Rate limit exceeded (600 cost/min) | Back off and retry after `Retry-After` header |

## Examples

### Search People by Email

```typescript
const { data } = await api.get('/people.json', {
  params: { email_addresses: ['prospect@example.com'] },
});
```

### Update a Person

```typescript
await api.put(`/people/${personId}.json`, {
  title: 'CTO',
  company_name: 'New Corp',
});
```

### List Activities for a Person

```typescript
const { data: activities } = await api.get('/activities/emails.json', {
  params: { person_id: personId, per_page: 50 },
});
```

## Resources

- [List People Endpoint](https://developers.salesloft.com/docs/api/people-index/)
- [SalesLoft API Reference](https://api.salesloft.com/swagger/index.html)
- [Retrieving Actions, Cadences, Steps](https://developers.salesloft.com/docs/platform/api-basics/retrieving-actions-cadences-steps/)

## Next Steps

Proceed to `salesloft-local-dev-loop` for development workflow setup.
