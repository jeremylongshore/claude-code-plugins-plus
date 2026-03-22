# Groq Skill Pack

> 24 Claude Code skills for Groq's ultra-fast LPU inference API -- real SDK code, real model IDs, real speed benchmarks.

## What This Covers

Groq provides the fastest LLM inference available through custom LPU (Language Processing Unit) hardware. This skill pack covers the `groq-sdk` npm package, the OpenAI-compatible REST API at `api.groq.com/openai/v1/`, and all current model families: Llama 3.x text, Llama 4 vision, Whisper audio, and text-to-speech.

**Key model IDs used throughout:**
- `llama-3.1-8b-instant` -- fastest, cheapest (~560 tok/s, $0.05/M tokens)
- `llama-3.3-70b-versatile` -- best quality (~280 tok/s, $0.59/M tokens)
- `llama-3.3-70b-specdec` -- speculative decoding variant
- `meta-llama/llama-4-scout-17b-16e-instruct` -- multimodal vision
- `whisper-large-v3-turbo` -- audio transcription at 216x real-time

## Installation

```bash
/plugin install groq-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `groq-install-auth` | Install `groq-sdk`, configure `GROQ_API_KEY`, verify connection |
| `groq-hello-world` | First chat completion, streaming, model selection |
| `groq-local-dev-loop` | Project setup, vitest mocking, integration tests |
| `groq-sdk-patterns` | Typed client, error handling with `Groq.APIError`, retry logic |
| `groq-core-workflow-a` | Chat completions, tool/function calling, JSON mode, structured outputs |
| `groq-core-workflow-b` | Whisper transcription, Llama 4 vision, text-to-speech, benchmarking |
| `groq-common-errors` | Error code reference (401, 429, 400, 500), rate limit headers |
| `groq-debug-bundle` | Diagnostic script: env, connectivity, rate limits, latency |
| `groq-rate-limits` | Header parsing, exponential backoff, `p-queue`, proactive throttling |
| `groq-security-basics` | Key rotation, git leak prevention, prompt injection defense |
| `groq-prod-checklist` | Go-live checklist: auth, fallback, health check, spending limits |
| `groq-upgrade-migration` | SDK upgrades, deprecated model scanner, model ID migration map |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `groq-ci-integration` | GitHub Actions: unit tests, integration tests, model deprecation checks |
| `groq-deploy-integration` | Vercel Edge, Cloud Run, Docker, Vercel AI SDK integration |
| `groq-webhooks-events` | SSE streaming, BullMQ batch processing, webhook event processor |
| `groq-performance-tuning` | Model speed tiers, prompt cache, parallel orchestration, benchmarking |
| `groq-cost-tuning` | Smart model routing (12x savings), batching, caching, usage tracking |
| `groq-reference-architecture` | Model registry, router, middleware, fallback chain, streaming pipeline |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `groq-multi-env-setup` | Dev/staging/prod config, secret management, Docker Compose |
| `groq-observability` | Prometheus metrics, rate limit gauges, alert rules, structured logging |
| `groq-incident-runbook` | Triage script, decision tree, fallback activation, postmortem template |
| `groq-data-handling` | PII redaction, response filtering, audit logging, Llama Guard moderation |
| `groq-enterprise-rbac` | Team access control, spending limits, API gateway, key rotation |
| `groq-migration-deep-dive` | OpenAI-to-Groq migration, provider abstraction, traffic shifting |

## Usage

Skills trigger automatically when you discuss Groq topics:

- "Help me set up Groq" triggers `groq-install-auth`
- "Groq 429 error" triggers `groq-common-errors`
- "Transcribe audio with Groq" triggers `groq-core-workflow-b`
- "Deploy my Groq app to Vercel" triggers `groq-deploy-integration`
- "Migrate from OpenAI to Groq" triggers `groq-migration-deep-dive`

## Key Links

- [Groq Console](https://console.groq.com)
- [Groq API Docs](https://console.groq.com/docs)
- [Groq Models](https://console.groq.com/docs/models)
- [groq-sdk on npm](https://www.npmjs.com/package/groq-sdk)
- [Groq Status](https://status.groq.com)

## License

MIT
