---
name: elevenlabs-ci-integration
description: |
  Configure CI/CD pipelines for ElevenLabs with mocked unit tests and gated integration tests.
  Use when setting up GitHub Actions for TTS projects, configuring CI test strategies,
  or automating ElevenLabs integration validation.
  Trigger: "elevenlabs CI", "elevenlabs GitHub Actions",
  "elevenlabs automated tests", "CI elevenlabs", "elevenlabs pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, ci, github-actions]
compatible-with: claude-code
---

# ElevenLabs CI Integration

## Overview

Set up CI/CD pipelines that test ElevenLabs integrations without burning character quota on every PR. Uses a two-tier strategy: mocked unit tests on every push, gated integration tests on demand.

## Prerequisites

- GitHub repository with Actions enabled
- ElevenLabs API key for integration tests
- npm/pnpm project with vitest configured

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/elevenlabs-tests.yml
name: ElevenLabs Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Tier 1: Always runs — no API key needed, no quota cost
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
        env:
          # Mock mode — no real API calls
          ELEVENLABS_API_KEY: "sk_test_mock_key_for_ci"

  # Tier 2: Only on main or manual trigger — uses real API
  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.event_name == 'workflow_dispatch'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci

      # Check quota before running integration tests
      - name: Check ElevenLabs quota
        env:
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
        run: |
          REMAINING=$(curl -s https://api.elevenlabs.io/v1/user \
            -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
            jq '.subscription | (.character_limit - .character_count)')
          echo "Characters remaining: $REMAINING"
          if [ "$REMAINING" -lt 5000 ]; then
            echo "::warning::Low ElevenLabs quota ($REMAINING chars). Skipping integration tests."
            echo "SKIP_INTEGRATION=true" >> $GITHUB_ENV
          fi

      - name: Run integration tests
        if: env.SKIP_INTEGRATION != 'true'
        env:
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
          ELEVENLABS_INTEGRATION: "1"
        run: npm run test:integration
```

### Step 2: Configure Repository Secrets

```bash
# Store API key as GitHub secret (use a test/dev key, NOT production)
gh secret set ELEVENLABS_API_KEY --body "sk_your_test_key_here"

# Optional: webhook secret for webhook tests
gh secret set ELEVENLABS_WEBHOOK_SECRET --body "whsec_your_secret_here"
```

### Step 3: Unit Test with SDK Mock

```typescript
// tests/unit/tts-service.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the entire SDK — no API calls, no quota usage
vi.mock("@elevenlabs/elevenlabs-js", () => ({
  ElevenLabsClient: vi.fn().mockImplementation(() => ({
    textToSpeech: {
      convert: vi.fn().mockResolvedValue(
        new ReadableStream({
          start(controller) {
            controller.enqueue(new Uint8Array([0xFF, 0xFB, 0x90, 0x00])); // MP3 header
            controller.close();
          },
        })
      ),
      stream: vi.fn().mockImplementation(async function* () {
        yield new Uint8Array([0xFF, 0xFB, 0x90, 0x00]);
      }),
    },
    voices: {
      getAll: vi.fn().mockResolvedValue({
        voices: [
          { voice_id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel", category: "premade" },
        ],
      }),
    },
    user: {
      get: vi.fn().mockResolvedValue({
        subscription: { tier: "pro", character_count: 1000, character_limit: 500000 },
      }),
    },
  })),
}));

import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

describe("TTS Service", () => {
  let client: InstanceType<typeof ElevenLabsClient>;

  beforeEach(() => {
    client = new ElevenLabsClient();
  });

  it("should call TTS with correct parameters", async () => {
    await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
      text: "Test speech",
      model_id: "eleven_multilingual_v2",
      voice_settings: { stability: 0.5, similarity_boost: 0.75 },
    });

    expect(client.textToSpeech.convert).toHaveBeenCalledWith(
      "21m00Tcm4TlvDq8ikWAM",
      expect.objectContaining({
        text: "Test speech",
        model_id: "eleven_multilingual_v2",
      })
    );
  });

  it("should handle voice listing", async () => {
    const result = await client.voices.getAll();
    expect(result.voices).toHaveLength(1);
    expect(result.voices[0].name).toBe("Rachel");
  });
});
```

### Step 4: Integration Test (Gated)

```typescript
// tests/integration/tts-smoke.test.ts
import { describe, it, expect } from "vitest";

const SKIP = !process.env.ELEVENLABS_INTEGRATION;

describe.skipIf(SKIP)("ElevenLabs Integration", () => {
  it("should generate audio from text", async () => {
    const { ElevenLabsClient } = await import("@elevenlabs/elevenlabs-js");
    const client = new ElevenLabsClient();

    // Use Flash model + short text to minimize quota usage
    const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
      text: "CI test.",  // 8 characters = 4 credits (Flash)
      model_id: "eleven_flash_v2_5",
      output_format: "mp3_22050_32",
    });

    expect(audio).toBeDefined();
  }, 30_000);

  it("should list voices", async () => {
    const { ElevenLabsClient } = await import("@elevenlabs/elevenlabs-js");
    const client = new ElevenLabsClient();
    const { voices } = await client.voices.getAll();
    expect(voices.length).toBeGreaterThan(0);
  });
});
```

### Step 5: Package Scripts

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "test:integration": "ELEVENLABS_INTEGRATION=1 vitest run tests/integration/",
    "test:ci": "vitest run --coverage --reporter=junit --outputFile=test-results.xml"
  }
}
```

## CI Strategy Summary

| Tier | When | API Key | Quota Cost | Coverage |
|------|------|---------|------------|----------|
| Unit tests | Every push/PR | Mock key | 0 characters | SDK integration patterns |
| Integration | Main + manual | Real test key | ~50 chars | End-to-end TTS verification |
| Quota check | Before integration | Real test key | 0 (GET only) | Prevents surprise billing |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in CI | Missing repository secret | `gh secret set ELEVENLABS_API_KEY` |
| Integration tests timeout | Slow TTS generation | Increase test timeout to 30s; use Flash model |
| Quota depleted in CI | Too many integration runs | Use quota guard; limit to main branch only |
| Mock drift | SDK API changed | Update mocks when upgrading SDK |

## Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Vitest CI Configuration](https://vitest.dev/guide/ci.html)
- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js)

## Next Steps

For deployment patterns, see `elevenlabs-deploy-integration`.
