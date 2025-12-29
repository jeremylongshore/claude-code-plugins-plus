---
name: supabase-local-dev-loop
description: |
  Supabase local development workflow with hot reload and testing.
  Trigger phrases: "supabase dev setup", "supabase local development",
  "supabase dev environment", "develop with supabase".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Supabase.

## Development Environment

### 1. Project Structure
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

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Hot Reload Configuration
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

## Testing Strategy

### Unit Tests
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

### Mock Responses
```typescript
vi.mock('@supabase/supabase-js', () => ({
  SupabaseClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

## Debugging Tips
- Use `DEBUG=SUPABASE=*` for verbose logging
- Check Supabase dashboard for request logs
- Use `supabase-debug-bundle` skill for evidence collection

## Next Steps
See `supabase-sdk-patterns` for production-ready code patterns.