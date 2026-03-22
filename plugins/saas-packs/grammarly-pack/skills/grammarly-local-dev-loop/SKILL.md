---
name: grammarly-local-dev-loop
description: |
  Configure Grammarly local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Grammarly.
  Trigger with phrases like "grammarly dev setup", "grammarly local development",
  "grammarly dev environment", "develop with grammarly".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Local Dev Loop

## Overview

Set up a development workflow for Grammarly API integrations with mocked responses and vitest.

## Instructions

### Step 1: Project Structure

```
grammarly-integration/
├── src/grammarly/
│   ├── client.ts       # API client with token management
│   ├── scoring.ts      # Writing Score API
│   ├── detection.ts    # AI + Plagiarism detection
│   └── types.ts        # TypeScript interfaces
├── tests/
│   ├── fixtures/       # Mock API responses
│   └── scoring.test.ts
├── .env.local
└── package.json
```

### Step 2: Mocked Tests

```typescript
import { describe, it, expect, vi } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Writing Score', () => {
  it('should return scores for valid text', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ overallScore: 85, engagement: 80, correctness: 90, clarity: 85, tone: 82 }),
    });
    // Test scoring logic
  });

  it('should reject text under 30 words', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 400, text: async () => 'Text too short' });
    // Test error handling
  });
});
```

## Resources

- [Grammarly API Docs](https://developer.grammarly.com/)

## Next Steps

See `grammarly-sdk-patterns` for production patterns.
