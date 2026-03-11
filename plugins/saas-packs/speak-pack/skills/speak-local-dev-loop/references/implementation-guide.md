# Speak Local Dev Loop - Implementation Guide

Detailed implementation reference for the speak-local-dev-loop skill.

## Instructions

### Step 1: Create Project Structure
```
my-speak-project/
├── src/
│   ├── speak/
│   │   ├── client.ts           # Speak client wrapper
│   │   ├── config.ts           # Configuration management
│   │   ├── tutor.ts            # AI tutor service
│   │   ├── speech.ts           # Speech recognition utilities
│   │   └── utils.ts            # Helper functions
│   ├── lessons/
│   │   ├── vocabulary.ts       # Vocabulary lesson logic
│   │   ├── conversation.ts     # Conversation practice
│   │   └── pronunciation.ts    # Pronunciation training
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── speak.test.ts
│   ├── integration/
│   │   └── lessons.test.ts
│   └── mocks/
│       └── speak-mock.ts       # Mock tutor responses
├── .env.local                  # Local secrets (git-ignored)
├── .env.example                # Template for team
├── .env.test                   # Test environment
└── package.json
```

### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env.local

# Create test environment
cat > .env.test << 'EOF'
SPEAK_API_KEY=test-key-for-mocks
SPEAK_APP_ID=test-app-id
SPEAK_MOCK_MODE=true
SPEAK_TARGET_LANGUAGE=es
EOF

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 3: Setup Hot Reload
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:lesson": "tsx watch src/lessons/conversation.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "vitest run tests/integration"
  }
}
```

### Step 4: Configure Testing with Mocks
```typescript
// tests/mocks/speak-mock.ts
import { vi } from 'vitest';

export const mockTutorResponse = {
  text: "Muy bien! Your pronunciation is improving.",
  audioUrl: 'https://speak.com/mock-audio.mp3',
  pronunciationScore: 85,
  grammarCorrections: [],
  suggestions: ['Try rolling your Rs more'],
};

export const mockSpeakClient = {
  health: {
    check: vi.fn().mockResolvedValue({ healthy: true }),
  },
  tutor: {
    startSession: vi.fn().mockResolvedValue({
      id: 'session-123',
      status: 'active',
    }),
    getPrompt: vi.fn().mockResolvedValue({
      text: 'Let\'s practice greetings in Spanish!',
      audioUrl: 'https://speak.com/mock-prompt.mp3',
    }),
    submitResponse: vi.fn().mockResolvedValue(mockTutorResponse),
  },
  speech: {
    recognize: vi.fn().mockResolvedValue({
      transcript: 'Hola, como estas',
      confidence: 0.92,
    }),
    score: vi.fn().mockResolvedValue({
      overall: 85,
      fluency: 82,
      accuracy: 88,
      pronunciation: 85,
    }),
  },
};

vi.mock('@speak/language-sdk', () => ({
  SpeakClient: vi.fn().mockImplementation(() => mockSpeakClient),
  AITutor: vi.fn(),
  SpeechRecognizer: vi.fn(),
}));
```

### Step 5: Write Unit Tests
```typescript
// tests/unit/speak.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mockSpeakClient } from '../mocks/speak-mock';
import { SpeakService } from '../../src/speak/client';

describe('Speak Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with API key', () => {
    const service = new SpeakService({ apiKey: 'test-key', appId: 'test-app' });
    expect(service).toBeDefined();
  });

  it('should verify health check', async () => {
    const result = await mockSpeakClient.health.check();
    expect(result.healthy).toBe(true);
  });

  it('should start a lesson session', async () => {
    const session = await mockSpeakClient.tutor.startSession({
      language: 'es',
      topic: 'greetings',
    });
    expect(session.id).toBe('session-123');
    expect(session.status).toBe('active');
  });

  it('should return pronunciation feedback', async () => {
    const feedback = await mockSpeakClient.tutor.submitResponse({
      text: 'Hola',
    });
    expect(feedback.pronunciationScore).toBeGreaterThan(0);
    expect(feedback.pronunciationScore).toBeLessThanOrEqual(100);
  });
});
```

### Step 6: Create Mock Lesson Runner
```typescript
// src/dev/mock-lesson.ts
import { SpeakClient } from '@speak/language-sdk';

const isMockMode = process.env.SPEAK_MOCK_MODE === 'true';

export async function runMockLesson() {
  if (isMockMode) {
    console.log('Running in MOCK mode');
    // Return mock responses without API calls
    return {
      prompt: 'Mock: Let\'s practice Spanish!',
      feedback: { score: 85, message: 'Mock feedback' },
    };
  }

  // Real API calls
  const client = new SpeakClient({
    apiKey: process.env.SPEAK_API_KEY!,
    appId: process.env.SPEAK_APP_ID!,
    language: 'es',
  });

  // ... real implementation
}
```


## Detailed Examples

### Mock Speech Recognition
```typescript
// tests/mocks/speech-mock.ts
export function createMockSpeechRecognizer() {
  return {
    start: vi.fn(),
    stop: vi.fn(),
    onResult: vi.fn(),
    simulateResult: (text: string, score: number) => {
      return {
        transcript: text,
        pronunciationScore: score,
        timing: {
          duration: 2500,
          words: [
            { word: 'Hola', start: 0, end: 500, score: 90 },
            { word: 'como', start: 600, end: 1000, score: 85 },
            { word: 'estas', start: 1100, end: 1600, score: 80 },
          ],
        },
      };
    },
  };
}
```

### Debug Mode with Verbose Logging
```bash
# Enable verbose logging for Speak operations
DEBUG=speak:* npm run dev

# Log only speech recognition
DEBUG=speak:speech npm run dev

# Log tutor interactions
DEBUG=speak:tutor npm run dev
```

### Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:mock": "SPEAK_MOCK_MODE=true tsx watch src/index.ts",
    "test:unit": "vitest run tests/unit",
    "test:integration": "vitest run tests/integration",
    "lesson:spanish": "tsx src/lessons/spanish-basics.ts",
    "lesson:korean": "SPEAK_TARGET_LANGUAGE=ko tsx src/lessons/korean-basics.ts"
  }
}
```

