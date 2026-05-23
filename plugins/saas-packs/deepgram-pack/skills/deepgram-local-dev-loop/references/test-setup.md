# Deepgram Local Dev Loop Test Setup

## TypeScript Dev Entry Point

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

## Test Setup with Vitest

```typescript
// tests/transcribe.test.ts
import { describe, it, expect } from 'vitest';
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

## Mock Responses for Offline Testing

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

## Alternative Test Frameworks

- **Jest**: Replace `vitest` imports with `jest` equivalents; mock `@deepgram/sdk` using `jest.mock()`
- **Mocha + Chai**: Use `describe/it` from mocha with `expect` from chai
- **Node built-in test runner**: Use `node:test` module for zero-dependency testing
