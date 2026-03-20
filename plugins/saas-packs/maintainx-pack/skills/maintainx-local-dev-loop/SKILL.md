---
name: maintainx-local-dev-loop
description: |
  Set up a local development loop for MaintainX integration development.
  Use when configuring dev environment, testing API calls locally,
  or setting up a sandbox workflow for MaintainX.
  Trigger with phrases like "maintainx dev setup", "maintainx local",
  "maintainx development environment", "maintainx testing setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Local Dev Loop

## Overview
Set up an efficient local development workflow for building and testing MaintainX integrations with hot reload, mock servers, and automated testing.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Node.js 18+ installed
- `MAINTAINX_API_KEY` environment variable set

## Instructions

### Step 1: Initialize TypeScript Project

```bash
mkdir maintainx-integration && cd maintainx-integration
npm init -y
npm install axios dotenv
npm install -D typescript tsx vitest @types/node
npx tsc --init --target ES2022 --module NodeNext --moduleResolution nodenext --outDir dist
```

Create `tsconfig.json` paths:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "nodenext",
    "outDir": "dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
```

### Step 2: Project Structure

```
maintainx-integration/
├── src/
│   ├── client.ts          # MaintainX API client (from install-auth)
│   ├── work-orders.ts     # Work order service layer
│   └── sync.ts            # Data sync logic
├── tests/
│   ├── client.test.ts     # Unit tests with mocks
│   └── integration.test.ts # Live API tests
├── .env                   # MAINTAINX_API_KEY=...
├── .env.example           # MAINTAINX_API_KEY=your-key-here
├── package.json
└── tsconfig.json
```

### Step 3: Dev Scripts in package.json

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:integration": "INTEGRATION=true vitest run tests/integration.test.ts",
    "build": "tsc",
    "repl": "tsx src/repl.ts"
  }
}
```

### Step 4: Write Unit Tests with Mocked API

```typescript
// tests/client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios');

describe('MaintainXClient', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    process.env.MAINTAINX_API_KEY = 'test-key-123';
  });

  it('creates a work order', async () => {
    const mockResponse = {
      data: { id: 1, title: 'Test WO', status: 'OPEN' },
    };
    vi.mocked(axios.create).mockReturnValue({
      post: vi.fn().mockResolvedValue(mockResponse),
      interceptors: { response: { use: vi.fn() } },
    } as any);

    const { MaintainXClient } = await import('../src/client');
    const client = new MaintainXClient();
    const result = await client.createWorkOrder({ title: 'Test WO' });

    expect(result.data.title).toBe('Test WO');
    expect(result.data.status).toBe('OPEN');
  });

  it('paginates work orders', async () => {
    const page1 = { data: { workOrders: [{ id: 1 }], cursor: 'abc' } };
    const page2 = { data: { workOrders: [{ id: 2 }], cursor: null } };
    const getMock = vi.fn()
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2);

    vi.mocked(axios.create).mockReturnValue({
      get: getMock,
      interceptors: { response: { use: vi.fn() } },
    } as any);

    const { MaintainXClient } = await import('../src/client');
    const client = new MaintainXClient();

    const all = [];
    let cursor: string | undefined;
    do {
      const { data } = await client.getWorkOrders({ cursor });
      all.push(...data.workOrders);
      cursor = data.cursor;
    } while (cursor);

    expect(all).toHaveLength(2);
  });
});
```

### Step 5: Interactive REPL

```typescript
// src/repl.ts
import * as repl from 'node:repl';
import 'dotenv/config';
import { MaintainXClient } from './client';

const client = new MaintainXClient();
console.log('MaintainX REPL ready. `client` is available.');
console.log('Try: await client.getWorkOrders({ limit: 3 })');

const r = repl.start({ prompt: 'maintainx> ' });
r.context.client = client;
```

```bash
# Start REPL
npm run repl
# maintainx> const { data } = await client.getWorkOrders({ limit: 3 })
# maintainx> data.workOrders.map(wo => wo.title)
```

## Output
- TypeScript project configured with `tsx watch` for hot reload
- Vitest unit tests with mocked MaintainX API responses
- Interactive REPL for exploring the API
- `.env.example` template for team onboarding
- Dev/test/build scripts in `package.json`

## Error Handling
| Issue | Solution |
|-------|----------|
| `MAINTAINX_API_KEY` undefined | Copy `.env.example` to `.env` and fill in your key |
| 429 Rate Limited during dev | Add delays between calls, use mocks for unit tests |
| TypeScript import errors | Ensure `moduleResolution: "nodenext"` in tsconfig |
| `tsx` not found | Install with `npm i -D tsx` |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Vitest Documentation](https://vitest.dev/)
- [tsx - TypeScript Execute](https://github.com/privatenumber/tsx)

## Next Steps
For SDK patterns and best practices, see `maintainx-sdk-patterns`.

## Examples

**Docker-based dev environment**:

```dockerfile
# Dockerfile.dev
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]
```

```yaml
# docker-compose.dev.yml
services:
  app:
    build: { dockerfile: Dockerfile.dev }
    env_file: .env
    volumes: ["./src:/app/src"]
```

**Run integration tests against live API**:

```bash
INTEGRATION=true npm run test:integration
```
