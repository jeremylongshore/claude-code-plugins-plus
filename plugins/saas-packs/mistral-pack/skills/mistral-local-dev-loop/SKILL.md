---
name: mistral-local-dev-loop
description: |
  Configure Mistral AI local development with hot reload, testing, and mocking.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Mistral AI.
  Trigger with phrases like "mistral dev setup", "mistral local development",
  "mistral dev environment", "develop with mistral".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, testing, workflow]

---
# Mistral AI Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Mistral AI integrations: project scaffold, environment config, hot reload with `tsx`, unit tests with Vitest mocking, and integration tests against the live API.

## Prerequisites
- Completed `mistral-install-auth` setup
- Node.js 18+ with npm/pnpm
- `MISTRAL_API_KEY` set in environment

## Instructions

### Step 1: Project Structure

```
my-mistral-project/
├── src/
│   ├── mistral/
│   │   ├── client.ts       # Singleton client
│   │   ├── config.ts       # Config with Zod validation
│   │   └── types.ts        # TypeScript types
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── mistral.test.ts
│   └── integration/
│       └── mistral.integration.test.ts
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
├── tsconfig.json
├── vitest.config.ts
└── package.json
```

### Step 2: Package Configuration

**package.json**
```json
{
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:integration": "vitest run tests/integration/",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@mistralai/mistralai": "^1.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "dotenv": "^16.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
```

**tsconfig.json**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### Step 3: Environment Setup

```bash
# Create environment template
cat > .env.example << 'EOF'
MISTRAL_API_KEY=your-api-key-here
MISTRAL_MODEL=mistral-small-latest
LOG_LEVEL=debug
EOF

cp .env.example .env.local
echo '.env.local' >> .gitignore
echo '.env' >> .gitignore
```

### Step 4: Client Module

```typescript
// src/mistral/client.ts
import { Mistral } from '@mistralai/mistralai';
import 'dotenv/config';

let instance: Mistral | null = null;

export function getMistralClient(): Mistral {
  if (!instance) {
    const apiKey = process.env.MISTRAL_API_KEY;
    if (!apiKey) throw new Error('MISTRAL_API_KEY not set');
    instance = new Mistral({ apiKey, timeoutMs: 30_000 });
  }
  return instance;
}

export function resetClient(): void {
  instance = null;
}
```

### Step 5: Unit Tests with Mocking

**vitest.config.ts**
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: { provider: 'v8', reporter: ['text', 'json'] },
  },
});
```

**tests/unit/mistral.test.ts**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the entire SDK
vi.mock('@mistralai/mistralai', () => ({
  Mistral: vi.fn().mockImplementation(() => ({
    chat: {
      complete: vi.fn().mockResolvedValue({
        id: 'test-id',
        model: 'mistral-small-latest',
        choices: [{
          index: 0,
          message: { role: 'assistant', content: 'Mocked response' },
          finishReason: 'stop',
        }],
        usage: { promptTokens: 10, completionTokens: 5, totalTokens: 15 },
      }),
      stream: vi.fn().mockImplementation(async function* () {
        yield { data: { choices: [{ delta: { content: 'Streamed ' } }] } };
        yield { data: { choices: [{ delta: { content: 'response' } }] } };
      }),
    },
    embeddings: {
      create: vi.fn().mockResolvedValue({
        data: [{ embedding: new Array(1024).fill(0.1) }],
        usage: { totalTokens: 5 },
      }),
    },
    models: {
      list: vi.fn().mockResolvedValue({ data: [{ id: 'mistral-small-latest' }] }),
    },
  })),
}));

describe('Mistral Client', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('should complete chat', async () => {
    const { Mistral } = await import('@mistralai/mistralai');
    const client = new Mistral({ apiKey: 'test' });

    const response = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Test' }],
    });

    expect(response.choices?.[0]?.message?.content).toBe('Mocked response');
    expect(response.usage?.totalTokens).toBe(15);
  });

  it('should generate embeddings', async () => {
    const { Mistral } = await import('@mistralai/mistralai');
    const client = new Mistral({ apiKey: 'test' });

    const response = await client.embeddings.create({
      model: 'mistral-embed',
      inputs: ['test text'],
    });

    expect(response.data[0].embedding).toHaveLength(1024);
  });
});
```

### Step 6: Integration Test (Live API)

```typescript
// tests/integration/mistral.integration.test.ts
import { describe, it, expect } from 'vitest';
import { Mistral } from '@mistralai/mistralai';

const apiKey = process.env.MISTRAL_API_KEY;

describe.skipIf(!apiKey)('Mistral Integration', () => {
  const client = new Mistral({ apiKey: apiKey! });

  it('should list models', async () => {
    const models = await client.models.list();
    expect(models.data?.length).toBeGreaterThan(0);
  }, 10_000);

  it('should complete chat', async () => {
    const response = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Reply with "ok"' }],
      maxTokens: 10,
      temperature: 0,
    });
    expect(response.choices?.[0]?.message?.content).toBeTruthy();
  }, 15_000);

  it('should generate embeddings', async () => {
    const response = await client.embeddings.create({
      model: 'mistral-embed',
      inputs: ['test'],
    });
    expect(response.data[0].embedding).toHaveLength(1024);
  }, 10_000);
});
```

## Output
- Working dev environment with hot reload (`tsx watch`)
- Unit tests with full SDK mocking
- Integration tests against live API (skip when no key)
- Environment variable management with `.env.local`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Integration timeout | Slow API response | Increase test timeout |
| Mock type errors | SDK interface changed | Update mock to match current SDK |

## Resources
- [Mistral TypeScript SDK](https://github.com/mistralai/client-ts)
- [Vitest Documentation](https://vitest.dev/)
- [tsx](https://github.com/privatenumber/tsx)

## Next Steps
See `mistral-sdk-patterns` for production-ready code patterns.
