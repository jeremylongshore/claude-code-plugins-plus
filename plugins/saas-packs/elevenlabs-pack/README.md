# ElevenLabs Skill Pack

> 18 Claude Code skills for ElevenLabs text-to-speech, voice cloning, speech-to-speech, sound effects, audio isolation, and real-time WebSocket streaming.

**Install:**
```bash
/plugin install elevenlabs-pack@claude-code-plugins-plus
```

## What It Covers

Real ElevenLabs API integration — every skill uses actual endpoints (`api.elevenlabs.io/v1/*`), real model IDs (`eleven_v3`, `eleven_multilingual_v2`, `eleven_flash_v2_5`), real voice settings (`stability`, `similarity_boost`, `style`, `speed`), and real error codes (401 quota, 429 concurrency, 400 validation). Both `@elevenlabs/elevenlabs-js` (TypeScript) and `elevenlabs` (Python) SDK patterns.

## Skills (18)

### Standard (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `elevenlabs-install-auth` | Install SDK, configure `xi-api-key`, verify connection |
| `elevenlabs-hello-world` | First TTS generation with voice selection and output formats |
| `elevenlabs-local-dev-loop` | Dev environment with SDK mocking and quota protection |
| `elevenlabs-sdk-patterns` | Singleton client, error classification, retry queue, multi-tenant |
| `elevenlabs-core-workflow-a` | TTS, instant voice cloning (IVC), WebSocket streaming |
| `elevenlabs-core-workflow-b` | Speech-to-speech, sound effects, audio isolation, transcription |
| `elevenlabs-common-errors` | Error reference by HTTP status (400/401/404/422/429/5xx) |
| `elevenlabs-debug-bundle` | Diagnostic collection script for support tickets |
| `elevenlabs-rate-limits` | Plan-aware concurrency queuing, backoff, quota monitoring |
| `elevenlabs-security-basics` | API key management, HMAC webhook verification, voice data protection |
| `elevenlabs-prod-checklist` | Health checks, circuit breaker, monitoring, pre-flight script |
| `elevenlabs-upgrade-migration` | SDK package rename, model generation migration, rollback |

### Pro (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `elevenlabs-ci-integration` | Two-tier CI: mocked unit tests + gated integration tests |
| `elevenlabs-deploy-integration` | Deploy to Vercel, Fly.io, Cloud Run with streaming support |
| `elevenlabs-webhooks-events` | HMAC signature verification, event routing, idempotency |
| `elevenlabs-performance-tuning` | Model selection, streaming TTFB, WebSocket, audio caching |
| `elevenlabs-cost-tuning` | Character-efficient patterns, quota monitoring, budget alerts |
| `elevenlabs-reference-architecture` | Production project structure, service layers, data flow |

## API Coverage

| ElevenLabs Feature | Endpoint | Skills |
|-------------------|----------|--------|
| Text-to-Speech | `POST /v1/text-to-speech/{voice_id}` | hello-world, core-workflow-a |
| TTS Streaming | `POST /v1/text-to-speech/{voice_id}/stream` | core-workflow-a, performance-tuning |
| WebSocket TTS | `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input` | core-workflow-a, performance-tuning |
| Voice Cloning | `POST /v1/voices/add` | core-workflow-a |
| Voice Management | `GET /v1/voices`, `GET/PUT /v1/voices/{voice_id}/settings` | core-workflow-a, reference-architecture |
| Speech-to-Speech | `POST /v1/speech-to-speech/{voice_id}` | core-workflow-b |
| Sound Effects | `POST /v1/sound-generation` | core-workflow-b |
| Audio Isolation | `POST /v1/audio-isolation` | core-workflow-b |
| Speech-to-Text | `POST /v1/speech-to-text` | core-workflow-b |
| User/Quota | `GET /v1/user` | install-auth, cost-tuning, rate-limits |
| Models | `GET /v1/models` | upgrade-migration, debug-bundle |
| Webhooks | HMAC `ElevenLabs-Signature` header | webhooks-events, security-basics |

## Models Quick Reference

| Model ID | Quality | Latency | Cost/Char | WebSocket |
|----------|---------|---------|-----------|-----------|
| `eleven_v3` | Highest | ~500ms | 1.0x | No |
| `eleven_multilingual_v2` | High | ~300ms | 1.0x | Yes |
| `eleven_flash_v2_5` | Good | ~75ms | 0.5x | Yes |
| `eleven_turbo_v2_5` | Good | ~150ms | 0.5x | Yes |

## License

MIT
