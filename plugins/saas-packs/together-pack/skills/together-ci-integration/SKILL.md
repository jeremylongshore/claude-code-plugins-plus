---
name: together-ci-integration
description: |
  Together AI ci integration for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together ci integration".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI CI Integration

## Overview

Set up CI/CD for Together AI inference integrations: run unit tests with mocked completion and embedding responses on every PR, validate live API connectivity for model inference on merge to main. Together AI provides an OpenAI-compatible API for 100+ open-source models including Llama, Mixtral, and FLUX, so CI pipelines verify prompt formatting, response parsing, model selection logic, and fine-tuning job management.

## GitHub Actions Workflow

```yaml
# .github/workflows/together-ci.yml
name: Together AI CI
on:
  pull_request:
    paths: ['src/together/**', 'tests/**']
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --reporter=verbose

  integration-tests:
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:integration
        env:
          TOGETHER_API_KEY: ${{ secrets.TOGETHER_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/together-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { generateCompletion, createEmbedding } from '../src/together-service';

vi.mock('../src/together-client', () => ({
  TogetherClient: vi.fn().mockImplementation(() => ({
    chatCompletion: vi.fn().mockResolvedValue({
      id: 'cmpl_abc123',
      model: 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
      choices: [{ message: { role: 'assistant', content: 'Hello! How can I help?' }, finish_reason: 'stop' }],
      usage: { prompt_tokens: 12, completion_tokens: 8, total_tokens: 20 },
    }),
    createEmbedding: vi.fn().mockResolvedValue({
      data: [{ embedding: new Array(768).fill(0.01), index: 0 }],
      model: 'togethercomputer/m2-bert-80M-8k-retrieval',
      usage: { total_tokens: 5 },
    }),
    listModels: vi.fn().mockResolvedValue([
      { id: 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo', type: 'chat' },
      { id: 'togethercomputer/m2-bert-80M-8k-retrieval', type: 'embedding' },
    ]),
  })),
}));

describe('Together AI Service', () => {
  it('generates a chat completion', async () => {
    const result = await generateCompletion('Hello', { model: 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo' });
    expect(result.choices[0].finish_reason).toBe('stop');
    expect(result.usage.total_tokens).toBe(20);
  });

  it('creates embeddings for text', async () => {
    const result = await createEmbedding('test text');
    expect(result.data[0].embedding).toHaveLength(768);
  });
});
```

## Integration Tests

```typescript
// tests/integration/together.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.TOGETHER_API_KEY;

describe.skipIf(!hasKey)('Together AI Live API', () => {
  it('runs inference via OpenAI-compatible endpoint', async () => {
    const res = await fetch('https://api.together.xyz/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.TOGETHER_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
        messages: [{ role: 'user', content: 'Say hello in one word.' }],
        max_tokens: 10,
      }),
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.choices[0].message.content).toBeDefined();
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at api.together.xyz/settings |
| `Model not found` | Wrong model ID string | Use `client.models.list()` to get valid IDs |
| `429 Rate limit` | Too many concurrent requests | Implement exponential backoff with 3 retries |
| `500 Server error` | Model overloaded or cold start | Retry with backoff; use Turbo variants for faster cold starts |
| Embedding dimension mismatch | Wrong model for embeddings | Use `m2-bert-80M-8k-retrieval` for embeddings, not chat models |

## Resources

- [Together AI Documentation](https://docs.together.ai/)
- [Together AI API Reference](https://docs.together.ai/reference/chat-completions-1)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See related Together AI skills for fine-tuning and batch inference patterns.
