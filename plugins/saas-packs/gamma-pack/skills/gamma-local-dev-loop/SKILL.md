---
name: gamma-local-dev-loop
description: |
  Set up efficient local development workflow for Gamma.
  Use when configuring hot reload, mock responses,
  or optimizing your Gamma development experience.
  Trigger with phrases like "gamma local dev", "gamma development setup",
  "gamma hot reload", "gamma mock", "gamma dev workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Local Dev Loop

## Overview
Configure an efficient local development workflow with hot reload and mock responses for Gamma presentation development.

## Prerequisites
- Completed `gamma-hello-world` setup
- Node.js 18+ with nodemon or tsx
- TypeScript project (recommended)

## Instructions

### Step 1: Install Dev Dependencies
```bash
set -euo pipefail
npm install -D nodemon tsx dotenv @types/node
```

### Step 2: Configure Development Script
Add to package.json:
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:mock": "GAMMA_MOCK=true tsx watch src/index.ts"
  }
}
```

### Step 3: Create Mock Client
```typescript
// src/gamma-client.ts
import { GammaClient } from '@gamma/sdk';

const isMock = process.env.GAMMA_MOCK === 'true';

export const gamma = isMock
  ? createMockClient()
  : new GammaClient({ apiKey: process.env.GAMMA_API_KEY });

function createMockClient() {
  return {
    presentations: {
      create: async (opts) => ({
        id: 'mock-123',
        url: 'https://gamma.app/mock/preview',
        title: opts.title,
      }),
    },
  };
}
```

### Step 4: Set Up Environment Files
```bash
# .env.development
GAMMA_API_KEY=your-dev-key
GAMMA_MOCK=false

# .env.test
GAMMA_MOCK=true
```

## Output
- Hot reload development server
- Mock client for offline development
- Environment-based configuration
- Fast iteration cycle

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Watch Error | File permissions | Check nodemon config |
| Mock Mismatch | Mock out of sync | Update mock responses |
| Env Not Loaded | dotenv not configured | Add `import 'dotenv/config'` |

## Examples

### Watch Mode Development
```bash
set -euo pipefail
npm run dev
# Changes to src/*.ts trigger automatic restart
```

### Offline Development with Mocks
```bash
set -euo pipefail
npm run dev:mock
# Uses mock responses, no API calls
```

## Resources
- [tsx Documentation](https://github.com/esbuild-kit/tsx)
- [Gamma SDK Mock Guide](https://gamma.app/docs/testing)

## Next Steps
Proceed to `gamma-sdk-patterns` for advanced SDK usage patterns.