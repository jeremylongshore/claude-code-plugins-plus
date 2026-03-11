# Apollo Local Dev Loop - Implementation Guide

> Full implementation details and code examples for the `apollo-local-dev-loop` skill.

# Apollo Local Dev Loop

## Overview
Set up efficient local development workflow for Apollo.io integrations with proper environment management, testing, and debugging.

## Prerequisites
- Completed `apollo-install-auth` setup
- Node.js 18+ or Python 3.10+
- Git repository initialized

## Instructions

### Step 1: Environment Setup
```bash
# Create environment files
touch .env .env.example .env.test

# Add to .gitignore
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

```bash
# .env.example (commit this)
APOLLO_API_KEY=your-api-key-here
APOLLO_RATE_LIMIT=100
APOLLO_ENV=development
```

### Step 2: Create Development Client
```typescript
// src/lib/apollo-dev.ts
import axios from 'axios';

const isDev = process.env.NODE_ENV !== 'production';

export const apolloClient = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
});

// Add request logging in development
if (isDev) {
  apolloClient.interceptors.request.use((config) => {
    console.log(`[Apollo] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  });

  apolloClient.interceptors.response.use(
    (response) => {
      console.log(`[Apollo] Response: ${response.status}`);
      return response;
    },
    (error) => {
      console.error(`[Apollo] Error: ${error.response?.status}`, error.message);
      return Promise.reject(error);
    }
  );
}
```

### Step 3: Create Mock Server for Testing
```typescript
// src/mocks/apollo-mock.ts
import { rest } from 'msw';

export const apolloHandlers = [
  rest.post('https://api.apollo.io/v1/people/search', (req, res, ctx) => {
    return res(
      ctx.json({
        people: [
          { id: '1', name: 'Test User', title: 'Engineer', email: 'test@example.com' },
        ],
        pagination: { page: 1, per_page: 10, total_entries: 1 },
      })
    );
  }),

  rest.get('https://api.apollo.io/v1/organizations/enrich', (req, res, ctx) => {
    return res(
      ctx.json({
        organization: {
          name: 'Test Company',
          domain: 'test.com',
          industry: 'Technology',
        },
      })
    );
  }),
];
```

### Step 4: Development Scripts
```json
{
  "scripts": {
    "dev": "NODE_ENV=development tsx watch src/index.ts",
    "dev:mock": "MOCK_APOLLO=true npm run dev",
    "test:apollo": "vitest run src/**/*.apollo.test.ts",
    "apollo:quota": "tsx scripts/check-apollo-quota.ts"
  }
}
```

### Step 5: Quota Monitoring Script
```typescript
// scripts/check-apollo-quota.ts
import { apolloClient } from '../src/lib/apollo-dev';

async function checkQuota() {
  try {
    const { data } = await apolloClient.get('/auth/health');
    console.log('API Status:', data);
    // Note: Apollo doesn't expose quota directly, track usage manually
  } catch (error: any) {
    if (error.response?.status === 429) {
      console.error('Rate limited! Wait before making more requests.');
    }
  }
}

checkQuota();
```

## Output
- Environment file structure (.env, .env.example)
- Development client with logging interceptors
- Mock server for testing without API calls
- npm scripts for development workflow
- Quota monitoring utility

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing API Key | .env not loaded | Run `source .env` or use dotenv |
| Mock Not Working | MSW not configured | Ensure setupServer is called |
| Rate Limited in Dev | Too many test calls | Use mock server for tests |
| Stale Credentials | Key rotated | Update .env with new key |

## Examples

### Watch Mode Development
```bash
# Terminal 1: Run dev server with watch
npm run dev

# Terminal 2: Test API calls
curl -X POST http://localhost:3000/api/apollo/search \
  -H "Content-Type: application/json" \
  -d '{"domain": "stripe.com"}'
```

### Testing with Mocks
```typescript
// src/services/apollo.apollo.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { setupServer } from 'msw/node';
import { apolloHandlers } from '../mocks/apollo-mock';
import { searchPeople } from './apollo';

const server = setupServer(...apolloHandlers);

beforeAll(() => server.listen());
afterAll(() => server.close());

describe('Apollo Service', () => {
  it('searches for people', async () => {
    const results = await searchPeople({ domain: 'test.com' });
    expect(results.people).toHaveLength(1);
    expect(results.people[0].name).toBe('Test User');
  });
});
```

## Resources
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Testing Framework](https://vitest.dev/)
- [dotenv Documentation](https://github.com/motdotla/dotenv)

## Next Steps
Proceed to `apollo-sdk-patterns` for production-ready code patterns.
