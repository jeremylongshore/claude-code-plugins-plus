---
name: firecrawl-local-dev-loop
description: |
  Configure FireCrawl local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with FireCrawl.
  Trigger with phrases like "firecrawl dev setup", "firecrawl local development",
  "firecrawl dev environment", "develop with firecrawl".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for FireCrawl.

## Prerequisites
- Completed `firecrawl-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control

## Instructions

### Step 1: Create Project Structure
```
my-firecrawl-project/
├── src/
│   ├── firecrawl/
│   │   ├── client.ts       # FireCrawl client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── firecrawl.test.ts
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
import { FireCrawlClient } from '../src/firecrawl/client';

describe('FireCrawl Client', () => {
  it('should initialize with API key', () => {
    const client = new FireCrawlClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for FireCrawl development

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Module not found | Missing dependency | Run `npm install` |
| Port in use | Another process | Kill process or change port |
| Env not loaded | Missing .env.local | Copy from .env.example |
| Test timeout | Slow network | Increase test timeout |

## Examples

### Mock FireCrawl Responses
```typescript
vi.mock('@firecrawl/sdk', () => ({
  FireCrawlClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Debug Mode
```bash
set -euo pipefail
# Enable verbose logging
DEBUG=FIRECRAWL=* npm run dev
```

## Resources
- [FireCrawl SDK Reference](https://docs.firecrawl.com/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
See `firecrawl-sdk-patterns` for production-ready code patterns.