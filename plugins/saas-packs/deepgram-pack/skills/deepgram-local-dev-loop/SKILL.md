---
name: deepgram-local-dev-loop
description: |
  Configure Deepgram local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Deepgram.
  Trigger with phrases like "deepgram dev setup", "deepgram local development",
  "deepgram dev environment", "develop with deepgram".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, deepgram]
---

# Deepgram Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Deepgram.

## Prerequisites
- Completed `deepgram-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-deepgram-project/
├── src/
│   ├── deepgram/
│   │   ├── client.ts       # Deepgram client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── deepgram.test.ts
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
import { DeepgramClient } from '../src/deepgram/client';

describe('Deepgram Client', () => {
  it('should initialize with API key', () => {
    const client = new DeepgramClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Deepgram development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock Deepgram Responses
```typescript
vi.mock('@deepgram/sdk', () => ({
  DeepgramClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
# Enable verbose logging
DEBUG=DEEPGRAM=* npm run dev
```

## Resources
- [Deepgram SDK Reference](https://docs.deepgram.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `deepgram-sdk-patterns` for production-ready code patterns.