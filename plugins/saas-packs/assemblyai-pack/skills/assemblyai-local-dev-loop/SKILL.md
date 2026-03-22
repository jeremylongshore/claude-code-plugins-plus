---
name: assemblyai-local-dev-loop
description: |
  Configure AssemblyAI local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with AssemblyAI.
  Trigger with phrases like "assemblyai dev setup", "assemblyai local development",
  "assemblyai dev environment", "develop with assemblyai".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription]
compatible-with: claude-code
---

# AssemblyAI Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for AssemblyAI transcription and LeMUR projects with mocking, caching, and hot reload.

## Prerequisites
- Completed `assemblyai-install-auth` setup
- Node.js 18+ with npm/pnpm
- TypeScript project with `tsx` or `ts-node`

## Instructions

### Step 1: Project Structure

```
my-assemblyai-project/
├── src/
│   ├── assemblyai/
│   │   ├── client.ts       # Singleton client
│   │   ├── transcribe.ts   # Transcription helpers
│   │   └── lemur.ts        # LeMUR helpers
│   └── index.ts
├── tests/
│   ├── transcribe.test.ts
│   └── fixtures/
│       └── sample-transcript.json  # Cached API response
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
└── package.json
```

### Step 2: Dev Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "transcribe": "tsx src/assemblyai/transcribe.ts"
  },
  "devDependencies": {
    "tsx": "^4.7.0",
    "vitest": "^1.6.0",
    "dotenv": "^16.4.0"
  },
  "dependencies": {
    "assemblyai": "^4.8.0"
  }
}
```

### Step 3: Singleton Client with Env Loading

```typescript
// src/assemblyai/client.ts
import 'dotenv/config';
import { AssemblyAI } from 'assemblyai';

let instance: AssemblyAI | null = null;

export function getClient(): AssemblyAI {
  if (!instance) {
    if (!process.env.ASSEMBLYAI_API_KEY) {
      throw new Error('ASSEMBLYAI_API_KEY not set. Copy .env.example to .env.local');
    }
    instance = new AssemblyAI({
      apiKey: process.env.ASSEMBLYAI_API_KEY,
    });
  }
  return instance;
}
```

### Step 4: Cache Transcription Results for Fast Iteration

```typescript
// src/assemblyai/transcribe.ts
import fs from 'fs';
import path from 'path';
import { getClient } from './client';
import type { Transcript } from 'assemblyai';

const CACHE_DIR = path.join(process.cwd(), '.assemblyai-cache');

export async function transcribeWithCache(
  audioUrl: string,
  options: Record<string, any> = {}
): Promise<Transcript> {
  const cacheKey = Buffer.from(audioUrl + JSON.stringify(options))
    .toString('base64url')
    .slice(0, 32);
  const cachePath = path.join(CACHE_DIR, `${cacheKey}.json`);

  // Return cached result in dev
  if (process.env.NODE_ENV !== 'production' && fs.existsSync(cachePath)) {
    console.log('[dev] Using cached transcript:', cacheKey);
    return JSON.parse(fs.readFileSync(cachePath, 'utf-8'));
  }

  const client = getClient();
  const transcript = await client.transcripts.transcribe({
    audio: audioUrl,
    ...options,
  });

  // Cache for next run
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  fs.writeFileSync(cachePath, JSON.stringify(transcript, null, 2));
  console.log('[dev] Cached transcript:', cacheKey);

  return transcript;
}
```

### Step 5: Test with Mocked Responses

```typescript
// tests/transcribe.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AssemblyAI } from 'assemblyai';

// Mock the assemblyai module
vi.mock('assemblyai', () => ({
  AssemblyAI: vi.fn().mockImplementation(() => ({
    transcripts: {
      transcribe: vi.fn().mockResolvedValue({
        id: 'test-transcript-id',
        status: 'completed',
        text: 'This is a test transcript.',
        audio_duration: 30,
        words: [
          { text: 'This', start: 0, end: 200, confidence: 0.99 },
          { text: 'is', start: 210, end: 350, confidence: 0.98 },
        ],
      }),
      get: vi.fn(),
      list: vi.fn(),
    },
    lemur: {
      task: vi.fn().mockResolvedValue({
        request_id: 'test-lemur-id',
        response: 'Test summary of the audio.',
      }),
    },
  })),
}));

describe('Transcription', () => {
  it('should transcribe audio and return text', async () => {
    const client = new AssemblyAI({ apiKey: 'test-key' });
    const result = await client.transcripts.transcribe({
      audio: 'https://example.com/audio.wav',
    });

    expect(result.status).toBe('completed');
    expect(result.text).toContain('test transcript');
    expect(result.words).toHaveLength(2);
  });

  it('should run LeMUR task on transcript', async () => {
    const client = new AssemblyAI({ apiKey: 'test-key' });
    const { response } = await client.lemur.task({
      transcript_ids: ['test-transcript-id'],
      prompt: 'Summarize this.',
    });

    expect(response).toContain('summary');
  });
});
```

## Output
- Hot-reloading dev server with `tsx watch`
- Cached transcription results to avoid repeated API calls during dev
- Mocked test suite that runs without API credentials
- Environment variable management with `.env.local`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `ASSEMBLYAI_API_KEY not set` | Missing env file | Copy `.env.example` to `.env.local` |
| `Module not found: assemblyai` | Missing dependency | Run `npm install assemblyai` |
| Stale cache results | Outdated cache | Delete `.assemblyai-cache/` directory |
| Test timeout | Slow mock setup | Ensure mocks resolve synchronously |

## Resources
- [AssemblyAI Node SDK](https://github.com/AssemblyAI/assemblyai-node-sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)

## Next Steps
See `assemblyai-sdk-patterns` for production-ready code patterns.
