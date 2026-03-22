---
name: salesloft-core-workflow-a
description: |
  Manage SalesLoft people, cadences, and email steps via the REST API.
  Use when building prospect management, enrolling people in cadences,
  or automating outbound sales sequences.
  Trigger: "salesloft cadence", "salesloft people", "salesloft outbound sequence".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Core Workflow A: People & Cadences

## Overview

The primary SalesLoft workflow: manage people records, build cadences (multi-step outbound sequences), and enroll prospects. Uses REST API v2 endpoints: `/people.json`, `/cadences.json`, `/cadence_memberships.json`, `/steps.json`.

## Prerequisites

- Completed `salesloft-install-auth` setup
- Understanding of SalesLoft cadence model (cadences contain steps, people are enrolled via memberships)

## Instructions

### Step 1: Search and Deduplicate People

```typescript
import axios from 'axios';
const api = axios.create({
  baseURL: 'https://api.salesloft.com/v2',
  headers: { Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}` },
});

// Search by email to avoid duplicates (supports array filter)
async function findOrCreatePerson(email: string, attrs: Record<string, any>) {
  const { data: existing } = await api.get('/people.json', {
    params: { email_addresses: [email] },
  });

  if (existing.data.length > 0) {
    console.log(`Found existing: ${existing.data[0].id}`);
    return existing.data[0];
  }

  const { data: created } = await api.post('/people.json', {
    email_address: email, ...attrs,
  });
  console.log(`Created: ${created.data.id}`);
  return created.data;
}
```

### Step 2: List and Select Cadences

```typescript
// List cadences -- filter by team_cadence, current_state
const { data: cadences } = await api.get('/cadences.json', {
  params: { team_cadence: true, per_page: 50 },
});

// Each cadence has: id, name, current_state (draft|active|paused|archived)
// counts.people_count, cadence_framework_id, team_cadence
const activeCadences = cadences.data.filter(
  (c: any) => c.current_state === 'active'
);
console.log(`Active cadences: ${activeCadences.length}`);
```

### Step 3: Enroll Person in Cadence

```typescript
// Create a cadence membership to enroll a person
async function enrollInCadence(personId: number, cadenceId: number) {
  try {
    const { data } = await api.post('/cadence_memberships.json', {
      person_id: personId,
      cadence_id: cadenceId,
    });
    console.log(`Enrolled person ${personId} in cadence ${data.data.cadence.name}`);
    return data.data;
  } catch (err: any) {
    if (err.response?.status === 422) {
      console.warn('Person already enrolled or cadence not active');
    }
    throw err;
  }
}
```

### Step 4: Bulk Import with Cadence Assignment

```typescript
// Import a CSV of prospects and enroll in a cadence
async function bulkEnroll(prospects: Array<{ email: string; name: string }>, cadenceId: number) {
  const results = { enrolled: 0, skipped: 0, errors: 0 };

  for (const prospect of prospects) {
    try {
      const [first, ...rest] = prospect.name.split(' ');
      const person = await findOrCreatePerson(prospect.email, {
        first_name: first, last_name: rest.join(' '),
      });
      await enrollInCadence(person.id, cadenceId);
      results.enrolled++;
    } catch {
      results.errors++;
    }
  }
  return results; // { enrolled: 47, skipped: 2, errors: 1 }
}
```

## Output

```
Found existing: 1234
Created: 5678
Enrolled person 5678 in cadence Q1 Outbound
Active cadences: 3
Bulk result: { enrolled: 47, skipped: 2, errors: 1 }
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422` on create person | Missing `email_address` | Required field |
| `422` on enrollment | Person already in cadence | Check memberships first |
| `404` cadence | Cadence archived or deleted | Verify cadence `current_state` |
| `429` bulk import | Rate limit (600 cost/min) | Add delay between batches |

## Resources

- [List People](https://developers.salesloft.com/docs/api/people-index/)
- [List Cadences](https://developers.salesloft.com/docs/api/cadences-index/)
- [Cadence Memberships](https://developers.salesloft.com/docs/api/1.0/public-api-v-1-person-cadence-memberships-index/)
- [Cadence Imports](https://developers.salesloft.com/docs/platform/cadence-imports/introduction/)

## Next Steps

For activity tracking and email analytics, see `salesloft-core-workflow-b`.
