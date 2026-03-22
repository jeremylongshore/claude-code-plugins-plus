---
name: intercom-local-dev-loop
description: |
  Configure Intercom local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Intercom.
  Trigger with phrases like "intercom dev setup", "intercom local development",
  "intercom dev environment", "develop with intercom".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Intercom.

## Prerequisites
- Completed `intercom-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-intercom-project/
├── src/
│   ├── intercom/
│   │   ├── client.ts       # Intercom client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── intercom.test.ts
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
import { IntercomClient } from '../src/intercom/client';

describe('Intercom Client', () => {
  it('should initialize with API key', () => {
    const client = new IntercomClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Intercom development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock Intercom Responses
```typescript
vi.mock('@intercom/sdk', () => ({
  IntercomClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
# Enable verbose logging
DEBUG=INTERCOM=* npm run dev
```

## Resources
- [Intercom SDK Reference](https://docs.intercom.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `intercom-sdk-patterns` for production-ready code patterns.