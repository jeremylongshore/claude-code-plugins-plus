# TwinMind Reference Architecture - Detailed Implementation

## Project Structure

```
my-twinmind-project/
├── src/
│   ├── twinmind/           # TwinMind layer
│   │   ├── client.ts       # Singleton client wrapper
│   │   ├── config.ts       # Environment configuration
│   │   ├── types.ts        # TypeScript types
│   │   ├── errors.ts       # Custom error classes
│   │   └── handlers/       # Webhook/event handlers
│   ├── services/meeting/   # Service layer
│   │   ├── index.ts        # Orchestration facade
│   │   ├── transcription.ts
│   │   ├── summary.ts
│   │   ├── actions.ts
│   │   └── cache.ts
│   ├── integrations/       # Integration layer
│   │   ├── calendar/
│   │   ├── slack/
│   │   ├── linear/
│   │   └── email/
│   ├── api/                # API layer
│   │   ├── routes/
│   │   └── middleware/
│   ├── jobs/               # Background jobs
│   └── utils/              # Utilities
├── tests/
├── config/
└── docs/
```

## Layer Architecture

```
API Layer (Controllers, Routes, Webhooks)
   ↓
Service Layer (Business Logic, Orchestration)
   ↓
TwinMind Layer (Client, Types, Error Handling)
   ↓
Integration Layer (Calendar, Slack, Linear, Email)
   ↓
Infrastructure Layer (Cache, Queue, Monitoring)
```

## Client Wrapper

```typescript
import axios, { AxiosInstance } from 'axios';

export class TwinMindService {
  private client: AxiosInstance;
  private cache: TranscriptCache;
  private metrics: MetricsCollector;

  constructor(config?: TwinMindConfig) {
    this.config = config || loadConfig();
    this.client = axios.create({
      baseURL: this.config.baseUrl,
      headers: { 'Authorization': `Bearer ${this.config.apiKey}`, 'Content-Type': 'application/json' },
      timeout: this.config.timeout,
    });
    this.cache = new TranscriptCache(this.config.cacheOptions);
    this.metrics = new MetricsCollector('twinmind');
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use((config) => { this.metrics.incrementCounter('requests', { method: config.method }); return config; });
    this.client.interceptors.response.use(
      (response) => { this.metrics.recordLatency('request_duration', response.config.metadata?.startTime); return response; },
      (error) => { this.metrics.incrementCounter('errors', { status: error.response?.status || 'network' }); throw error; }
    );
  }

  async transcribe(audioUrl: string, options?: TranscriptionOptions): Promise<Transcript> {
    return this.cache.getOrFetch(`transcript:${audioUrl}`, () => this.metrics.track('transcribe', () => this.client.post('/transcribe', { audio_url: audioUrl, ...options })));
  }
}

let instance: TwinMindService | null = null;
export function getTwinMindService(): TwinMindService {
  if (!instance) instance = new TwinMindService();
  return instance;
}
```

## Service Layer

```typescript
export class MeetingService {
  private twinmind = getTwinMindService();

  async processMeeting(audioUrl: string, options = {}): Promise<MeetingResult> {
    const calendarEvent = options.calendarEventId ? await this.calendar.getEvent(options.calendarEventId) : null;
    const transcript = await this.transcription.transcribe(audioUrl, { title: calendarEvent?.title, attendees: calendarEvent?.attendees });

    const [summary, actionItems] = await Promise.all([
      this.summaryService.generate(transcript.id),
      this.actionService.extract(transcript.id),
    ]);

    const participants = await this.identifyParticipants(transcript, calendarEvent?.attendees);

    if (options.notifySlack) {
      await this.slack.notifyMeetingComplete({ title: transcript.title, summary: summary.summary, actionItems });
    }

    return { transcriptId: transcript.id, transcript, summary, actionItems, participants };
  }
}
```

## Error Boundary

```typescript
export class TwinMindError extends Error {
  constructor(message: string, public readonly code: string, public readonly statusCode?: number, public readonly retryable = false) {
    super(message);
    this.name = 'TwinMindError';
  }

  static fromApiError(error: any): TwinMindError {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message;
    switch (status) {
      case 401: return new TwinMindError(message, 'AUTH_FAILED', status, false);
      case 429: return new TwinMindError(message, 'RATE_LIMITED', status, true);
      case 500: case 502: case 503: return new TwinMindError(message, 'SERVER_ERROR', status, true);
      default: return new TwinMindError(message, 'UNKNOWN', status, false);
    }
  }
}
```

## Health Check

```typescript
export async function checkHealth(): Promise<HealthStatus> {
  const checks: HealthCheck[] = [];

  // TwinMind API
  const start = Date.now();
  try { await getTwinMindService().healthCheck(); checks.push({ name: 'twinmind_api', status: 'pass', latencyMs: Date.now() - start }); }
  catch (e: any) { checks.push({ name: 'twinmind_api', status: 'fail', latencyMs: Date.now() - start, message: e.message }); }

  // Cache + DB checks...
  const hasFailure = checks.some(c => c.status === 'fail');
  const hasWarning = checks.some(c => c.status === 'warn');
  return { status: hasFailure ? 'unhealthy' : hasWarning ? 'degraded' : 'healthy', checks, timestamp: new Date() };
}
```

## Configuration

```typescript
export function loadConfig(): TwinMindConfig {
  const env = process.env.NODE_ENV || 'development';
  const envConfig = require(`./twinmind.${env}.json`);
  return {
    apiKey: process.env.TWINMIND_API_KEY!,
    baseUrl: process.env.TWINMIND_API_URL || 'https://api.twinmind.com/v1',
    environment: env,
    timeout: parseInt(process.env.TWINMIND_TIMEOUT || '30000'),
    retries: parseInt(process.env.TWINMIND_RETRIES || '3'),
    ...envConfig,
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
