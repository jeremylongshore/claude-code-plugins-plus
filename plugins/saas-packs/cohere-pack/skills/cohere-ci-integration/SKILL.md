---
name: cohere-ci-integration
description: |
  Configure CI/CD for Cohere integrations with GitHub Actions and automated testing.
  Use when setting up automated testing for Chat/Embed/Rerank,
  configuring CI pipelines, or testing Cohere-powered applications.
  Trigger with phrases like "cohere CI", "cohere GitHub Actions",
  "cohere automated tests", "CI cohere", "cohere pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere CI Integration

## Overview
Set up CI/CD pipelines with automated unit tests (mocked) and integration tests (real API) for Cohere API v2 applications.

## Prerequisites
- GitHub repository with Actions enabled
- Cohere trial or production API key
- `cohere-ai` package installed

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/cohere-ci.yml
name: Cohere CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        # Unit tests use mocked Cohere responses — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      CO_API_KEY: ${{ secrets.CO_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Run Cohere integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 2: Configure GitHub Secrets

```bash
# Store Cohere API key as a repo secret
gh secret set CO_API_KEY --body "your-production-key-here"

# Verify it was set
gh secret list
```

### Step 3: Unit Tests (Mocked — No API Key)

```typescript
// tests/unit/cohere-chat.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the entire SDK
vi.mock('cohere-ai', () => ({
  CohereClientV2: vi.fn().mockImplementation(() => ({
    chat: vi.fn().mockResolvedValue({
      message: { content: [{ type: 'text', text: 'mocked response' }] },
      finishReason: 'COMPLETE',
      usage: { billedUnits: { inputTokens: 5, outputTokens: 3 } },
    }),
    embed: vi.fn().mockResolvedValue({
      embeddings: { float: [[0.1, 0.2, 0.3]] },
    }),
    rerank: vi.fn().mockResolvedValue({
      results: [{ index: 0, relevanceScore: 0.95 }],
    }),
  })),
}));

describe('Chat service', () => {
  it('returns text from chat completion', async () => {
    const { CohereClientV2 } = await import('cohere-ai');
    const cohere = new CohereClientV2();

    const response = await cohere.chat({
      model: 'command-a-03-2025',
      messages: [{ role: 'user', content: 'test' }],
    });

    expect(response.message?.content?.[0]?.text).toBe('mocked response');
    expect(cohere.chat).toHaveBeenCalledWith(
      expect.objectContaining({ model: 'command-a-03-2025' })
    );
  });

  it('handles embed with correct input type', async () => {
    const { CohereClientV2 } = await import('cohere-ai');
    const cohere = new CohereClientV2();

    const response = await cohere.embed({
      model: 'embed-v4.0',
      texts: ['test'],
      inputType: 'search_document',
      embeddingTypes: ['float'],
    });

    expect(response.embeddings.float).toHaveLength(1);
  });
});
```

### Step 4: Integration Tests (Real API — Gated)

```typescript
// tests/integration/cohere.test.ts
import { describe, it, expect } from 'vitest';
import { CohereClientV2 } from 'cohere-ai';

const hasApiKey = !!process.env.CO_API_KEY;

describe.skipIf(!hasApiKey)('Cohere Integration', () => {
  const cohere = new CohereClientV2();

  it('chat completion works', async () => {
    const response = await cohere.chat({
      model: 'command-r7b-12-2024', // cheapest model for CI
      messages: [{ role: 'user', content: 'Reply with exactly: OK' }],
      maxTokens: 5,
    });
    expect(response.message?.content?.[0]?.text).toBeTruthy();
    expect(response.finishReason).toBe('COMPLETE');
  }, 15_000);

  it('embed generates vectors', async () => {
    const response = await cohere.embed({
      model: 'embed-v4.0',
      texts: ['CI test embedding'],
      inputType: 'search_document',
      embeddingTypes: ['float'],
    });
    expect(response.embeddings.float[0].length).toBeGreaterThan(0);
  }, 15_000);

  it('rerank scores documents', async () => {
    const response = await cohere.rerank({
      model: 'rerank-v3.5',
      query: 'machine learning',
      documents: ['ML is AI', 'cooking recipes', 'deep learning'],
      topN: 2,
    });
    expect(response.results).toHaveLength(2);
    expect(response.results[0].relevanceScore).toBeGreaterThan(0.5);
  }, 15_000);
});
```

### Step 5: Package Scripts

```json
{
  "scripts": {
    "test": "vitest --run",
    "test:watch": "vitest --watch",
    "test:integration": "COHERE_INTEGRATION=1 vitest --run tests/integration/",
    "test:coverage": "vitest --run --coverage"
  }
}
```

## CI Cost Control

- Use `command-r7b-12-2024` (cheapest) for integration tests
- Set `maxTokens: 5` on all CI chat calls
- Run integration tests only on `main` pushes (not PRs)
- Use trial key for CI if under 1000 monthly calls

## Error Handling
| CI Issue | Cause | Solution |
|----------|-------|----------|
| Secret not found | Missing GitHub secret | `gh secret set CO_API_KEY` |
| 429 in CI | Rate limited (trial key) | Reduce test count or upgrade key |
| Integration timeout | Slow API response | Set `timeout-minutes: 5` |
| Flaky tests | API latency variance | Add retry in test setup |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest Configuration](https://vitest.dev/config/)
- [Cohere Rate Limits](https://docs.cohere.com/docs/rate-limits)

## Next Steps
For deployment patterns, see `cohere-deploy-integration`.
