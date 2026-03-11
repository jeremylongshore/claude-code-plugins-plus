---
name: juicebox-local-dev-loop
description: |
  Configure Juicebox local development workflow.
  Use when setting up local testing, mock data, or development environment
  for Juicebox integration work.
  Trigger with phrases like "juicebox local dev", "juicebox development setup",
  "juicebox mock data", "test juicebox locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Local Dev Loop

## Overview
Configure a fast local development workflow for Juicebox integration with mock data and testing utilities.

## Prerequisites
- Juicebox SDK installed
- Node.js or Python environment
- Test API key (sandbox mode)

## Instructions

### Step 1: Configure Development Environment
```bash
# Create development config
cat > .env.development << 'EOF'
JUICEBOX_API_KEY=jb_test_xxxxxxxxxxxx
JUICEBOX_ENVIRONMENT=sandbox
JUICEBOX_LOG_LEVEL=debug
EOF
```

### Step 2: Set Up Mock Data
```typescript
// mocks/juicebox.ts
export const mockProfiles = [
  {
    id: 'mock-1',
    name: 'Test User',
    title: 'Software Engineer',
    company: 'Test Corp',
    location: 'San Francisco, CA'
  }
];

export const mockSearchResponse = {
  total: 1,
  profiles: mockProfiles,
  hasMore: false
};
```

### Step 3: Create Test Utilities
```typescript
// test-utils/juicebox.ts
import { JuiceboxClient } from '@juicebox/sdk';

export function createTestClient() {
  return new JuiceboxClient({
    apiKey: process.env.JUICEBOX_API_KEY,
    sandbox: true,
    timeout: 5000  # 5000: 5 seconds in ms
  });
}

export async function withMockSearch<T>(
  fn: (client: JuiceboxClient) => Promise<T>
): Promise<T> {
  const client = createTestClient();
  return fn(client);
}
```

### Step 4: Hot Reload Setup
```json
// package.json
{
  "scripts": {
    "dev": "nodemon --watch src --exec ts-node src/index.ts",
    "test:watch": "vitest watch"
  }
}
```

## Output
- Development environment configuration
- Mock data for offline testing
- Test utilities for integration tests
- Hot reload for rapid iteration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Sandbox Limit | Exceeded test quota | Wait or upgrade plan |
| Mock Mismatch | Schema changed | Update mock data |
| Hot Reload Fail | File lock | Restart dev server |

## Examples

### Integration Test
```typescript
import { describe, it, expect } from 'vitest';
import { createTestClient } from './test-utils/juicebox';

describe('Juicebox Search', () => {
  it('returns profiles for valid query', async () => {
    const client = createTestClient();
    const results = await client.search.people({
      query: 'engineer',
      limit: 5
    });

    expect(results.profiles.length).toBeGreaterThan(0);
  });
});
```

## Resources
- [Sandbox Environment](https://juicebox.ai/docs/sandbox)
- [Testing Guide](https://juicebox.ai/docs/testing)

## Next Steps
With local dev configured, explore `juicebox-sdk-patterns` for production patterns.