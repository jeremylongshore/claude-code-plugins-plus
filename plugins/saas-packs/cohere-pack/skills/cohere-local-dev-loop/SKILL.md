---
name: cohere-local-dev-loop
description: |
  Configure Cohere local development with mocking, testing, and hot reload.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Cohere API v2.
  Trigger with phrases like "cohere dev setup", "cohere local development",
  "cohere dev environment", "develop with cohere", "mock cohere".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow with Cohere API v2 mocking, vitest testing, and hot reload.

## Prerequisites
- Completed `cohere-install-auth` setup
- Node.js 18+ with npm/pnpm
- TypeScript project with `tsx` or `ts-node`

## Instructions

### Step 1: Project Structure

```
my-cohere-project/
├── src/
│   ├── cohere/
│   │   ├── client.ts       # CohereClientV2 wrapper
│   │   ├── chat.ts         # Chat completions
│   │   ├── embed.ts        # Embedding operations
│   │   └── rerank.ts       # Reranking operations
│   └── index.ts
├── tests/
│   ├── chat.test.ts
│   ├── embed.test.ts
│   └── fixtures/
│       └── responses.ts    # Mock API responses
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
└── package.json
```

### Step 2: Package Setup

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "COHERE_INTEGRATION=1 vitest --run"
  },
  "dependencies": {
    "cohere-ai": "^7.0.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0",
    "typescript": "^5.5.0"
  }
}
```

### Step 3: Client Wrapper

```typescript
// src/cohere/client.ts
import { CohereClientV2 } from 'cohere-ai';

let instance: CohereClientV2 | null = null;

export function getCohere(): CohereClientV2 {
  if (!instance) {
    instance = new CohereClientV2({
      token: process.env.CO_API_KEY,
    });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

### Step 4: Mock Fixtures

```typescript
// tests/fixtures/responses.ts
export const mockChatResponse = {
  id: 'test-chat-id',
  message: {
    role: 'assistant' as const,
    content: [{ type: 'text' as const, text: 'Mocked response' }],
  },
  finishReason: 'COMPLETE' as const,
  usage: { billedUnits: { inputTokens: 10, outputTokens: 5 } },
};

export const mockEmbedResponse = {
  id: 'test-embed-id',
  embeddings: {
    float: [[0.1, 0.2, 0.3, 0.4]], // truncated for dev
  },
  meta: { billedUnits: { inputTokens: 4 } },
};

export const mockRerankResponse = {
  id: 'test-rerank-id',
  results: [
    { index: 0, relevanceScore: 0.95 },
    { index: 2, relevanceScore: 0.72 },
  ],
  meta: { billedUnits: { searchUnits: 1 } },
};
```

### Step 5: Test with Mocks

```typescript
// tests/chat.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mockChatResponse } from './fixtures/responses';

vi.mock('cohere-ai', () => ({
  CohereClientV2: vi.fn().mockImplementation(() => ({
    chat: vi.fn().mockResolvedValue(mockChatResponse),
    chatStream: vi.fn().mockReturnValue({
      [Symbol.asyncIterator]: async function* () {
        yield { type: 'content-delta', delta: { message: { content: { text: 'Hi' } } } };
      },
    }),
    embed: vi.fn().mockResolvedValue({ embeddings: { float: [[0.1, 0.2]] } }),
    rerank: vi.fn().mockResolvedValue({
      results: [{ index: 0, relevanceScore: 0.9 }],
    }),
  })),
}));

describe('Cohere Chat', () => {
  it('should return a chat completion', async () => {
    const { CohereClientV2 } = await import('cohere-ai');
    const cohere = new CohereClientV2();

    const result = await cohere.chat({
      model: 'command-a-03-2025',
      messages: [{ role: 'user', content: 'test' }],
    });

    expect(result.message?.content?.[0]?.text).toBe('Mocked response');
    expect(result.finishReason).toBe('COMPLETE');
  });
});
```

### Step 6: Integration Tests (Optional, Hits Real API)

```typescript
// tests/integration.test.ts
import { describe, it, expect } from 'vitest';
import { CohereClientV2 } from 'cohere-ai';

const shouldRun = process.env.COHERE_INTEGRATION === '1';

describe.skipIf(!shouldRun)('Cohere Integration', () => {
  const cohere = new CohereClientV2();

  it('chat endpoint responds', async () => {
    const res = await cohere.chat({
      model: 'command-r7b-12-2024', // cheapest model for tests
      messages: [{ role: 'user', content: 'Say OK' }],
      maxTokens: 5,
    });
    expect(res.message?.content?.[0]?.text).toBeTruthy();
  }, 15_000);

  it('embed endpoint responds', async () => {
    const res = await cohere.embed({
      model: 'embed-v4.0',
      texts: ['test'],
      inputType: 'search_document',
      embeddingTypes: ['float'],
    });
    expect(res.embeddings.float[0].length).toBeGreaterThan(0);
  }, 15_000);
});
```

## Environment Management

```bash
# .env.example (commit this)
CO_API_KEY=your-trial-key-here

# .env.local (git-ignored, used by tsx/vitest)
CO_API_KEY=actual-key

# .gitignore entries
.env.local
.env.*.local
```

## Output
- Working dev environment with hot reload via `tsx watch`
- Unit tests with mocked Cohere responses (no API calls)
- Optional integration tests gated by `COHERE_INTEGRATION=1`
- Mock fixtures matching real API v2 response shapes

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `vi.mock not working` | Wrong import order | Mock before importing modules |
| `CO_API_KEY undefined` | .env not loaded | Use `dotenv/config` or tsx env support |
| Integration test timeout | Slow network | Increase timeout to 15s+ |
| Type mismatch on mock | API shape changed | Update fixtures to match SDK types |

## Resources
- [Vitest Documentation](https://vitest.dev/)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)
- [Cohere TypeScript SDK](https://github.com/cohere-ai/cohere-typescript)

## Next Steps
See `cohere-sdk-patterns` for production-ready code patterns.
