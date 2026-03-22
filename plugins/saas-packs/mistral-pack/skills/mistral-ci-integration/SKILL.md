---
name: mistral-ci-integration
description: |
  Configure Mistral AI CI/CD integration with GitHub Actions and prompt testing.
  Use when setting up automated testing, prompt regression suites,
  or integrating Mistral AI quality gates into your build process.
  Trigger with phrases like "mistral CI", "mistral GitHub Actions",
  "mistral automated tests", "CI mistral", "prompt testing".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, testing, ci-cd]

---
# Mistral CI Integration

## Overview
Integrate Mistral AI validation into CI/CD pipelines: prompt regression tests, model response quality checks, cost estimation in PR comments, and deployment gates for prompt changes. Uses GitHub Actions with `MISTRAL_API_KEY` stored as a repository secret.

## Prerequisites
- `MISTRAL_API_KEY` stored as GitHub repository secret
- GitHub Actions configured
- Test framework (Vitest recommended)

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/mistral-tests.yml
name: Mistral AI Tests

on:
  pull_request:
    paths:
      - 'src/prompts/**'
      - 'src/ai/**'
      - 'tests/ai/**'

jobs:
  prompt-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci

      - name: Run prompt regression tests
        env:
          MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
        run: npx vitest run tests/ai/ --reporter=verbose

      - name: Cost estimation
        env:
          MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
        run: npx tsx scripts/estimate-costs.ts >> $GITHUB_STEP_SUMMARY
```

### Step 2: Prompt Regression Tests

```typescript
// tests/ai/mistral-prompts.test.ts
import { describe, it, expect } from 'vitest';
import { Mistral } from '@mistralai/mistralai';

const apiKey = process.env.MISTRAL_API_KEY;

describe.skipIf(!apiKey)('Mistral Prompt Regression', () => {
  const client = new Mistral({ apiKey: apiKey! });

  it('summarization produces 2-3 sentences', async () => {
    const result = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [
        { role: 'system', content: 'Summarize in 2-3 sentences.' },
        { role: 'user', content: 'TypeScript is a typed superset of JavaScript that compiles to plain JavaScript. It adds optional static typing and class-based OOP.' },
      ],
      maxTokens: 150,
      temperature: 0, // Deterministic for regression
    });

    const content = result.choices?.[0]?.message?.content ?? '';
    expect(content.length).toBeGreaterThan(20);
    expect(content.split(/[.!?]+/).filter(Boolean).length).toBeGreaterThanOrEqual(2);
  }, 15_000);

  it('classification returns valid category', async () => {
    const result = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [
        { role: 'system', content: 'Classify as: bug, feature, question. Reply with one word only.' },
        { role: 'user', content: 'The login page crashes on mobile devices' },
      ],
      maxTokens: 10,
      temperature: 0,
    });

    const category = result.choices?.[0]?.message?.content?.trim().toLowerCase();
    expect(['bug', 'feature', 'question']).toContain(category);
  }, 15_000);

  it('JSON mode returns valid JSON', async () => {
    const result = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Return {"status": "ok"} as JSON' }],
      responseFormat: { type: 'json_object' },
      maxTokens: 50,
      temperature: 0,
    });

    const content = result.choices?.[0]?.message?.content ?? '';
    expect(() => JSON.parse(content)).not.toThrow();
  }, 15_000);

  it('respects maxTokens limit', async () => {
    const result = await client.chat.complete({
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Write a long essay about AI' }],
      maxTokens: 50,
    });

    expect(result.usage?.completionTokens).toBeLessThanOrEqual(50);
  }, 15_000);
});
```

### Step 3: Cost Estimation Script

```typescript
// scripts/estimate-costs.ts
import { readdirSync, readFileSync } from 'fs';
import { join } from 'path';

const PRICING: Record<string, { input: number; output: number }> = {
  'mistral-small-latest': { input: 0.1, output: 0.3 },
  'mistral-large-latest': { input: 0.5, output: 1.5 },
  'codestral-latest':     { input: 0.3, output: 0.9 },
  'mistral-embed':        { input: 0.1, output: 0 },
};

console.log('## Prompt Cost Estimates\n');
console.log('| File | Est. Tokens | Cost/call (small) | Cost/call (large) |');
console.log('|------|-------------|-------------------|-------------------|');

const promptDir = join(process.cwd(), 'src/prompts');
if (readdirSync(promptDir, { withFileTypes: true })) {
  for (const file of readdirSync(promptDir)) {
    const content = readFileSync(join(promptDir, file), 'utf-8');
    const tokens = Math.ceil(content.length / 4);
    const smallCost = (tokens / 1e6) * PRICING['mistral-small-latest'].input;
    const largeCost = (tokens / 1e6) * PRICING['mistral-large-latest'].input;

    console.log(`| ${file} | ~${tokens} | $${smallCost.toFixed(6)} | $${largeCost.toFixed(6)} |`);
  }
}
```

### Step 4: Model Validation Gate

```yaml
# .github/workflows/model-gate.yml
name: AI Model Gate

on:
  pull_request:
    paths: ['src/ai/**', 'src/prompts/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci

      - name: Validate model references
        run: |
          echo "## Model References" >> $GITHUB_STEP_SUMMARY
          grep -rn "mistral-\|codestral-\|pixtral-" src/ --include="*.ts" | \
            grep -oP "(mistral|codestral|pixtral)-[\w-]+" | sort -u | while read model; do
            echo "- \`$model\`" >> $GITHUB_STEP_SUMMARY
          done

      - name: Check for deprecated models
        run: |
          DEPRECATED="open-mistral-7b open-mixtral-8x7b mistral-tiny mistral-medium"
          for model in $DEPRECATED; do
            if grep -rq "$model" src/ --include="*.ts"; then
              echo "::warning::Deprecated model found: $model"
            fi
          done
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Tests fail in CI | Missing API key secret | Add `MISTRAL_API_KEY` to repo Settings > Secrets |
| Flaky prompt tests | Non-deterministic output | Set `temperature: 0` for regression tests |
| High CI costs | Running on every push | Only trigger on prompt/AI file changes via `paths:` |
| Test timeout | Slow API response | Set generous timeout (15s) per test |

## Examples

### Minimal Smoke Test
```yaml
- name: Mistral smoke test
  env:
    MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
  run: |
    curl -sf -X POST https://api.mistral.ai/v1/chat/completions \
      -H "Authorization: Bearer $MISTRAL_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"model":"mistral-small-latest","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' \
      | jq '.choices[0].message.content'
```

## Resources
- [Mistral API Reference](https://docs.mistral.ai/api/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

## Output
- GitHub Actions workflow for prompt testing
- Regression test suite with deterministic assertions
- Cost estimation in PR summaries
- Model validation gate catching deprecated references
