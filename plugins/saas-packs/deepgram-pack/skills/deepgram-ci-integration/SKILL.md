---
name: deepgram-ci-integration
description: |
  Configure Deepgram CI/CD integration for automated testing and deployment.
  Use when setting up continuous integration pipelines, automated testing,
  or deployment workflows for Deepgram integrations.
  Trigger: "deepgram CI", "deepgram CD", "deepgram pipeline",
  "deepgram github actions", "deepgram automated testing".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, deployment, testing, ci-cd]

---
# Deepgram CI Integration

## Overview
Set up CI/CD pipelines for Deepgram integrations with GitHub Actions. Includes unit tests with mocked SDK, integration tests against the real API, smoke tests, automated key rotation, and deployment gates.

## Prerequisites
- GitHub repository with Actions enabled
- `DEEPGRAM_API_KEY` stored as repository secret
- `@deepgram/sdk` and `vitest` installed
- Test fixtures committed (or downloaded in CI)

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/deepgram-ci.yml
name: Deepgram CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test -- --reporter=verbose
        # Unit tests use mocked SDK — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.event_name == 'push' || github.event.pull_request.head.repo.full_name == github.repository
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm run test:integration
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY }}
        timeout-minutes: 5

  smoke-test:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci && npm run build
      - name: Smoke test
        run: npx tsx scripts/smoke-test.ts
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY }}
        timeout-minutes: 2
```

### Step 2: Integration Test Suite

```typescript
// tests/integration/deepgram.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { createClient, DeepgramClient } from '@deepgram/sdk';

const SAMPLE_URL = 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav';

describe('Deepgram Integration', () => {
  let client: DeepgramClient;

  beforeAll(() => {
    const key = process.env.DEEPGRAM_API_KEY;
    if (!key) throw new Error('DEEPGRAM_API_KEY required for integration tests');
    client = createClient(key);
  });

  it('authenticates successfully', async () => {
    const { result, error } = await client.manage.getProjects();
    expect(error).toBeNull();
    expect(result.projects.length).toBeGreaterThan(0);
  });

  it('transcribes pre-recorded audio with Nova-3', async () => {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: SAMPLE_URL },
      { model: 'nova-3', smart_format: true }
    );
    expect(error).toBeNull();
    const alt = result.results.channels[0].alternatives[0];
    expect(alt.transcript).toContain('Life');
    expect(alt.confidence).toBeGreaterThan(0.85);
  }, 30000);

  it('returns word-level timing', async () => {
    const { result } = await client.listen.prerecorded.transcribeUrl(
      { url: SAMPLE_URL },
      { model: 'nova-3' }
    );
    const words = result.results.channels[0].alternatives[0].words;
    expect(words).toBeDefined();
    expect(words!.length).toBeGreaterThan(0);
    expect(words![0]).toHaveProperty('start');
    expect(words![0]).toHaveProperty('end');
    expect(words![0]).toHaveProperty('confidence');
  }, 30000);

  it('speaker diarization identifies speakers', async () => {
    const { result } = await client.listen.prerecorded.transcribeUrl(
      { url: SAMPLE_URL },
      { model: 'nova-3', diarize: true }
    );
    const words = result.results.channels[0].alternatives[0].words;
    expect(words?.some((w: any) => w.speaker !== undefined)).toBe(true);
  }, 30000);

  it('TTS generates audio stream', async () => {
    const response = await client.speak.request(
      { text: 'CI test.' },
      { model: 'aura-2-thalia-en', encoding: 'linear16', container: 'wav' }
    );
    const stream = await response.getStream();
    expect(stream).toBeTruthy();
  }, 15000);
});
```

### Step 3: Smoke Test Script

```typescript
// scripts/smoke-test.ts
import { createClient } from '@deepgram/sdk';

const SAMPLE_URL = 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav';

async function smokeTest() {
  console.log('Deepgram Smoke Test');
  console.log('='.repeat(40));

  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  let passed = 0;
  let failed = 0;

  // Test 1: Authentication
  try {
    const { error } = await client.manage.getProjects();
    if (error) throw error;
    console.log('[PASS] Authentication');
    passed++;
  } catch (err: any) {
    console.error(`[FAIL] Authentication: ${err.message}`);
    failed++;
  }

  // Test 2: Pre-recorded transcription
  try {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: SAMPLE_URL },
      { model: 'nova-3', smart_format: true }
    );
    if (error) throw error;
    if (!result.results.channels[0].alternatives[0].transcript) {
      throw new Error('Empty transcript');
    }
    console.log('[PASS] Pre-recorded transcription');
    passed++;
  } catch (err: any) {
    console.error(`[FAIL] Pre-recorded transcription: ${err.message}`);
    failed++;
  }

  // Test 3: TTS
  try {
    const response = await client.speak.request(
      { text: 'Smoke test.' },
      { model: 'aura-2-thalia-en' }
    );
    const stream = await response.getStream();
    if (!stream) throw new Error('No audio stream');
    console.log('[PASS] Text-to-speech');
    passed++;
  } catch (err: any) {
    console.error(`[FAIL] Text-to-speech: ${err.message}`);
    failed++;
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

smokeTest();
```

### Step 4: Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "test:integration": "vitest run tests/integration/",
    "test:smoke": "tsx scripts/smoke-test.ts",
    "lint": "eslint src/ tests/",
    "typecheck": "tsc --noEmit"
  }
}
```

### Step 5: Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    exclude: ['tests/integration/**'],  // Integration tests run separately
    coverage: {
      include: ['src/**'],
      reporter: ['text', 'lcov'],
    },
  },
});
```

### Step 6: Automated Key Rotation (Scheduled)

```yaml
# .github/workflows/rotate-deepgram-key.yml
name: Rotate Deepgram API Key

on:
  schedule:
    - cron: '0 0 1 */3 *'  # Quarterly (1st of every 3rd month)
  workflow_dispatch:

jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - name: Rotate key
        run: |
          NEW_KEY=$(npx tsx scripts/rotate-key.ts)
          gh secret set DEEPGRAM_API_KEY --body "$NEW_KEY"
          echo "Key rotated successfully"
        env:
          DEEPGRAM_ADMIN_KEY: ${{ secrets.DEEPGRAM_ADMIN_KEY }}
          DEEPGRAM_PROJECT_ID: ${{ secrets.DEEPGRAM_PROJECT_ID }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Output
- GitHub Actions workflow (unit -> integration -> smoke)
- Integration test suite covering STT, diarization, TTS
- Smoke test script with pass/fail exit codes
- Vitest configuration with integration test separation
- Quarterly key rotation workflow

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Integration tests 401 | Secret not set or expired | Rotate `DEEPGRAM_API_KEY` secret |
| Smoke test timeout | API latency | Increase `timeout-minutes` |
| Tests pass locally, fail in CI | Missing env var | Check `secrets` are set in repo settings |
| Fork PRs can't access secrets | GitHub security | Skip integration tests on fork PRs |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest CI Configuration](https://vitest.dev/guide/ci.html)
- [Deepgram SDK Testing](https://developers.deepgram.com/docs/testing)
