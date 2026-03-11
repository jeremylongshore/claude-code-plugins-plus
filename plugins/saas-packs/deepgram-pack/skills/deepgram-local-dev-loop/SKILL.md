---
name: deepgram-local-dev-loop
description: |
  Configure Deepgram local development workflow with testing and iteration.
  Use when setting up development environment, configuring test fixtures,
  or establishing rapid iteration patterns for Deepgram integration.
  Trigger with phrases like "deepgram local dev", "deepgram development setup",
  "deepgram test environment", "deepgram dev workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Local Dev Loop

## Overview
Set up an efficient local development workflow for Deepgram integration with fast feedback cycles.

## Prerequisites
- Completed `deepgram-install-auth` setup
- Node.js 18+ with npm/pnpm or Python 3.10+
- Sample audio files for testing
- Environment variables configured

## Instructions

### Step 1: Create Project Structure
```bash
mkdir -p src tests fixtures
touch src/transcribe.ts tests/transcribe.test.ts
```

### Step 2: Set Up Environment Files
```bash
# .env.development
DEEPGRAM_API_KEY=your-dev-api-key
DEEPGRAM_MODEL=nova-2

# .env.test
DEEPGRAM_API_KEY=your-test-api-key
DEEPGRAM_MODEL=nova-2
```

### Step 3: Create Test Fixtures
```bash
set -euo pipefail
# Download sample audio for testing
curl -o fixtures/sample.wav https://static.deepgram.com/examples/nasa-podcast.wav
```

### Step 4: Set Up Watch Mode
```json
{
  "scripts": {
    "dev": "tsx watch src/transcribe.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

## Output
- Project structure with src, tests, fixtures directories
- Environment files for development and testing
- Watch mode scripts for rapid iteration
- Sample audio fixtures for testing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Fixture Not Found | Missing audio file | Run fixture download script |
| Env Not Loaded | dotenv not configured | Install and configure dotenv |
| Watch Mode Fails | Missing tsx | Install tsx: `npm i -D tsx` |
| API Rate Limited | Too many dev requests | Use cached responses in tests |

## Examples

### TypeScript Dev Setup
```typescript
// src/transcribe.ts
import { createClient } from '@deepgram/sdk';
import { config } from 'dotenv';

config(); // Load .env

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

export async function transcribeAudio(audioPath: string) {
  const audio = await Bun.file(audioPath).arrayBuffer();

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    Buffer.from(audio),
    { model: process.env.DEEPGRAM_MODEL || 'nova-2', smart_format: true }
  );

  if (error) throw error;
  return result.results.channels[0].alternatives[0].transcript;
}

// Dev mode: run with sample
if (import.meta.main) {
  transcribeAudio('./fixtures/sample.wav').then(console.log);
}
```

### Test Setup with Vitest
```typescript
// tests/transcribe.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { transcribeAudio } from '../src/transcribe';

describe('Deepgram Transcription', () => {
  it('should transcribe audio file', async () => {
    const transcript = await transcribeAudio('./fixtures/sample.wav');
    expect(transcript).toBeDefined();
    expect(transcript.length).toBeGreaterThan(0);
  });

  it('should handle empty audio gracefully', async () => {
    await expect(transcribeAudio('./fixtures/empty.wav'))
      .rejects.toThrow();
  });
});
```

### Mock Responses for Testing
```typescript
// tests/mocks/deepgram.ts
export const mockTranscriptResponse = {
  results: {
    channels: [{
      alternatives: [{
        transcript: 'This is a test transcript.',
        confidence: 0.99,
        words: [
          { word: 'This', start: 0.0, end: 0.2, confidence: 0.99 },
          { word: 'is', start: 0.2, end: 0.3, confidence: 0.99 },
        ]
      }]
    }]
  }
};
```

## Resources
- [Deepgram SDK Reference](https://developers.deepgram.com/docs/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [dotenv Configuration](https://github.com/motdotla/dotenv)

## Next Steps
Proceed to `deepgram-sdk-patterns` for production-ready code patterns.