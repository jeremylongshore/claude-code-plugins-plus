---
name: ideogram-ci-integration
description: |
  Configure CI/CD pipelines for Ideogram integrations with GitHub Actions.
  Use when setting up automated testing, visual regression tests,
  or integrating Ideogram validation into your build process.
  Trigger with phrases like "ideogram CI", "ideogram GitHub Actions",
  "ideogram automated tests", "CI ideogram", "ideogram pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, testing, ci-cd]

---
# Ideogram CI Integration

## Overview
Set up CI/CD pipelines for Ideogram integrations. Since Ideogram has no free tier for API testing, CI strategies focus on: mocked unit tests (free), optional integration tests gated behind secrets, and prompt validation without API calls.

## Prerequisites
- GitHub repository with Actions enabled
- Ideogram API key for integration tests (optional)
- npm/pnpm project with vitest

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/ideogram-ci.yml
name: Ideogram Integration CI

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
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm test -- --reporter=verbose
      - run: npm run lint

  # Optional: runs only when secret is configured
  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      IDEOGRAM_API_KEY: ${{ secrets.IDEOGRAM_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run integration tests
        if: env.IDEOGRAM_API_KEY != ''
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 2: Configure Secrets
```bash
set -euo pipefail
# Store Ideogram API key in GitHub repository secrets
gh secret set IDEOGRAM_API_KEY

# Verify it was set
gh secret list
```

### Step 3: Unit Tests with Mocked API
```typescript
// tests/ideogram-generate.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

const mockGenerateResponse = {
  created: "2025-01-15T10:00:00Z",
  data: [{
    url: "https://ideogram.ai/assets/image/mock-123.png",
    prompt: "test prompt",
    resolution: "1024x1024",
    is_image_safe: true,
    seed: 42,
    style_type: "DESIGN",
  }],
};

describe("Ideogram Generate", () => {
  let fetchSpy: any;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(mockGenerateResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
  });

  afterEach(() => fetchSpy.mockRestore());

  it("sends correct headers", async () => {
    await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: { "Api-Key": "test-key", "Content-Type": "application/json" },
      body: JSON.stringify({ image_request: { prompt: "test" } }),
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      "https://api.ideogram.ai/generate",
      expect.objectContaining({
        headers: expect.objectContaining({ "Api-Key": "test-key" }),
      })
    );
  });

  it("parses response correctly", async () => {
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: { "Api-Key": "test-key", "Content-Type": "application/json" },
      body: JSON.stringify({ image_request: { prompt: "test" } }),
    });
    const result = await response.json();
    expect(result.data[0].seed).toBe(42);
    expect(result.data[0].is_image_safe).toBe(true);
  });

  it("handles 429 rate limit", async () => {
    fetchSpy.mockResolvedValueOnce(new Response("Rate limited", { status: 429 }));
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: { "Api-Key": "test-key", "Content-Type": "application/json" },
      body: JSON.stringify({ image_request: { prompt: "test" } }),
    });
    expect(response.status).toBe(429);
  });
});
```

### Step 4: Prompt Validation in CI (No API Key Required)
```typescript
// tests/prompt-validation.test.ts
import { describe, it, expect } from "vitest";

const VALID_STYLES = ["AUTO", "GENERAL", "REALISTIC", "DESIGN", "RENDER_3D", "ANIME"];
const VALID_ASPECTS = [
  "ASPECT_1_1", "ASPECT_16_9", "ASPECT_9_16", "ASPECT_3_2", "ASPECT_2_3",
  "ASPECT_4_3", "ASPECT_3_4", "ASPECT_10_16", "ASPECT_16_10", "ASPECT_1_3", "ASPECT_3_1",
];

function validateIdeogramRequest(req: any): string[] {
  const errors: string[] = [];
  if (!req.prompt || req.prompt.length === 0) errors.push("Prompt is required");
  if (req.prompt?.length > 10000) errors.push("Prompt exceeds 10,000 char limit");
  if (req.style_type && !VALID_STYLES.includes(req.style_type)) {
    errors.push(`Invalid style_type: ${req.style_type}`);
  }
  if (req.aspect_ratio && !VALID_ASPECTS.includes(req.aspect_ratio)) {
    errors.push(`Invalid aspect_ratio: ${req.aspect_ratio}`);
  }
  if (req.num_images && (req.num_images < 1 || req.num_images > 4)) {
    errors.push("num_images must be 1-4");
  }
  return errors;
}

describe("Prompt Validation", () => {
  it("accepts valid request", () => {
    const errors = validateIdeogramRequest({
      prompt: "A sunset over mountains",
      style_type: "REALISTIC",
      aspect_ratio: "ASPECT_16_9",
    });
    expect(errors).toHaveLength(0);
  });

  it("rejects empty prompt", () => {
    const errors = validateIdeogramRequest({ prompt: "" });
    expect(errors).toContain("Prompt is required");
  });

  it("rejects invalid style", () => {
    const errors = validateIdeogramRequest({ prompt: "test", style_type: "INVALID" });
    expect(errors[0]).toContain("Invalid style_type");
  });
});
```

### Step 5: Integration Test (API Key Required)
```typescript
// tests/integration/ideogram-live.test.ts
import { describe, it, expect } from "vitest";

describe.skipIf(!process.env.IDEOGRAM_API_KEY)("Ideogram Live API", () => {
  it("generates an image successfully", async () => {
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: {
        "Api-Key": process.env.IDEOGRAM_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_request: {
          prompt: "CI test: simple geometric shape",
          model: "V_2_TURBO",
          magic_prompt_option: "OFF",
        },
      }),
    });

    expect(response.status).toBe(200);
    const result = await response.json();
    expect(result.data).toHaveLength(1);
    expect(result.data[0].url).toContain("http");
    expect(result.data[0].is_image_safe).toBe(true);
  }, 30000); // 30s timeout for generation
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing in GitHub settings | `gh secret set IDEOGRAM_API_KEY` |
| Integration timeout | Generation takes 5-15s | Set `timeout-minutes: 5` |
| Flaky rate limits | Concurrent CI runs | Run integration tests on main only |
| Credits burned in CI | Too many integration tests | Mock in PRs, live tests on main only |

## Output
- GitHub Actions workflow with unit + integration jobs
- Mocked unit tests that run without API key
- Prompt validation tests (zero API calls)
- Gated integration tests for main branch only

## Resources
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Vitest Docs](https://vitest.dev/)
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)

## Next Steps
For deployment patterns, see `ideogram-deploy-integration`.
