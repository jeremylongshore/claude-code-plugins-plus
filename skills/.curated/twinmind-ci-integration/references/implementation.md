# TwinMind CI Integration - Detailed Implementation

## GitHub Actions Workflow

```yaml
name: TwinMind Integration Tests

on:
  push:
    branches: [main, develop]
    paths: ['src/twinmind/**', 'tests/twinmind/**']
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'

env:
  NODE_VERSION: '20'

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}', cache: 'npm' }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}', cache: 'npm' }
      - run: npm ci
      - run: npm run test:unit
        env: { TWINMIND_API_KEY: '${{ secrets.TWINMIND_API_KEY_TEST }}' }

  integration-tests:
    runs-on: ubuntu-latest
    needs: [lint-and-typecheck, unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}', cache: 'npm' }
      - run: npm ci
      - run: npm run test:integration
        env:
          TWINMIND_API_KEY: '${{ secrets.TWINMIND_API_KEY_TEST }}'
          TWINMIND_WEBHOOK_SECRET: '${{ secrets.TWINMIND_WEBHOOK_SECRET }}'
        timeout-minutes: 10
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: test-results, path: coverage/ }

  api-health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check TwinMind API Health
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer ${{ secrets.TWINMIND_API_KEY_TEST }}" \
            https://api.twinmind.com/v1/health)
          if [ "$HTTP_CODE" != "200" ]; then exit 1; fi

  transcription-smoke-test:
    runs-on: ubuntu-latest
    needs: [integration-tests, api-health-check]
    if: github.event_name == 'schedule' || github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ env.NODE_VERSION }}', cache: 'npm' }
      - run: npm ci
      - run: npm run test:smoke
        env:
          TWINMIND_API_KEY: '${{ secrets.TWINMIND_API_KEY_TEST }}'
          TEST_AUDIO_URL: '${{ secrets.TEST_AUDIO_URL }}'
        timeout-minutes: 5
```

## Unit Tests

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('TwinMindClient', () => {
  let client: TwinMindClient;
  beforeEach(() => { client = new TwinMindClient({ apiKey: 'test_api_key' }); });

  it('should send correct request for transcription', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ id: 'tr_123', status: 'processing' }) });
    global.fetch = mockFetch;
    await client.transcribe('https://example.com/audio.mp3');
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/transcribe'), expect.objectContaining({ method: 'POST' }));
  });

  it('should handle rate limit errors', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 429, headers: new Headers({ 'Retry-After': '60' }) });
    await expect(client.transcribe('https://example.com/audio.mp3')).rejects.toThrow(/rate limit/i);
  });
});
```

## Integration Tests

```typescript
describe('TwinMind Transcription Integration', () => {
  let client: TwinMindClient;
  beforeAll(() => {
    const apiKey = process.env.TWINMIND_API_KEY;
    if (!apiKey) throw new Error('TWINMIND_API_KEY required');
    client = new TwinMindClient({ apiKey });
  });

  it('should return healthy status', async () => {
    expect(await client.healthCheck()).toBe(true);
  });

  it('should transcribe test audio', async () => {
    const audioUrl = process.env.TEST_AUDIO_URL;
    if (!audioUrl) return;
    const transcript = await client.transcribe(audioUrl, { language: 'en' });
    expect(transcript.text.length).toBeGreaterThan(0);
  }, 60000);
});
```

## Smoke Test Runner

```typescript
async function runSmokeTests(): Promise<SmokeTestResult[]> {
  const results: SmokeTestResult[] = [];
  const client = new TwinMindClient({ apiKey: process.env.TWINMIND_API_KEY! });

  // Health Check
  const t1 = Date.now();
  try { await client.healthCheck(); results.push({ name: 'Health Check', passed: true, duration: Date.now() - t1 }); }
  catch (e: any) { results.push({ name: 'Health Check', passed: false, duration: Date.now() - t1, error: e.message }); }

  // Account Access
  const t2 = Date.now();
  try { const a = await client.getAccount(); results.push({ name: 'Account', passed: !!a.id, duration: Date.now() - t2 }); }
  catch (e: any) { results.push({ name: 'Account', passed: false, duration: Date.now() - t2, error: e.message }); }

  return results;
}

const results = await runSmokeTests();
const allPassed = results.every(r => r.passed);
process.exit(allPassed ? 0 : 1);
```

## GitLab CI

```yaml
stages: [lint, test, integration]

.node-template: &node-template
  image: node:20
  cache: { key: ${CI_COMMIT_REF_SLUG}, paths: [node_modules/] }

lint:
  <<: *node-template
  stage: lint
  script: [npm ci, npm run lint, npm run typecheck]

unit-tests:
  <<: *node-template
  stage: test
  script: [npm ci, npm run test:unit]

integration-tests:
  <<: *node-template
  stage: integration
  variables: { TWINMIND_API_KEY: $TWINMIND_API_KEY_TEST }
  script: [npm ci, npm run test:integration]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## Vitest Config

```typescript
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: { provider: 'v8', reporter: ['text', 'json', 'html'] },
    testTimeout: 30000,
  },
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
