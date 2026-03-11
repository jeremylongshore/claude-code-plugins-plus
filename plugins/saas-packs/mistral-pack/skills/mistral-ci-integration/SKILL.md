---
name: mistral-ci-integration
description: |
  Configure Mistral AI CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Mistral AI tests into your build process.
  Trigger with phrases like "mistral CI", "mistral GitHub Actions",
  "mistral automated tests", "CI mistral".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral CI Integration

## Overview
Integrate Mistral AI model validation and prompt testing into CI/CD pipelines. Covers automated prompt regression tests, model response quality checks, cost estimation in PRs, and deployment gates for prompt changes.

## Prerequisites
- Mistral API key stored as GitHub secret
- GitHub Actions configured
- Test framework (Vitest or Jest)
- Understanding of prompt versioning

## Instructions

### Step 1: GitHub Actions Workflow for Prompt Testing
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
        run: npm test -- --grep "mistral" --reporter=verbose

      - name: Estimate token costs
        env:
          MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
        run: node scripts/estimate-costs.js >> $GITHUB_STEP_SUMMARY
```

### Step 2: Prompt Regression Test Suite
```typescript
// tests/ai/mistral-prompts.test.ts
import { describe, it, expect } from 'vitest';
import { Mistral } from '@mistralai/mistralai';

const mistral = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });

describe('Mistral Prompt Regression', () => {
  it('summarization prompt returns valid output', async () => {
    const result = await mistral.chat.complete({
      model: 'mistral-small-latest',
      messages: [
        { role: 'system', content: 'Summarize in 2-3 sentences.' },
        { role: 'user', content: 'TypeScript is a typed superset of JavaScript...' },
      ],
      maxTokens: 150,
    });

    const content = result.choices?.[0]?.message?.content || '';
    expect(content.length).toBeGreaterThan(20);
    expect(content.split('.').length).toBeGreaterThanOrEqual(2);
  });

  it('classification prompt returns valid category', async () => {
    const result = await mistral.chat.complete({
      model: 'mistral-small-latest',
      messages: [
        { role: 'system', content: 'Classify as: bug, feature, question. Reply with one word.' },
        { role: 'user', content: 'The login page crashes on mobile devices' },
      ],
      maxTokens: 10,
    });

    const category = result.choices?.[0]?.message?.content?.trim().toLowerCase();
    expect(['bug', 'feature', 'question']).toContain(category);
  });

  it('respects token limits', async () => {
    const result = await mistral.chat.complete({
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Write a haiku about programming' }],
      maxTokens: 50,
    });

    expect(result.usage?.completionTokens).toBeLessThanOrEqual(50);
  });
});
```

### Step 3: Cost Estimation Script
```typescript
// scripts/estimate-costs.ts
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

const COST_PER_MILLION = {
  'mistral-small-latest': { input: 0.1, output: 0.3 },
  'mistral-medium-latest': { input: 0.275, output: 0.81 },
  'mistral-large-latest': { input: 2.0, output: 6.0 },
};

function estimatePromptCost(promptFile: string) {
  const content = readFileSync(promptFile, 'utf-8');
  const tokens = Math.ceil(content.length / 4);

  console.log(`| ${promptFile} | ~${tokens} tokens |`);

  for (const [model, costs] of Object.entries(COST_PER_MILLION)) {
    const costPer1k = (tokens / 1_000_000) * costs.input;
    console.log(`|   ${model} | $${costPer1k.toFixed(6)}/call |`);
  }
}

console.log('## Prompt Cost Estimates');
console.log('| File | Metric |');
console.log('|------|--------|');

const promptDir = join(process.cwd(), 'src/prompts');
for (const file of readdirSync(promptDir)) {
  estimatePromptCost(join(promptDir, file));
}
```

### Step 4: Deployment Gate for Model Changes
```yaml
# .github/workflows/deploy-gate.yml
name: AI Deployment Gate

on:
  pull_request:
    paths:
      - 'src/ai/models.ts'
      - 'src/prompts/**'

jobs:
  validate-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci

      - name: Validate model references
        run: |
          # Ensure all referenced models are valid
          grep -r "mistral-" src/ --include="*.ts" | \
            grep -oP "mistral-\w+-\w+" | sort -u | while read model; do
            echo "Checking model: $model"
          done

      - name: Run AI integration tests
        env:
          MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
        run: npm test -- tests/ai/ --reporter=verbose
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Tests fail in CI | Missing API key | Add `MISTRAL_API_KEY` to repo secrets |
| Flaky prompt tests | Non-deterministic output | Set `temperature: 0` for regression tests |
| High CI costs | Running on every push | Only trigger on prompt/AI file changes |
| Model deprecation | Using outdated model ID | Validate model names in CI |

## Examples

### Minimal CI Config
```yaml
- name: Quick Mistral smoke test
  env:
    MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
  run: |
    curl -s -X POST https://api.mistral.ai/v1/chat/completions \
      -H "Authorization: Bearer $MISTRAL_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"model":"mistral-small-latest","messages":[{"role":"user","content":"ping"}]}' \
      | jq '.choices[0].message.content'
```

## Resources
- [Mistral AI API Reference](https://docs.mistral.ai/api/)
- [Mistral Models](https://docs.mistral.ai/getting-started/models/)
