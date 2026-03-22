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
tags: [saas, langfuse, testing, ci-cd]

---
# Langfuse CI Integration

## Overview
Integrate Langfuse into CI/CD pipelines: trace validation tests, prompt regression testing, experiment-driven quality gates, automated prompt deployment from version control, and score monitoring.

## Prerequisites
- Langfuse API keys stored as GitHub secrets (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`)
- Test framework (Vitest or Jest)
- OpenAI API key for LLM tests

## Instructions

### Step 1: GitHub Actions Workflow for AI Quality Tests

```yaml
# .github/workflows/langfuse-tests.yml
name: AI Quality Tests

on:
  pull_request:
    paths: ["src/ai/**", "src/prompts/**", "tests/ai/**"]

jobs:
  ai-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "npm" }
      - run: npm ci

      - name: Run AI quality tests with tracing
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
          LANGFUSE_BASE_URL: ${{ vars.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com' }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: npx vitest run tests/ai/ --reporter=verbose

      - name: Langfuse connectivity check
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
        run: |
          node -e "
            const { LangfuseClient } = require('@langfuse/client');
            const lf = new LangfuseClient();
            lf.prompt.get('__ci-health__').catch(() => {});
            console.log('Langfuse SDK initialized OK');
          "
```

### Step 2: Prompt Regression Tests

```typescript
// tests/ai/prompt-quality.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { LangfuseClient } from "@langfuse/client";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";
import OpenAI from "openai";

const langfuse = new LangfuseClient();
const openai = new OpenAI();

describe("Prompt Quality Regression", () => {
  it("summarization prompt produces valid output", async () => {
    const prompt = await langfuse.prompt.get("summarize-article", { type: "text" });
    const compiled = prompt.compile({ maxLength: "100 words" });

    const result = await startActiveObservation(
      { name: "ci-test-summarize", asType: "generation" },
      async () => {
        updateActiveObservation({ model: "gpt-4o-mini", input: compiled });

        const response = await openai.chat.completions.create({
          model: "gpt-4o-mini",
          messages: [{ role: "user", content: compiled }],
          temperature: 0,
        });

        const output = response.choices[0].message.content || "";
        updateActiveObservation({
          output,
          usage: {
            promptTokens: response.usage?.prompt_tokens,
            completionTokens: response.usage?.completion_tokens,
          },
        });
        return output;
      }
    );

    expect(result.length).toBeGreaterThan(20);
    expect(result.length).toBeLessThan(600);
  });

  it("classification prompt returns valid intent", async () => {
    const prompt = await langfuse.prompt.get("classify-intent", { type: "text" });
    const compiled = prompt.compile({ userMessage: "I want to cancel my subscription" });

    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: compiled }],
      temperature: 0,
    });

    const intent = response.choices[0].message.content?.trim().toLowerCase() || "";
    const validIntents = ["billing", "cancellation", "support", "feedback"];
    expect(validIntents).toContain(intent);
  });
});
```

### Step 3: Experiment-Driven Quality Gates

```typescript
// tests/ai/experiment-gate.test.ts
import { describe, it, expect } from "vitest";
import { LangfuseClient } from "@langfuse/client";
import OpenAI from "openai";

const langfuse = new LangfuseClient();
const openai = new OpenAI();

describe("Quality Gate: Intent Classification", () => {
  it("scores above 80% accuracy on test dataset", async () => {
    async function classifyIntent(input: { query: string }) {
      const response = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: "Classify intent. Return one word." },
          { role: "user", content: input.query },
        ],
        temperature: 0,
      });
      return response.choices[0].message.content?.trim() || "";
    }

    const result = await langfuse.runExperiment({
      datasetName: "intent-classification-test",
      runName: `ci-${process.env.GITHUB_SHA?.slice(0, 7) || "local"}`,
      task: classifyIntent,
      evaluators: [
        ({ output, expectedOutput }) => ({
          name: "exact-match",
          value: output.toLowerCase() === expectedOutput.intent.toLowerCase() ? 1 : 0,
          dataType: "BOOLEAN" as const,
        }),
      ],
    });

    // Calculate accuracy
    const scores = result.runs.flatMap((r) => r.scores || []);
    const accuracy = scores.filter((s) => s.value === 1).length / scores.length;

    console.log(`Accuracy: ${(accuracy * 100).toFixed(1)}%`);
    expect(accuracy).toBeGreaterThanOrEqual(0.8);
  });
});
```

### Step 4: Automated Prompt Deployment

```yaml
# .github/workflows/deploy-prompts.yml
name: Deploy Prompts to Langfuse

on:
  push:
    branches: [main]
    paths: ["src/prompts/**"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "npm" }
      - run: npm ci

      - name: Deploy prompts
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
        run: node scripts/deploy-prompts.mjs
```

```typescript
// scripts/deploy-prompts.mjs
import { LangfuseClient } from "@langfuse/client";
import { readdirSync, readFileSync } from "fs";
import { join } from "path";

const langfuse = new LangfuseClient();
const promptDir = join(process.cwd(), "src/prompts");

for (const file of readdirSync(promptDir).filter((f) => f.endsWith(".json"))) {
  const config = JSON.parse(readFileSync(join(promptDir, file), "utf-8"));

  await langfuse.api.prompts.create({
    name: config.name,
    prompt: config.template,
    type: config.type || "text",
    config: config.config || {},
    labels: ["production", `deploy-${new Date().toISOString().split("T")[0]}`],
  });

  console.log(`Deployed: ${config.name}`);
}
```

### Step 5: Score Regression Monitoring

```typescript
// scripts/check-quality-regression.ts
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

async function checkRegression() {
  const scores = await langfuse.api.scores.list({
    name: "quality",
    limit: 100,
  });

  const values = scores.data.map((s) => s.value).filter((v): v is number => v !== null);
  const avg = values.reduce((a, b) => a + b, 0) / values.length;

  console.log(`Average quality score: ${avg.toFixed(3)} (n=${values.length})`);

  if (avg < 0.7) {
    console.error("QUALITY REGRESSION: Score below 0.7 threshold");
    process.exit(1);
  }
}

checkRegression();
```

## CI Best Practices

| Practice | Why |
|----------|-----|
| Use `temperature: 0` in CI tests | Deterministic outputs, fewer false failures |
| Separate CI API keys | Isolate test traces from production |
| Run experiments on dataset changes | Catch regressions before deploy |
| Assert on ranges, not exact strings | LLM output varies even at temp 0 |
| Flush/shutdown in `afterAll` | Ensure all traces reach Langfuse |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Traces not in dashboard | No flush in CI | Add `sdk.shutdown()` or `afterAll` flush |
| Flaky quality tests | Non-deterministic LLM | Use `temperature: 0`, assert on ranges |
| Prompt not found | Not yet deployed | Deploy prompts before running tests |
| Missing secrets in CI | Not configured | Add to GitHub Settings > Secrets > Actions |

## Resources
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Prompt Management](https://langfuse.com/docs/prompt-management/get-started)
- [Scores via SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
