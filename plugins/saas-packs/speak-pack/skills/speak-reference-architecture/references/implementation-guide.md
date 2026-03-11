# Speak Reference Architecture - Implementation Guide

Detailed implementation reference for the speak-reference-architecture skill.

## Project Structure

```
my-speak-app/
├── src/
│   ├── speak/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── lessons/
│   │   ├── session.ts          # Session management
│   │   ├── conversation.ts     # Conversation practice
│   │   ├── pronunciation.ts    # Pronunciation training
│   │   └── vocabulary.ts       # Vocabulary exercises
│   ├── speech/
│   │   ├── recognizer.ts       # Speech recognition wrapper
│   │   ├── scorer.ts           # Pronunciation scoring
│   │   └── audio.ts            # Audio processing utilities
│   ├── progress/
│   │   ├── tracker.ts          # Progress tracking
│   │   ├── streaks.ts          # Streak management
│   │   └── achievements.ts     # Gamification
│   ├── services/
│   │   └── speak/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── speak/
│   │       ├── lessons.ts      # Lesson endpoints
│   │       ├── progress.ts     # Progress endpoints
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── speak/
│           ├── sync.ts         # Background sync job
│           └── notifications.ts # Reminder notifications
├── tests/
│   ├── unit/
│   │   └── speak/
│   ├── integration/
│   │   └── speak/
│   └── fixtures/
│       └── audio/              # Test audio files
├── config/
│   ├── speak.development.json
│   ├── speak.staging.json
│   └── speak.production.json
└── docs/
    └── speak/
        ├── SETUP.md
        └── RUNBOOK.md
```


## Layer Architecture

```
┌─────────────────────────────────────────┐
│             API Layer                    │
│   (Controllers, Routes, Webhooks)        │
├─────────────────────────────────────────┤
│           Lesson Layer                   │
│  (Conversation, Pronunciation, Vocab)    │
├─────────────────────────────────────────┤
│          Speech Layer                    │
│   (Recognition, Scoring, Audio)          │
├─────────────────────────────────────────┤
│          Speak SDK Layer                 │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Storage, Monitoring)   │
└─────────────────────────────────────────┘
```


## Key Components

### Step 1: Client Wrapper
```typescript
// src/speak/client.ts
import { SpeakClient as SDKClient } from '@speak/language-sdk';

export class SpeakService {
  private client: SDKClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SpeakConfig) {
    this.client = new SDKClient({
      apiKey: config.apiKey,
      appId: config.appId,
    });
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('speak');
  }

  get tutor() {
    return {
      startSession: (config: SessionConfig) =>
        this.monitor.track('tutor.startSession', () =>
          this.client.tutor.startSession(config)
        ),
      getPrompt: (sessionId: string) =>
        this.monitor.track('tutor.getPrompt', () =>
          this.client.tutor.getPrompt(sessionId)
        ),
    };
  }

  get speech() {
    return {
      recognize: (audio: ArrayBuffer) =>
        this.monitor.track('speech.recognize', () =>
          this.client.speech.recognize(audio)
        ),
      score: (audio: ArrayBuffer, text: string) =>
        this.monitor.track('speech.score', () =>
          this.client.speech.score({ audio, expectedText: text })
        ),
    };
  }

  get vocabulary() {
    return {
      lookup: (word: string, language: string) =>
        this.cache.getOrFetch(`vocab:${language}:${word}`, () =>
          this.client.vocabulary.lookup(word, language)
        ),
    };
  }
}
```

### Step 2: Error Boundary
```typescript
// src/speak/errors.ts
export class SpeakServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SpeakServiceError';
  }

  static fromSDKError(error: unknown): SpeakServiceError {
    if (error instanceof RateLimitError) {
      return new SpeakServiceError(
        'Rate limit exceeded',
        'RATE_LIMITED',
        true,
        error
      );
    }
    if (error instanceof AuthError) {
      return new SpeakServiceError(
        'Authentication failed',
        'AUTH_ERROR',
        false,
        error
      );
    }
    if (error instanceof AudioError) {
      return new SpeakServiceError(
        'Audio processing failed',
        'AUDIO_ERROR',
        true,
        error
      );
    }
    return new SpeakServiceError(
      error instanceof Error ? error.message : 'Unknown error',
      'UNKNOWN',
      true
    );
  }
}
```

