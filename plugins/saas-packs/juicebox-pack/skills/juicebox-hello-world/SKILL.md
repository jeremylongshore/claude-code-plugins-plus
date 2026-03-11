---
name: juicebox-hello-world
description: |
  Create a minimal working Juicebox example.
  Use when getting started with Juicebox, creating your first search,
  or testing basic people search functionality.
  Trigger with phrases like "juicebox hello world", "first juicebox search",
  "simple juicebox example", "test juicebox".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Hello World

## Overview
Create a minimal working example to search for people using Juicebox AI.

## Prerequisites
- Juicebox SDK installed (`juicebox-install-auth` completed)
- Valid API key configured
- Node.js or Python environment

## Instructions

### Step 1: Create Search Script
```typescript
// search.ts
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({
  apiKey: process.env.JUICEBOX_API_KEY
});

async function searchPeople() {
  const results = await client.search.people({
    query: 'software engineer at Google',
    limit: 5
  });

  console.log(`Found ${results.total} people`);
  results.profiles.forEach(profile => {
    console.log(`- ${profile.name} | ${profile.title} at ${profile.company}`);
  });
}

searchPeople();
```

### Step 2: Run the Search
```bash
npx ts-node search.ts
```

### Step 3: Verify Output
Expected output:
```
Found 150 people
- Jane Smith | Senior Software Engineer at Google
- John Doe | Staff Engineer at Google
- ...
```

## Output
- Working search script
- Console output with search results
- Profile data including name, title, company

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty Results | Query too specific | Broaden search terms |
| Timeout | Large result set | Add `limit` parameter |
| Invalid Query | Malformed syntax | Check query format |

## Examples

### Python Example
```python
from juicebox import JuiceboxClient
import os

client = JuiceboxClient(api_key=os.environ.get('JUICEBOX_API_KEY'))

results = client.search.people(
    query='product manager in San Francisco',
    limit=10
)

for profile in results.profiles:
    print(f"- {profile.name} | {profile.title}")
```

### Advanced Search
```typescript
const results = await client.search.people({
  query: 'senior engineer',
  filters: {
    location: 'New York',
    company_size: '1000+',  # 1000: 1 second in ms
    experience_years: { min: 5 }
  },
  limit: 20
});
```

## Resources
- [Search API Reference](https://juicebox.ai/docs/api/search)
- [Query Syntax Guide](https://juicebox.ai/docs/queries)

## Next Steps
After your first search, explore `juicebox-sdk-patterns` for production-ready code.