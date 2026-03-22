# Wispr Flow Skill Pack

> 18 production-ready Claude Code skills for Wispr Flow -- real voice-to-text API code with WebSocket streaming and REST transcription.

## What This Is

A complete skill pack for integrating Wispr Flow voice dictation. Every skill contains real API code: WebSocket streaming, REST transcription, audio capture, and developer-context-aware dictation. Wispr Flow understands code, CLI commands, and technical jargon.

## Installation

```bash
/plugin install wispr-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `wispr-install-auth` | API key setup, WebSocket connection, client token generation |
| S02 | `wispr-hello-world` | REST transcription, WebSocket streaming, browser audio capture |
| S03 | `wispr-local-dev-loop` | Mock transcription, test fixtures, audio recording tools |
| S04 | `wispr-sdk-patterns` | WebSocket reconnection, audio processing, context management |
| S05 | `wispr-core-workflow-a` | Real-time dictation, partial/final results, IDE integration |
| S06 | `wispr-core-workflow-b` | Batch transcription, file processing, multi-language |
| S07 | `wispr-common-errors` | WebSocket disconnects, audio format issues, empty results |
| S08 | `wispr-debug-bundle` | Connection diagnostics, audio format validation |
| S09 | `wispr-rate-limits` | Concurrent connections, request throttling |
| S10 | `wispr-security-basics` | API key protection, client tokens, audio data privacy |
| S11 | `wispr-prod-checklist` | Audio quality, fallback strategies, health checks |
| S12 | `wispr-upgrade-migration` | API version changes, WebSocket protocol updates |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `wispr-ci-integration` | Automated transcription tests, fixture-based validation |
| P14 | `wispr-deploy-integration` | Deploy voice features to Vercel/Cloud Run |
| P15 | `wispr-webhooks-events` | Transcription completion callbacks, real-time events |
| P16 | `wispr-performance-tuning` | Audio compression, WebSocket optimization, latency |
| P17 | `wispr-cost-tuning` | Usage monitoring, audio length optimization |
| P18 | `wispr-reference-architecture` | Voice-powered app architecture, audio pipeline |

## Key Concepts

- **WebSocket**: `wss://api.wisprflow.ai/api/v1/ws` for real-time streaming
- **REST**: `POST /api/v1/transcribe` for file-based transcription
- **Audio**: 16kHz mono PCM preferred, supports WAV/MP3
- **Context**: Developer-aware -- understands code, CLI, and technical terms
- **Auth**: API key (backend) or short-lived access tokens (client)

## License

MIT
