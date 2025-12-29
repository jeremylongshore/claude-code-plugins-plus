---
name: supabase-local-dev-loop
description: |
  Set up Supabase local development workflow with hot reload and testing.
  Use when configuring a reproducible development environment.
  Trigger with phrases like "supabase dev setup", "supabase local development",
  "supabase dev environment", "develop with supabase".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Supabase.

## Prerequisites
- Completed `supabase-install-auth` setup
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)

## Instructions

### Step 1: Create Project Structure
```
my-supabase-project/
├── src/
│   ├── supabase/
│   │   ├── client.ts       # Supabase client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── supabase.test.ts
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

### Step 3: Set Up Hot Reload
```json
// package.json scripts
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
import { SupabaseClient } from '../src/supabase/client';

describe('Supabase Client', () => {
  it('should initialize with API key', () => {
    const client = new SupabaseClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Output
- Working development environment with hot reload
- Test suite configured and passing
- Environment variables properly isolated
- Mock responses for offline development

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| .env not found | Missing configuration | Copy `.env.example` to `.env.local` |
| Test failures | Mock not configured | Set up mocks in test setup file |
| Hot reload broken | File watcher issue | Restart dev server |
| Import errors | TypeScript paths | Check `tsconfig.json` paths |

## Examples

### Mock Responses for Testing
```typescript
vi.mock('@supabase/supabase-js', () => ({
  SupabaseClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

### Environment Validation
```typescript
// src/supabase/config.ts
import { z } from 'zod';

const configSchema = z.object({
  SUPABASE_API_KEY: z.string().min(1),
});

export const config = configSchema.parse(process.env);
```

## Resources
- [Supabase Local Development Guide](https://supabase.com/docs/local-dev)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps
- Use `DEBUG=SUPABASE=*` for verbose logging
- Check Supabase dashboard for request logs
- Use `supabase-debug-bundle` skill for evidence collection
- See `supabase-sdk-patterns` for production-ready code patterns