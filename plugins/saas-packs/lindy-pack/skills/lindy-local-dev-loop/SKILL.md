---
name: lindy-local-dev-loop
description: |
  Configure Lindy local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Lindy.
  Trigger with phrases like "lindy dev setup", "lindy local development",
  "lindy dev environment", "develop with lindy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Lindy.

## Prerequisites
- Completed `lindy-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-lindy-project/
├── src/
│   ├── lindy/
│   │   ├── client.ts       # Lindy client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── lindy.test.ts
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
└── package.json
```

### Step 2: Configure Environment
```bash
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
import { LindyClient } from '../src/lindy/client';

describe('Lindy Client', () => {
  it('should initialize with API key', () => {
    const client = new LindyClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Lindy development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock Lindy Responses
```typescript
vi.mock('@lindy/sdk', () => ({
  LindyClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
# Enable verbose logging
DEBUG=LINDY=* npm run dev
```

## Resources
- [Lindy SDK Reference](https://docs.lindy.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `lindy-sdk-patterns` for production-ready code patterns.