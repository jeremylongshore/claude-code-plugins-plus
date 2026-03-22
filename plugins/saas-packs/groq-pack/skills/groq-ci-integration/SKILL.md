---
name: groq-ci-integration
description: |
  Configure Groq CI/CD integration with GitHub Actions, testing, and model validation.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Groq tests into your build process.
  Trigger with phrases like "groq CI", "groq GitHub Actions",
  "groq automated tests", "CI groq".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, testing, ci-cd]

---
# Groq CI Integration

## Overview
Set up CI/CD pipelines for Groq integrations with unit tests (mocked), integration tests (live API), and model deprecation checks. Groq's fast inference makes live integration tests practical in CI -- a completion round-trip takes < 500ms.

## Prerequisites
- GitHub repository with Actions enabled
- Groq API key stored as GitHub secret
- vitest or jest for testing

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/groq-tests.yml
name: Groq Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"  # Weekly model deprecation check

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm test -- --coverage
        # Unit tests use mocked groq-sdk -- no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'  # Only on push to main
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run Groq integration tests
        run: GROQ_INTEGRATION=1 npx vitest tests/groq.integration.ts --reporter=verbose
        timeout-minutes: 2

  model-check:
    runs-on: ubuntu-latest
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - name: Check for deprecated models
        run: |
          set -euo pipefail
          # Get current models from Groq API
          MODELS=$(curl -sf https://api.groq.com/openai/v1/models \
            -H "Authorization: Bearer $GROQ_API_KEY" | jq -r '.data[].id')

          # Check our code references valid models
          USED=$(grep -roh "model.*['\"].*['\"]" src/ --include="*.ts" | \
            grep -oP "(?<=['\"])[\w./-]+(?=['\"])" | sort -u)

          echo "=== Models in our code ==="
          echo "$USED"
          echo ""
          echo "=== Available on Groq ==="
          echo "$MODELS"

          # Flag any model in our code that's not in the API response
          MISSING=""
          while IFS= read -r model; do
            if ! echo "$MODELS" | grep -qF "$model"; then
              MISSING="$MISSING\n  - $model"
            fi
          done <<< "$USED"

          if [ -n "$MISSING" ]; then
            echo "WARNING: These models in code are not available on Groq:$MISSING"
            exit 1
          fi
          echo "All models valid."
```

### Step 2: Configure Secrets
```bash
# Store Groq API key as GitHub secret
gh secret set GROQ_API_KEY --body "gsk_your_ci_key_here"

# Use a separate key for CI (easier to rotate, track usage)
```

### Step 3: Integration Test Suite
```typescript
// tests/groq.integration.ts
import { describe, it, expect } from "vitest";
import Groq from "groq-sdk";

const shouldRun = !!process.env.GROQ_INTEGRATION;

describe.skipIf(!shouldRun)("Groq API Integration", () => {
  const groq = new Groq();

  it("lists available models", async () => {
    const models = await groq.models.list();
    expect(models.data.length).toBeGreaterThan(0);

    const ids = models.data.map((m) => m.id);
    expect(ids).toContain("llama-3.1-8b-instant");
    expect(ids).toContain("llama-3.3-70b-versatile");
  }, 10_000);

  it("completes a chat request with 8B model", async () => {
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Reply with exactly one word: PONG" }],
      temperature: 0,
      max_tokens: 10,
    });

    expect(result.choices[0].message.content).toContain("PONG");
    expect(result.usage?.total_tokens).toBeGreaterThan(0);
  }, 10_000);

  it("streams a response", async () => {
    const stream = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Count from 1 to 5." }],
      stream: true,
      max_tokens: 50,
    });

    let content = "";
    for await (const chunk of stream) {
      content += chunk.choices[0]?.delta?.content || "";
    }

    expect(content).toContain("1");
    expect(content).toContain("5");
  }, 10_000);

  it("returns JSON mode output", async () => {
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [
        { role: "system", content: "Respond with JSON: {\"status\": \"ok\"}" },
        { role: "user", content: "Health check" },
      ],
      response_format: { type: "json_object" },
      temperature: 0,
      max_tokens: 50,
    });

    const parsed = JSON.parse(result.choices[0].message.content!);
    expect(parsed).toHaveProperty("status");
  }, 10_000);
});
```

### Step 4: Release Workflow
```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ["v*"]

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm test
      - name: Verify Groq API in production
        run: GROQ_INTEGRATION=1 npx vitest tests/groq.integration.ts
      - run: npm run build
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## CI Best Practices
- Mock `groq-sdk` in unit tests (no API key needed, no network)
- Run integration tests only on `main` push (not PRs -- saves quota)
- Use `llama-3.1-8b-instant` for CI tests (cheapest, fastest)
- Set `max_tokens` low (5-50) in CI to minimize token usage
- Add `timeout-minutes: 2` to prevent hung jobs
- Schedule weekly model deprecation checks

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | `GROQ_API_KEY` not configured | `gh secret set GROQ_API_KEY` |
| Integration test timeout | Network issue or rate limit | Increase timeout, add retry |
| Model check fails | Model deprecated | Update model ID in source code |
| Flaky tests | Rate limiting in CI | Add backoff, run integration tests less often |

## Resources
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Model Deprecations](https://console.groq.com/docs/deprecations)

## Next Steps
For deployment patterns, see `groq-deploy-integration`.
