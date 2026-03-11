# Deepgram CI Integration - Implementation Details

## GitHub Actions Workflow
```yaml
# .github/workflows/deepgram-ci.yml
name: Deepgram CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - name: Run integration tests
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY }}
        run: npm run test:integration
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  integration:
    runs-on: ubuntu-latest
    needs: [test, lint]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - name: Run Deepgram integration tests
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY }}
          DEEPGRAM_PROJECT_ID: ${{ secrets.DEEPGRAM_PROJECT_ID }}
        run: npm run test:deepgram
      - name: Smoke test
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY }}
        run: |
          npm run build
          npm run smoke-test

  deploy:
    runs-on: ubuntu-latest
    needs: [integration]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY_STAGING }}
        run: npm run deploy:staging
      - name: Run post-deploy tests
        env:
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY_STAGING }}
        run: npm run test:staging
```

## GitLab CI Configuration
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "20"

.node-template:
  image: node:${NODE_VERSION}
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/

unit-tests:
  extends: .node-template
  stage: test
  script:
    - npm ci
    - npm test
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'

integration-tests:
  extends: .node-template
  stage: test
  variables:
    DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY}
  script:
    - npm ci
    - npm run test:integration
  only:
    - main
    - develop

deploy-staging:
  extends: .node-template
  stage: deploy
  variables:
    DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY_STAGING}
  script:
    - npm ci
    - npm run deploy:staging
  environment:
    name: staging
  only:
    - main
```

## Integration Test Suite
```typescript
// tests/integration/deepgram.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { createClient, DeepgramClient } from '@deepgram/sdk';

describe('Deepgram Integration Tests', () => {
  let client: DeepgramClient;

  beforeAll(() => {
    const apiKey = process.env.DEEPGRAM_API_KEY;
    if (!apiKey) throw new Error('DEEPGRAM_API_KEY not set');
    client = createClient(apiKey);
  });

  it('should connect to Deepgram API', async () => {
    const { result, error } = await client.manage.getProjects();
    expect(error).toBeNull();
    expect(result).toBeDefined();
  });

  it('should transcribe audio from URL', async () => {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' },
      { model: 'nova-2', smart_format: true }
    );
    expect(error).toBeNull();
    expect(result.results.channels[0].alternatives[0].transcript).toBeTruthy();
  }, 30000);

  it('should handle invalid URLs gracefully', async () => {
    const { error } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://invalid.example.com/audio.wav' },
      { model: 'nova-2' }
    );
    expect(error).toBeDefined();
  });
});
```

## Smoke Test Script
```typescript
// scripts/smoke-test.ts
import { createClient } from '@deepgram/sdk';

async function smokeTest(): Promise<void> {
  console.log('Running Deepgram smoke test...');
  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  console.log('Testing API connectivity...');
  const { error: connectError } = await client.manage.getProjects();
  if (connectError) throw new Error(`API connectivity failed: ${connectError.message}`);
  console.log('  API connectivity OK');

  console.log('Testing transcription...');
  const { result, error: transcribeError } = await client.listen.prerecorded.transcribeUrl(
    { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' },
    { model: 'nova-2', smart_format: true }
  );
  if (transcribeError) throw new Error(`Transcription failed: ${transcribeError.message}`);

  const transcript = result.results.channels[0].alternatives[0].transcript;
  if (!transcript || transcript.length < 10) throw new Error('Transcription result too short');
  console.log('  Transcription OK');
  console.log('\nSmoke test passed!');
}

smokeTest()
  .then(() => process.exit(0))
  .catch((error) => { console.error('Smoke test failed:', error.message); process.exit(1); });
```

## Secret Rotation in CI
```yaml
# .github/workflows/rotate-keys.yml
name: Rotate Deepgram Keys

on:
  schedule:
    - cron: '0 0 1 * *'
  workflow_dispatch:

jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Rotate API key
        env:
          DEEPGRAM_ADMIN_KEY: ${{ secrets.DEEPGRAM_ADMIN_KEY }}
          DEEPGRAM_PROJECT_ID: ${{ secrets.DEEPGRAM_PROJECT_ID }}
          GH_TOKEN: ${{ secrets.GH_PAT }}
        run: |
          NEW_KEY=$(curl -s -X POST \
            "https://api.deepgram.com/v1/projects/$DEEPGRAM_PROJECT_ID/keys" \
            -H "Authorization: Token $DEEPGRAM_ADMIN_KEY" \
            -H "Content-Type: application/json" \
            -d '{"comment": "CI Key - rotated", "scopes": ["usage:write"]}' \
            | jq -r '.key')
          gh secret set DEEPGRAM_API_KEY --body "$NEW_KEY"
          echo "Key rotated successfully"
```
