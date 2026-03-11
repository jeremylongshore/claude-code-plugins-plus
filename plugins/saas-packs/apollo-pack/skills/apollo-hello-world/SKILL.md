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
---
# Apollo Hello World

## Overview
Minimal working example demonstrating core Apollo.io functionality - searching for people and enriching contact data.

## Prerequisites
- Completed `apollo-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import axios from 'axios';

const apolloClient = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  headers: { 'Content-Type': 'application/json' },
  params: { api_key: process.env.APOLLO_API_KEY },
});
```

### Step 3: Search for People
```typescript
async function searchPeople() {
  const response = await apolloClient.post('/people/search', {
    q_organization_domains: ['apollo.io'],
    page: 1,
    per_page: 10,
  });

  console.log('Found contacts:', response.data.people.length);
  response.data.people.forEach((person: any) => {
    console.log(`- ${person.name} (${person.title})`);
  });
}

searchPeople().catch(console.error);
```

## Output
- Working code file with Apollo client initialization
- Successful API response with contact data
- Console output showing:
```
Found contacts: 10
- John Smith (VP of Sales)
- Jane Doe (Account Executive)
...
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check APOLLO_API_KEY environment variable |
| 422 Unprocessable | Invalid request body | Verify request payload format |
| 429 Rate Limited | Too many requests | Wait and retry with exponential backoff |
| Empty Results | No matching contacts | Broaden search criteria |

## Examples

### TypeScript Example - People Search
```typescript
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
});

interface Person {
  id: string;
  name: string;
  title: string;
  email: string;
  organization: { name: string };
}

async function main() {
  // Search for people at a company
  const { data } = await client.post('/people/search', {
    q_organization_domains: ['stripe.com'],
    person_titles: ['engineer', 'developer'],
    page: 1,
    per_page: 5,
  });

  console.log('People Search Results:');
  data.people.forEach((person: Person) => {
    console.log(`  ${person.name} - ${person.title} at ${person.organization?.name}`);
  });
}

main().catch(console.error);
```

### Python Example - Company Enrichment
```python
import os
import requests

APOLLO_API_KEY = os.environ.get('APOLLO_API_KEY')
BASE_URL = 'https://api.apollo.io/v1'

def enrich_company(domain: str):
    response = requests.get(
        f'{BASE_URL}/organizations/enrich',
        params={
            'api_key': APOLLO_API_KEY,
            'domain': domain,
        }
    )
    return response.json()

if __name__ == '__main__':
    company = enrich_company('apollo.io')
    org = company.get('organization', {})
    print(f"Company: {org.get('name')}")
    print(f"Industry: {org.get('industry')}")
    print(f"Employees: {org.get('estimated_num_employees')}")
```

## Resources
- [Apollo People Search API](https://apolloio.github.io/apollo-api-docs/#people-api)
- [Apollo Organization API](https://apolloio.github.io/apollo-api-docs/#organizations-api)
- [Apollo API Examples](https://apolloio.github.io/apollo-api-docs/#examples)

## Next Steps
Proceed to `apollo-local-dev-loop` for development workflow setup.