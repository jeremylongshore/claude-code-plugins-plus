---
name: vastai-local-dev-loop
description: |
  Configure Vast.ai local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Vast.ai.
  Trigger with phrases like "vastai dev setup", "vastai local development",
  "vastai dev environment", "develop with vastai".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vast.ai Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Vast.ai.

## Prerequisites
- Completed `vastai-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-vastai-project/
├── src/
│   ├── vastai/
│   │   ├── client.ts       # Vast.ai client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── vastai.test.ts
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
import { Vast.aiClient } from '../src/vastai/client';

describe('Vast.ai Client', () => {
  it('should initialize with API key', () => {
    const client = new Vast.aiClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Vast.ai development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock Vast.ai Responses
```typescript
vi.mock('@vastai/sdk', () => ({
  Vast.aiClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
set -euo pipefail
# Enable verbose logging
DEBUG=VASTAI=* npm run dev
```

## Resources
- [Vast.ai SDK Reference](https://docs.vastai.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `vastai-sdk-patterns` for production-ready code patterns.