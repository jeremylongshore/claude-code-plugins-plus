---
name: mistral-local-dev-loop
description: |
  Configure Mistral AI local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Mistral AI.
  Trigger with phrases like "mistral dev setup", "mistral local development",
  "mistral dev environment", "develop with mistral".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Mistral AI integrations.

## Prerequisites
- Completed `mistral-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-mistral-project/
├── src/
│   ├── mistral/
│   │   ├── client.ts       # Mistral client wrapper
│   │   ├── config.ts       # Configuration management
│   │   ├── types.ts        # TypeScript types
│   │   └── utils.ts        # Helper functions
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

### Step 2: Configure Environment

```bash
# Create environment template
cat > .env.example << 'EOF'
MISTRAL_API_KEY=your-api-key-here
MISTRAL_MODEL=mistral-small-latest
LOG_LEVEL=debug
EOF

# Copy for local development
cp .env.example .env.local

# Add to .gitignore
echo '.env.local' >> .gitignore
echo '.env' >> .gitignore
```

### Step 3: Setup Hot Reload

**package.json**
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "vitest run --config vitest.integration.config.ts",
    "lint": "eslint src --ext .ts",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "dotenv": "^16.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^1.0.0"
  },
  "dependencies": {
    "@mistralai/mistralai": "^1.0.0"
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

### Step 4: Configure Testing

**vitest.config.ts**
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
    setupFiles: ['./tests/setup.ts'],
  },
});
```

**tests/setup.ts**
```typescript
import 'dotenv/config';
import { beforeAll, afterAll, vi } from 'vitest';

beforeAll(() => {
  // Global setup
});

afterAll(() => {
  vi.restoreAllMocks();
});
```

**tests/unit/mistral.test.ts**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getMistralClient } from '../../src/mistral/client';

// Mock the Mistral SDK
vi.mock('@mistralai/mistralai', () => ({
  default: vi.fn().mockImplementation(() => ({
    chat: {
      complete: vi.fn().mockResolvedValue({
        choices: [{ message: { content: 'Mocked response' } }],
      }),
    },
    models: {
      list: vi.fn().mockResolvedValue({ data: [] }),
    },
  })),
}));

describe('Mistral Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with API key', () => {
    const client = getMistralClient();
    expect(client).toBeDefined();
  });

  it('should complete chat successfully', async () => {
    const client = getMistralClient();
    const response = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Test' }],
    });
    expect(response.choices?.[0]?.message?.content).toBe('Mocked response');
  });
});
```

### Step 5: Create Client Wrapper

**src/mistral/client.ts**
```typescript
import Mistral from '@mistralai/mistralai';
import 'dotenv/config';

let instance: Mistral | null = null;

export function getMistralClient(): Mistral {
  if (!instance) {
    const apiKey = process.env.MISTRAL_API_KEY;
    if (!apiKey) {
      throw new Error('MISTRAL_API_KEY environment variable is required');
    }
    instance = new Mistral({ apiKey });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Mistral development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |
| Type errors | Missing types | Check @types packages |

## Examples

### Mock Mistral Responses in Tests
```typescript
import { vi } from 'vitest';

vi.mock('@mistralai/mistralai', () => ({
  default: vi.fn().mockImplementation(() => ({
    chat: {
      complete: vi.fn().mockResolvedValue({
        id: 'test-id',
        object: 'chat.completion',
        model: 'mistral-small-latest',
        choices: [{
          index: 0,
          message: { role: 'assistant', content: 'Mocked!' },
          finishReason: 'stop',
        }],
        usage: { promptTokens: 10, completionTokens: 5, totalTokens: 15 },
      }),
      stream: vi.fn().mockImplementation(async function* () {
        yield { data: { choices: [{ delta: { content: 'Streaming ' } }] } };
        yield { data: { choices: [{ delta: { content: 'response' } }] } };
      }),
    },
  })),
}));
```

### Debug Mode
```bash
set -euo pipefail
# Enable verbose logging
DEBUG=mistral:* npm run dev

# Or in code
const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
  // Enable debug logging
});
```

## Resources
- [Mistral AI SDK Reference](https://docs.mistral.ai/api/)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `mistral-sdk-patterns` for production-ready code patterns.