---
name: fireflies-local-dev-loop
description: |
  Configure Fireflies.ai local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Fireflies.ai.
  Trigger with phrases like "fireflies dev setup", "fireflies local development",
  "fireflies dev environment", "develop with fireflies".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Fireflies.ai.

## Prerequisites
- Completed `fireflies-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-fireflies-project/
├── src/
│   ├── fireflies/
│   │   ├── client.ts       # Fireflies.ai client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── fireflies.test.ts
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
import { Fireflies.aiClient } from '../src/fireflies/client';

describe('Fireflies.ai Client', () => {
  it('should initialize with API key', () => {
    const client = new Fireflies.aiClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Fireflies.ai development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock Fireflies.ai Responses
```typescript
vi.mock('@fireflies/sdk', () => ({
  Fireflies.aiClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
set -euo pipefail
# Enable verbose logging
DEBUG=FIREFLIES=* npm run dev
```

## Resources
- [Fireflies.ai SDK Reference](https://docs.fireflies.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `fireflies-sdk-patterns` for production-ready code patterns.