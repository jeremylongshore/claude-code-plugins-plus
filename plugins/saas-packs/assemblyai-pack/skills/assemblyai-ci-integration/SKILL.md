---
name: assemblyai-ci-integration
description: |
  Configure AssemblyAI CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating AssemblyAI transcription tests into your build process.
  Trigger with phrases like "assemblyai CI", "assemblyai GitHub Actions",
  "assemblyai automated tests", "CI assemblyai".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, ci]
compatible-with: claude-code
---

# AssemblyAI CI Integration

## Overview
Set up CI/CD pipelines for AssemblyAI transcription projects with unit tests (mocked), integration tests (live API), and cost-controlled test strategies.

## Prerequisites
- GitHub repository with Actions enabled
- AssemblyAI API key for testing
- npm/pnpm project configured

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/assemblyai-tests.yml
name: AssemblyAI Tests

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
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        # Unit tests use mocked AssemblyAI client — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    # Only run on main branch to limit API costs
    if: github.ref == 'refs/heads/main'
    env:
      ASSEMBLYAI_API_KEY: ${{ secrets.ASSEMBLYAI_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration
        timeout-minutes: 5
```

### Step 2: Configure Secrets

```bash
# Store API key as GitHub secret
gh secret set ASSEMBLYAI_API_KEY --body "your-test-api-key"

# Use a separate test key with lower quota to control costs
# Get one from https://www.assemblyai.com/app/account
```

### Step 3: Unit Tests (Mocked — Free, Fast)

```typescript
// tests/unit/transcription.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AssemblyAI } from 'assemblyai';

vi.mock('assemblyai', () => ({
  AssemblyAI: vi.fn().mockImplementation(() => ({
    transcripts: {
      transcribe: vi.fn().mockResolvedValue({
        id: 'mock-transcript-id',
        status: 'completed',
        text: 'Hello world, this is a test transcription.',
        audio_duration: 5.2,
        words: [
          { text: 'Hello', start: 0, end: 300, confidence: 0.99 },
          { text: 'world', start: 310, end: 600, confidence: 0.98 },
        ],
        utterances: [
          { speaker: 'A', text: 'Hello world, this is a test transcription.', start: 0, end: 5200 },
        ],
      }),
      get: vi.fn(),
      list: vi.fn().mockResolvedValue({
        transcripts: [{ id: 'mock-1', status: 'completed' }],
      }),
      delete: vi.fn().mockResolvedValue({}),
    },
    lemur: {
      task: vi.fn().mockResolvedValue({
        request_id: 'mock-lemur-id',
        response: 'This is a greeting recording.',
      }),
      summary: vi.fn().mockResolvedValue({
        response: 'The audio contains a greeting.',
      }),
    },
  })),
}));

describe('TranscriptionService', () => {
  it('should transcribe audio and return text', async () => {
    const client = new AssemblyAI({ apiKey: 'test-key' });
    const result = await client.transcripts.transcribe({
      audio: 'https://example.com/test.wav',
    });

    expect(result.status).toBe('completed');
    expect(result.text).toContain('Hello world');
    expect(result.words).toHaveLength(2);
  });

  it('should handle speaker diarization', async () => {
    const client = new AssemblyAI({ apiKey: 'test-key' });
    const result = await client.transcripts.transcribe({
      audio: 'https://example.com/test.wav',
      speaker_labels: true,
    });

    expect(result.utterances).toBeDefined();
    expect(result.utterances![0].speaker).toBe('A');
  });

  it('should run LeMUR task', async () => {
    const client = new AssemblyAI({ apiKey: 'test-key' });
    const { response } = await client.lemur.task({
      transcript_ids: ['mock-transcript-id'],
      prompt: 'Summarize.',
    });

    expect(response).toBeTruthy();
  });
});
```

### Step 4: Integration Tests (Live API — Controlled)

```typescript
// tests/integration/assemblyai.test.ts
import { describe, it, expect } from 'vitest';
import { AssemblyAI } from 'assemblyai';

// Use a short, free sample audio to minimize costs
const TEST_AUDIO = 'https://storage.googleapis.com/aai-web-samples/5_common_sports_702.wav';

const skipIfNoKey = !process.env.ASSEMBLYAI_API_KEY;

describe.skipIf(skipIfNoKey)('AssemblyAI Integration', () => {
  const client = new AssemblyAI({
    apiKey: process.env.ASSEMBLYAI_API_KEY!,
  });

  it('should transcribe a short audio file', async () => {
    const transcript = await client.transcripts.transcribe({
      audio: TEST_AUDIO,
    });

    expect(transcript.status).toBe('completed');
    expect(transcript.text).toBeTruthy();
    expect(transcript.audio_duration).toBeGreaterThan(0);
    expect(transcript.words?.length).toBeGreaterThan(0);
  }, 60_000); // 60s timeout for transcription

  it('should list recent transcripts', async () => {
    const page = await client.transcripts.list({ limit: 5 });
    expect(page.transcripts).toBeDefined();
    expect(Array.isArray(page.transcripts)).toBe(true);
  });

  it('should run LeMUR on a transcript', async () => {
    const transcript = await client.transcripts.transcribe({
      audio: TEST_AUDIO,
    });

    const { response } = await client.lemur.task({
      transcript_ids: [transcript.id],
      prompt: 'What is this about? One sentence.',
    });

    expect(response).toBeTruthy();
    expect(response.length).toBeGreaterThan(10);
  }, 90_000);
});
```

### Step 5: Cost-Controlled Testing Strategy

```yaml
# Only run integration tests on main (not on every PR)
# Use short sample audio (~30s = ~$0.002 per test run)
# Cache transcript IDs across tests when possible

# In package.json:
# "test": "vitest --exclude='**/integration/**'"
# "test:integration": "vitest --include='**/integration/**'"
```

## Output
- Unit test pipeline (mocked, runs on every PR)
- Integration test pipeline (live API, runs on main only)
- GitHub Secrets configured for API key
- Cost-controlled test strategy

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | `gh secret set ASSEMBLYAI_API_KEY` |
| Integration test timeout | Slow transcription | Increase timeout to 60s+, use short audio |
| Flaky tests | Network latency | Add retry logic, use `vitest.retries(2)` |
| High test costs | Long audio files | Use 30-second sample audio |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)
- [AssemblyAI Node SDK](https://github.com/AssemblyAI/assemblyai-node-sdk)

## Next Steps
For deployment patterns, see `assemblyai-deploy-integration`.
