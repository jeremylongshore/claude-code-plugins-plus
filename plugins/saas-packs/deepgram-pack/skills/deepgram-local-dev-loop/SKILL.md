---
name: deepgram-local-dev-loop
description: |
  Configure Deepgram local development workflow with testing and mocks.
  Use when setting up development environment, configuring test fixtures,
  or establishing rapid iteration patterns for Deepgram integration.
  Trigger: "deepgram local dev", "deepgram development setup",
  "deepgram test environment", "deepgram dev workflow", "deepgram mock".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, testing, workflow, development]

---
# Deepgram Local Dev Loop

## Overview
Set up a fast local development workflow for Deepgram: test fixtures with sample audio, mock responses for offline unit tests, Vitest integration tests against the real API, and a watch-mode transcription dev server.

## Prerequisites
- `@deepgram/sdk` installed, `DEEPGRAM_API_KEY` configured
- `npm install -D vitest tsx dotenv` for testing and dev server
- Optional: `curl` for downloading test fixtures

## Instructions

### Step 1: Project Structure

```bash
mkdir -p src tests/mocks fixtures
touch src/transcribe.ts tests/transcribe.test.ts tests/mocks/deepgram-responses.ts
```

### Step 2: Download Test Fixtures

```bash
# Deepgram provides free sample audio files
curl -o fixtures/nasa-podcast.wav \
  https://static.deepgram.com/examples/nasa-podcast.wav

curl -o fixtures/bueller.wav \
  https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav
```

### Step 3: Environment Config

```bash
# .env.development
DEEPGRAM_API_KEY=your-dev-key
DEEPGRAM_MODEL=nova-3

# .env.test (use a separate test key with low limits)
DEEPGRAM_API_KEY=your-test-key
DEEPGRAM_MODEL=base
```

```json
{
  "scripts": {
    "dev": "tsx watch src/transcribe.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "vitest run tests/integration/"
  }
}
```

### Step 4: Mock Deepgram Responses

```typescript
// tests/mocks/deepgram-responses.ts
export const mockPrerecordedResult = {
  metadata: {
    request_id: 'mock-request-id-001',
    created: '2026-01-01T00:00:00.000Z',
    duration: 12.5,
    channels: 1,
    models: ['nova-3'],
    model_info: { 'nova-3': { name: 'nova-3', version: '2026-01-01' } },
  },
  results: {
    channels: [{
      alternatives: [{
        transcript: 'Life moves pretty fast. If you don\'t stop and look around once in a while, you could miss it.',
        confidence: 0.98,
        words: [
          { word: 'life', start: 0.08, end: 0.32, confidence: 0.99, punctuated_word: 'Life' },
          { word: 'moves', start: 0.32, end: 0.56, confidence: 0.98, punctuated_word: 'moves' },
          { word: 'pretty', start: 0.56, end: 0.88, confidence: 0.97, punctuated_word: 'pretty' },
          { word: 'fast', start: 0.88, end: 1.12, confidence: 0.99, punctuated_word: 'fast.' },
        ],
      }],
    }],
    utterances: [{
      speaker: 0,
      transcript: 'Life moves pretty fast. If you don\'t stop and look around once in a while, you could miss it.',
      start: 0.08,
      end: 5.44,
      confidence: 0.98,
    }],
  },
};

export const mockLiveTranscript = {
  type: 'Results',
  channel_index: [0, 1],
  duration: 1.5,
  start: 0.0,
  is_final: true,
  speech_final: true,
  channel: {
    alternatives: [{
      transcript: 'Hello, how are you today?',
      confidence: 0.95,
      words: [
        { word: 'hello', start: 0.0, end: 0.3, confidence: 0.98, punctuated_word: 'Hello,' },
        { word: 'how', start: 0.35, end: 0.5, confidence: 0.96, punctuated_word: 'how' },
      ],
    }],
  },
};

export const mockTtsResponse = {
  content_type: 'audio/wav',
  request_id: 'mock-tts-001',
  model_name: 'aura-2-thalia-en',
  characters: { count: 42, limit: 100000 },
};
```

### Step 5: Unit Tests with Mocks

```typescript
// tests/transcribe.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mockPrerecordedResult } from './mocks/deepgram-responses';

// Mock the SDK
vi.mock('@deepgram/sdk', () => ({
  createClient: () => ({
    listen: {
      prerecorded: {
        transcribeUrl: vi.fn().mockResolvedValue({
          result: mockPrerecordedResult,
          error: null,
        }),
        transcribeFile: vi.fn().mockResolvedValue({
          result: mockPrerecordedResult,
          error: null,
        }),
      },
    },
    speak: {
      request: vi.fn().mockResolvedValue({
        getStream: () => Promise.resolve(null),
      }),
    },
  }),
}));

describe('DeepgramTranscriber', () => {
  it('transcribes URL and returns transcript text', async () => {
    const { createClient } = await import('@deepgram/sdk');
    const client = createClient('mock-key');

    const { result } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://example.com/audio.wav' },
      { model: 'nova-3', smart_format: true }
    );

    expect(result.results.channels[0].alternatives[0].transcript).toContain('Life moves');
    expect(result.metadata.duration).toBe(12.5);
    expect(result.metadata.request_id).toBe('mock-request-id-001');
  });

  it('returns word-level timing data', async () => {
    const { createClient } = await import('@deepgram/sdk');
    const client = createClient('mock-key');

    const { result } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://example.com/audio.wav' },
      { model: 'nova-3' }
    );

    const words = result.results.channels[0].alternatives[0].words;
    expect(words[0].word).toBe('life');
    expect(words[0].start).toBe(0.08);
    expect(words[0].confidence).toBeGreaterThan(0.9);
  });
});
```

### Step 6: Integration Tests (Real API)

```typescript
// tests/integration/deepgram.test.ts
import { describe, it, expect } from 'vitest';
import { createClient } from '@deepgram/sdk';

describe('Deepgram Integration', () => {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  it('transcribes sample audio URL', async () => {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav' },
      { model: 'nova-3', smart_format: true }
    );

    expect(error).toBeNull();
    expect(result.results.channels[0].alternatives[0].transcript).toBeTruthy();
    expect(result.results.channels[0].alternatives[0].confidence).toBeGreaterThan(0.8);
  }, 30000);

  it('verifies API key with project listing', async () => {
    const { result, error } = await client.manage.getProjects();
    expect(error).toBeNull();
    expect(result.projects.length).toBeGreaterThan(0);
  });
});
```

## Output
- Project structure with src, tests, fixtures directories
- Mock response objects matching real Deepgram API shape
- Unit tests with mocked SDK (no API calls)
- Integration tests against real API with timeout
- Watch mode for rapid iteration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Fixture 404 | Deepgram moved sample URL | Check latest URLs at developers.deepgram.com |
| `DEEPGRAM_API_KEY` undefined in test | `.env.test` not loaded | Configure Vitest `env` or use `dotenv/config` |
| Integration test timeout | Network or API slow | Increase timeout to 30000ms |
| Mock shape mismatch | API response changed | Update mocks from real response capture |

## Resources
- [Vitest Documentation](https://vitest.dev/)
- [Deepgram Sample Audio](https://static.deepgram.com/examples/)
- [SDK Testing Guide](https://developers.deepgram.com/docs/testing)

## Next Steps
Proceed to `deepgram-sdk-patterns` for production-ready code patterns.
