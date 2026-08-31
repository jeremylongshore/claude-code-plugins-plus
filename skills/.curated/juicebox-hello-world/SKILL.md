---
name: juicebox-hello-world
description: 'Create a minimal Juicebox people search example.

  Trigger: "juicebox hello world", "first people search", "test juicebox".

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
# Juicebox Hello World

## Overview

Three examples: natural language people search, profile enrichment, and contact data from 800M+ profiles.

## Instructions

### Example 1: Natural Language Search

```typescript
import { JuiceboxClient } from '@juicebox/sdk';
const client = new JuiceboxClient({ apiKey: process.env.JUICEBOX_API_KEY });

const results = await client.search({
  query: 'senior ML engineer at FAANG with PhD in Bay Area',
  limit: 10,
  filters: { experience_years: { min: 5 } }
});
results.profiles.forEach(p =>
  console.log(`${p.name} | ${p.title} at ${p.company} | ${p.location}`)
);
```

### Example 2: Profile Enrichment

```typescript
const enriched = await client.enrich({
  linkedin_url: 'https://linkedin.com/in/example',
  fields: ['skills', 'experience', 'education', 'contact']
});
console.log(`Skills: ${enriched.skills.join(', ')}`);
if (enriched.tech_profile?.github) {
  console.log(`GitHub: ${enriched.tech_profile.github.repos} repos`);
}
```

### Example 3: Contact Data (Python)

```python
results = client.search(query='PM fintech NYC', limit=5, include_contact=True)
for p in results.profiles:
    email = p.contact.email if p.contact else 'N/A'
    print(f"{p.name} | {p.title} | {email}")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Empty results | Query too narrow | Broaden terms or remove filters |
| Partial contact | Limited coverage | Not all profiles have contact data |

## Prerequisites

- A sandbox workspace, synthetic prospects, documented source authority, approved destination, suppression policy, and deletion path for test artifacts.

## Output

Return an onboarding receipt with workspace, source-authority result, input/accepted/quarantined counts, suppression result, destination, export-count assertion, retention date, and cleanup state. Do not include names, contact details, enrichment values, or credentials.

## Examples

Run a synthetic prospect fixture and record `workspace=hello-sandbox; source=approved; accepted=2; quarantined=0; suppression=pass; contacts_exported=0; cleanup=complete`.

## Resources

- [Search API](https://docs.juicebox.work/api/search)
- [PeopleGPT](https://juicebox.ai/peoplegpt)

## Next Steps

Explore `juicebox-sdk-patterns` for production code.
