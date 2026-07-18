# ElevenLabs Reference Architecture — Project Layout, Data Flow & Decisions

Reference companion to `SKILL.md`. Full project tree, request data flow, and the
decision table behind each architectural choice.

## Project Structure

```
my-elevenlabs-service/
├── src/
│   ├── elevenlabs/
│   │   ├── client.ts            # Singleton client with retry config
│   │   ├── config.ts            # Environment-aware configuration
│   │   ├── models.ts            # Model selection logic
│   │   ├── errors.ts            # Error classification (see sdk-patterns)
│   │   └── types.ts             # TypeScript interfaces
│   ├── services/
│   │   ├── tts-service.ts       # Text-to-Speech orchestration
│   │   ├── voice-service.ts     # Voice management (clone, list, settings)
│   │   ├── audio-service.ts     # SFX, isolation, transcription
│   │   └── cache-service.ts     # Audio caching layer
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tts.ts           # POST /api/tts
│   │   │   ├── voices.ts        # GET/POST /api/voices
│   │   │   ├── webhooks.ts      # POST /webhooks/elevenlabs
│   │   │   └── health.ts        # GET /health
│   │   └── middleware/
│   │       ├── rate-limit.ts    # Request throttling
│   │       └── auth.ts          # Your app's auth (not ElevenLabs auth)
│   ├── queue/
│   │   ├── tts-queue.ts         # Async TTS job processing
│   │   └── workers.ts           # Queue workers
│   └── monitoring/
│       ├── metrics.ts           # Latency, error rate, quota tracking
│       └── alerts.ts            # Budget and health alerts
├── tests/
│   ├── unit/
│   │   ├── tts-service.test.ts
│   │   └── cache-service.test.ts
│   └── integration/
│       └── tts-smoke.test.ts
├── config/
│   ├── development.json
│   ├── staging.json
│   └── production.json
└── .env.example
```

## Data Flow Diagram

```
                         ┌──────────────┐
                         │   Client     │
                         │  (Browser/   │
                         │   Mobile)    │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │   API Layer  │
                         │   /api/tts   │
                         │   /api/voice │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────▼──┐ ┌─────▼─────┐ ┌──▼──────┐
             │  Cache   │ │   TTS     │ │  Voice  │
             │ Service  │ │  Service  │ │ Service │
             └──────┬───┘ └─────┬─────┘ └────────┘
                    │           │
              ┌─────▼─┐  ┌─────▼──────────┐
              │ Redis/ │  │ Concurrency    │
              │ LRU    │  │ Queue (p-queue)│
              └────────┘  └─────┬──────────┘
                                │
                         ┌──────▼───────┐
                         │  ElevenLabs  │
                         │  Client SDK  │
                         │  (singleton) │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────▼──┐ ┌─────▼─────┐ ┌──▼──────┐
             │ /v1/tts  │ │ /v1/voices│ │ /v1/sfx │
             │ REST/WS  │ │  REST     │ │  REST   │
             └──────────┘ └───────────┘ └─────────┘
                    ElevenLabs API (api.elevenlabs.io)
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Client pattern | Singleton | One connection pool, shared retry config |
| Concurrency | p-queue | Respects plan limits, prevents 429 |
| Caching | LRU (local) or Redis (distributed) | Repeated content is common in TTS |
| Long text | Sentence-boundary splitting | Preserves natural speech prosody |
| Error handling | Classification + retry | Different strategies for 429 vs 401 vs 500 |
| Model selection | Environment-based | Flash in dev (cheap), Multilingual in prod (quality) |
| Streaming | HTTP streaming + WebSocket | HTTP for simple, WS for LLM integration |