### Step 3: Lesson Session Manager
```typescript
// src/lessons/session.ts
interface ActiveSession {
  id: string;
  userId: string;
  language: string;
  topic: string;
  startedAt: Date;
  exchanges: number;
}

export class LessonSessionManager {
  private sessions: Map<string, ActiveSession> = new Map();
  private speakService: SpeakService;

  constructor(speakService: SpeakService) {
    this.speakService = speakService;
  }

  async startSession(userId: string, config: LessonConfig): Promise<Session> {
    // End existing session if any
    await this.endSession(userId);

    const session = await this.speakService.tutor.startSession({
      language: config.language,
      topic: config.topic,
      difficulty: config.difficulty,
    });

    this.sessions.set(userId, {
      id: session.id,
      userId,
      language: config.language,
      topic: config.topic,
      startedAt: new Date(),
      exchanges: 0,
    });

    // Track session start
    await analytics.track('lesson_started', {
      userId,
      sessionId: session.id,
      ...config,
    });

    return session;
  }

  getActiveSession(userId: string): ActiveSession | null {
    return this.sessions.get(userId) || null;
  }

  async endSession(userId: string): Promise<SessionSummary | null> {
    const active = this.sessions.get(userId);
    if (!active) return null;

    const summary = await this.speakService.tutor.endSession(active.id);
    this.sessions.delete(userId);

    // Track session end
    await analytics.track('lesson_completed', {
      userId,
      sessionId: active.id,
      duration: Date.now() - active.startedAt.getTime(),
      exchanges: active.exchanges,
    });

    return summary;
  }
}
```

### Step 4: Health Check
```typescript
// src/speak/health.ts
interface SpeakHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latencyMs: number;
  services: {
    api: boolean;
    speech: boolean;
    tutor: boolean;
  };
}

export async function checkSpeakHealth(): Promise<SpeakHealthStatus> {
  const start = Date.now();
  const services = { api: false, speech: false, tutor: false };

  try {
    // Check API
    await speakService.health.check();
    services.api = true;

    // Check speech recognition (with minimal audio)
    services.speech = await testSpeechRecognition();

    // Check tutor availability
    services.tutor = await testTutorAvailability();

    return {
      status: Object.values(services).every(Boolean) ? 'healthy' : 'degraded',
      latencyMs: Date.now() - start,
      services,
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      latencyMs: Date.now() - start,
      services,
    };
  }
}
```


## Data Flow Diagram

```
User Interaction
     │
     ▼
┌─────────────┐
│   Web/App   │
│   Client    │
└──────┬──────┘
       │ Audio + Text
       ▼
┌─────────────┐    ┌─────────────┐
│   API       │───▶│   Cache     │
│   Gateway   │    │   (Redis)   │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│   Lesson    │───▶│   Audio     │
│   Service   │    │   Storage   │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│   Speak     │
│   SDK       │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Speak     │
│   API       │
└─────────────┘
```


## Configuration Management

```typescript
// config/speak.ts
export interface SpeakConfig {
  apiKey: string;
  appId: string;
  environment: 'development' | 'staging' | 'production';
  defaultLanguage: string;
  supportedLanguages: string[];
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
  audio: {
    maxDuration: number;
    format: 'wav' | 'mp3';
    sampleRate: number;
  };
}

export function loadSpeakConfig(): SpeakConfig {
  const env = process.env.NODE_ENV || 'development';
  const baseConfig = require('./speak.base.json');
  const envConfig = require(`./speak.${env}.json`);

  return {
    ...baseConfig,
    ...envConfig,
    apiKey: process.env.SPEAK_API_KEY!,
    appId: process.env.SPEAK_APP_ID!,
    environment: env as SpeakConfig['environment'],
  };
}
```


## Flagship Skills
For multi-environment setup, see `speak-multi-env-setup`.
