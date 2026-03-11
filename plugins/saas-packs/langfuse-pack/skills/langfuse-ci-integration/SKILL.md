---
name: langfuse-ci-integration
description: |
  Configure Langfuse CI/CD integration with GitHub Actions and automated testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Langfuse tests into your build process.
  Trigger with phrases like "langfuse CI", "langfuse GitHub Actions",
  "langfuse automated tests", "CI langfuse", "langfuse pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Langfuse CI Integration

## Overview
Integrate Langfuse observability and prompt management into CI/CD. Covers trace validation tests, prompt versioning checks, evaluation score regression testing, and automated prompt deployment from version control.

## Prerequisites
- Langfuse Cloud or self-hosted instance
- Langfuse API keys (public + secret) as GitHub secrets
- Test framework configured
- Understanding of Langfuse traces and prompts

## Instructions

### Step 1: CI Workflow for Trace Validation
```yaml
# .github/workflows/langfuse-tests.yml
name: Langfuse AI Quality Tests

on:
  pull_request:
    paths:
      - 'src/ai/**'
      - 'src/prompts/**'
      - 'tests/ai/**'

jobs:
  ai-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci

      - name: Run AI quality tests with tracing
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
          LANGFUSE_HOST: ${{ vars.LANGFUSE_HOST || 'https://cloud.langfuse.com' }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: npm test -- tests/ai/ --reporter=verbose

      - name: Flush Langfuse traces
        run: node -e "
          const { Langfuse } = require('langfuse');
          const lf = new Langfuse();
          lf.flushAsync().then(() => console.log('Traces flushed'));
        "
```

### Step 2: Prompt Regression Tests
```typescript
// tests/ai/prompt-quality.test.ts
import { describe, it, expect } from 'vitest';
import { Langfuse } from 'langfuse';

const langfuse = new Langfuse();

describe('Prompt Quality Regression', () => {
  it('summarization prompt produces valid output', async () => {
    const prompt = await langfuse.getPrompt('summarize-article');

    const trace = langfuse.trace({ name: 'ci-test-summarize' });
    const generation = trace.generation({
      name: 'summarize',
      prompt: prompt.prompt,
      model: 'gpt-4o-mini',
    });

    // Call your LLM with the prompt
    const result = await callLLM(prompt.compile({ maxLength: '100 words' }));

    generation.end({ output: result });
    trace.score({ name: 'has-content', value: result.length > 20 ? 1 : 0 });

    expect(result.length).toBeGreaterThan(20);
    expect(result.length).toBeLessThan(500);
  });

  it('classification prompt returns expected format', async () => {
    const prompt = await langfuse.getPrompt('classify-intent');
    const trace = langfuse.trace({ name: 'ci-test-classify' });

    const result = await callLLM(
      prompt.compile({ userMessage: 'I want to cancel my subscription' })
    );

    const validIntents = ['billing', 'cancellation', 'support', 'feedback'];
    expect(validIntents).toContain(result.trim().toLowerCase());

    trace.score({ name: 'valid-intent', value: 1 });
  });

  afterAll(async () => {
    await langfuse.flushAsync();
  });
});
```

### Step 3: Prompt Version Sync
```yaml
# .github/workflows/sync-prompts.yml
name: Sync Prompts to Langfuse

on:
  push:
    branches: [main]
    paths:
      - 'src/prompts/**'

jobs:
  sync-prompts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci

      - name: Deploy prompts to Langfuse
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
        run: node scripts/deploy-prompts.js
```

```typescript
// scripts/deploy-prompts.ts
import { Langfuse } from 'langfuse';
import { readdirSync, readFileSync } from 'fs';
import { join } from 'path';

const langfuse = new Langfuse();

async function deployPrompts() {
  const promptDir = join(process.cwd(), 'src/prompts');

  for (const file of readdirSync(promptDir)) {
    if (!file.endsWith('.json')) continue;

    const config = JSON.parse(readFileSync(join(promptDir, file), 'utf-8'));

    await langfuse.createPrompt({
      name: config.name,
      prompt: config.template,
      config: config.config || {},
      labels: ['production', `deployed-${new Date().toISOString().split('T')[0]}`],
    });

    console.log(`Deployed prompt: ${config.name}`);
  }

  await langfuse.flushAsync();
}

deployPrompts();
```

### Step 4: Evaluation Score Monitoring
```typescript
// scripts/check-scores.ts - Run as CI step
import { Langfuse } from 'langfuse';

const langfuse = new Langfuse();

async function checkScoreRegression() {
  // Fetch recent scores
  const scores = await langfuse.fetchScores({
    name: 'quality',
    limit: 100,
  });

  const avgScore = scores.data.reduce((s, sc) => s + sc.value, 0) / scores.data.length;

  console.log(`Average quality score: ${avgScore.toFixed(2)}`);

  if (avgScore < 0.7) {
    console.error('QUALITY REGRESSION: Score dropped below 0.7 threshold');
    process.exit(1);
  }
}

checkScoreRegression();
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Traces not appearing | Flush not called | Always call `flushAsync` in afterAll |
| Prompt not found | Wrong name or not deployed | Check prompt name matches exactly |
| Flaky quality tests | Non-deterministic LLM | Set temperature to 0, use broader assertions |
| Missing API keys | Not in GitHub secrets | Add both public and secret keys |

## Examples

### Minimal CI Smoke Test
```yaml
- name: Langfuse connectivity check
  env:
    LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
    LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
  run: |
    node -e "
      const { Langfuse } = require('langfuse');
      const lf = new Langfuse();
      lf.trace({ name: 'ci-health-check' });
      lf.flushAsync().then(() => console.log('Langfuse OK'));
    "
```

## Resources
- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Prompt Management](https://langfuse.com/docs/prompts)
- [Langfuse Evaluation](https://langfuse.com/docs/scores)
