# Deepgram Skill Pack

> Speech-to-text, text-to-speech, and audio intelligence for Claude Code. 24 skills covering the full Deepgram platform: Nova-3/Nova-2 transcription, Aura-2 TTS, live streaming WebSocket, diarization, summarization, and enterprise deployment.

**SDK:** `@deepgram/sdk` (TypeScript) / `deepgram-sdk` (Python)
**API:** `createClient()` (v3/v4) or `new DeepgramClient()` (v5)
**Models:** Nova-3 (best accuracy), Nova-2 (proven), Base (fastest), Whisper (multilingual)

## Installation

```bash
/plugin install deepgram-pack@claude-code-plugins-plus
```

## Skills

### Standard (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `deepgram-install-auth` | Install SDK, configure API key, verify connection with `getProjects()` |
| S02 | `deepgram-hello-world` | Transcribe audio URL in 5 lines — `transcribeUrl` with Nova-3 |
| S03 | `deepgram-local-dev-loop` | Test fixtures, Vitest mocks, watch mode, integration tests |
| S04 | `deepgram-sdk-patterns` | Singleton client, TTS with Aura-2, audio intelligence pipeline, Python patterns |
| S05 | `deepgram-core-workflow-a` | Pre-recorded STT: file/URL transcription, diarization, batch with p-limit, callbacks |
| S06 | `deepgram-core-workflow-b` | Live streaming: WebSocket, Sox mic capture, interim results, auto-reconnect, SSE |
| S07 | `deepgram-common-errors` | HTTP error reference, WebSocket debugging, audio format validation, retry patterns |
| S08 | `deepgram-debug-bundle` | Collect env/connectivity/audio diagnostics into sanitized support bundle |
| S09 | `deepgram-rate-limits` | Concurrency-based limiting with p-limit, exponential backoff, circuit breaker |
| S10 | `deepgram-security-basics` | Scoped keys, PII redaction (`redact`), temp keys for browsers, SSRF prevention |
| S11 | `deepgram-prod-checklist` | Health check, Prometheus metrics, AlertManager rules, go-live timeline |
| S12 | `deepgram-upgrade-migration` | SDK v3->v5 migration map, Nova-2->Nova-3 A/B testing, validation suite |

### Pro (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `deepgram-ci-integration` | GitHub Actions workflow, integration tests, smoke test script, key rotation |
| P14 | `deepgram-deploy-integration` | Docker, Kubernetes (HPA + secrets), AWS Lambda (S3 trigger), Cloud Run |
| P15 | `deepgram-webhooks-events` | Callback URL async transcription, signature verification, Redis job tracking |
| P16 | `deepgram-performance-tuning` | ffmpeg preprocessing, model selection, streaming large files, caching |
| P17 | `deepgram-cost-tuning` | Budget guardrails, silence removal savings, usage API dashboard, feature costs |
| P18 | `deepgram-reference-architecture` | Sync REST, BullMQ queue, WebSocket proxy, hybrid router |

### Flagship (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `deepgram-multi-env-setup` | Typed config per environment, client factory, Docker profiles, K8s overlays |
| F20 | `deepgram-observability` | Prometheus metrics, OpenTelemetry tracing, Pino logging, Grafana dashboards |
| F21 | `deepgram-incident-runbook` | Automated triage script, SEV1-4 response, fallback queue, post-incident template |
| F22 | `deepgram-data-handling` | PII redaction, S3 encrypted upload, retention policies, GDPR erasure |
| F23 | `deepgram-enterprise-rbac` | 5-role model, scoped key provisioning, permission middleware, team management |
| F24 | `deepgram-migration-deep-dive` | Adapter pattern, AWS/Google/Whisper migration, traffic shifting, validation |

## Quick Start

```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

// Pre-recorded transcription
const { result } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav' },
  { model: 'nova-3', smart_format: true, diarize: true }
);
console.log(result.results.channels[0].alternatives[0].transcript);

// Text-to-speech
const response = await deepgram.speak.request(
  { text: 'Hello from Deepgram.' },
  { model: 'aura-2-thalia-en' }
);
```

## Deepgram Platform

| Product | API | Models |
|---------|-----|--------|
| Speech-to-Text | `listen.prerecorded` / `listen.live` | Nova-3, Nova-2, Base, Whisper |
| Text-to-Speech | `speak.request` | Aura-2 (thalia, asteria, orion, luna, helios) |
| Audio Intelligence | STT params | Summarize, Topics, Sentiment, Intent |
| PII Redaction | `redact: ['pci','ssn']` | Built into STT pipeline |

## License

MIT
