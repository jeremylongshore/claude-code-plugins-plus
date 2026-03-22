---
name: speak-local-dev-loop
description: |
  Configure Speak local development with mocked tutors and audio testing.
  Use when setting up a development environment, configuring test workflows,
  or building language learning features locally.
  Trigger with phrases like "speak dev setup", "speak local development",
  "speak dev environment", "develop with speak".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, speak, testing, workflow]

---
# Speak Local Dev Loop

## Overview
Set up a fast local development workflow for Speak language learning integrations. Includes mock tutor responses for offline development, audio test fixtures, and a debug mode for scoring analysis.

## Prerequisites
- Completed `speak-install-auth` setup
- Node.js 18+ with npm/pnpm
- ffmpeg installed (for audio conversion)

## Instructions

### Step 1: Project Structure
```
speak-app/
  src/
    speak/client.ts       # Speak API client
    speak/tutor.ts        # AI tutor conversation manager
    speak/pronunciation.ts # Pronunciation assessment
    speak/audio.ts        # Audio recording and preprocessing
  tests/
    mocks/                # Mock responses for offline dev
    fixtures/             # Sample audio files for testing
    unit/                 # Unit tests with mocked API
    integration/          # Integration tests (needs API key)
  .env.development        # Dev credentials
  .env.test              # Test credentials (mock mode)
```

### Step 2: Mock Tutor for Offline Development
```typescript
// tests/mocks/mock-speak-client.ts
export class MockSpeakClient {
  async startConversation(config: any) {
    return {
      id: 'mock-session-123',
      firstPrompt: {
        text: 'Hola! Bienvenido. Como te llamas?',
        audioUrl: null,
      },
    };
  }

  async sendTurn(sessionId: string, input: any) {
    return {
      tutorText: 'Muy bien! Tu pronunciacion es buena.',
      pronunciationScore: 85,
      corrections: [],
      vocabularyNotes: ['llamo = I call myself'],
    };
  }

  async assessPronunciation(config: any) {
    return {
      score: 82,
      words: [
        { text: 'Hola', score: 95, phonemes: [] },
        { text: 'como', score: 78, phonemes: [
          { symbol: 'o', score: 65, suggestion: 'Round lips more' }
        ]},
      ],
    };
  }
}
```

### Step 3: Audio Test Fixtures
```bash
# Generate test audio files using text-to-speech
# macOS:
say -v "Paulina" "Hola, como estas" -o tests/fixtures/hola-es.wav
# Linux:
espeak -v es "Hola, como estas" -w tests/fixtures/hola-es.wav

# Convert to required format
ffmpeg -i tests/fixtures/hola-es.wav -ar 16000 -ac 1 tests/fixtures/hola-es-16k.wav
```

### Step 4: Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:mock": "SPEAK_MOCK_MODE=true tsx watch src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "lesson:test": "tsx src/test-lesson.ts"
  }
}
```

### Step 5: Debug Mode
```typescript
// Enable detailed scoring output
const DEBUG = process.env.SPEAK_DEBUG === 'true';

function logAssessment(result: PronunciationResult) {
  if (!DEBUG) return;
  console.log('=== Pronunciation Debug ===');
  for (const word of result.words) {
    const flag = word.score < 70 ? 'WEAK' : 'OK';
    console.log(`  [${flag}] "${word.text}": ${word.score}/100`);
    for (const p of word.phonemes || []) {
      if (p.score < 70) {
        console.log(`    phoneme "${p.symbol}": ${p.score} - ${p.suggestion}`);
      }
    }
  }
}
```

## Output
- Project structure with client, tests, and mocks
- Mock tutor client for offline development
- Audio test fixtures generated with TTS
- Debug mode for pronunciation analysis
- Development scripts for fast iteration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| ffmpeg not found | Not installed | Install via `brew install ffmpeg` or `apt install ffmpeg` |
| Mock mode not activating | Env var not set | Check `SPEAK_MOCK_MODE=true` |
| Audio file too large | Long recording | Trim to 30 seconds max for testing |
| Test timeout | Slow API response | Use mock mode for unit tests |

## Resources
- [Vitest](https://vitest.dev/)
- [ffmpeg](https://ffmpeg.org/documentation.html)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)

## Next Steps
See `speak-sdk-patterns` for production-ready code patterns.

## Examples

**Mock-first development**: Run `npm run dev:mock` to iterate on UI and conversation flow without API calls. Switch to real API for integration testing.

**Audio quality testing**: Record samples at different quality levels and compare pronunciation scores to calibrate your recording pipeline.
