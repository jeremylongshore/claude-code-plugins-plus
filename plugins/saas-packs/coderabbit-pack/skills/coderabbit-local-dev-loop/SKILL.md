---
name: coderabbit-local-dev-loop
description: |
  Configure CodeRabbit local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with CodeRabbit.
  Trigger with phrases like "coderabbit dev setup", "coderabbit local development",
  "coderabbit dev environment", "develop with coderabbit".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for CodeRabbit.

## Prerequisites
- Completed `coderabbit-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-coderabbit-project/
├── src/
│   ├── coderabbit/
│   │   ├── client.ts       # CodeRabbit client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── coderabbit.test.ts
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
└── package.json
```

### Step 2: Configure Environment
```bash
set -euo pipefail
# Copy environment template
cp .env.example .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 3: Setup Hot Reload
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

### Step 4: Configure Testing
```typescript
import { describe, it, expect, vi } from 'vitest';
import { CodeRabbitClient } from '../src/coderabbit/client';

describe('CodeRabbit Client', () => {
  it('should initialize with API key', () => {
    const client = new CodeRabbitClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for CodeRabbit development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock CodeRabbit Responses
```typescript
vi.mock('@coderabbit/sdk', () => ({
  CodeRabbitClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
set -euo pipefail
# Enable verbose logging
DEBUG=CODERABBIT=* npm run dev
```

## Resources
- [CodeRabbit SDK Reference](https://docs.coderabbit.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `coderabbit-sdk-patterns` for production-ready code patterns.