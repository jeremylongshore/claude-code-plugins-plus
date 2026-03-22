# AssemblyAI Skill Pack

> Claude Code skill pack for AssemblyAI speech-to-text, LeMUR, and streaming transcription (18 skills)

**What it does:** Gives Claude Code deep knowledge of the AssemblyAI API — async transcription with audio intelligence (speaker diarization, sentiment, entities, PII redaction), real-time streaming via WebSocket, and LeMUR for LLM-powered audio analysis (summarization, Q&A, action items). Every skill uses the real `assemblyai` npm package with real SDK methods.

**Links:** [AssemblyAI Docs](https://www.assemblyai.com/docs) | [Node SDK](https://github.com/AssemblyAI/assemblyai-node-sdk) | [API Reference](https://www.assemblyai.com/docs/api-reference/overview) | [Pricing](https://www.assemblyai.com/pricing)

## Installation

```bash
/plugin install assemblyai-pack@claude-code-plugins-plus
```

## Skills Included

### Getting Started (S01-S04)
| Skill | What It Does |
|-------|-------------|
| `assemblyai-install-auth` | Install `assemblyai` npm package, configure API key, verify connection |
| `assemblyai-hello-world` | First transcription — remote URL, local file, audio intelligence features, LeMUR |
| `assemblyai-local-dev-loop` | Dev environment with transcript caching, mocked tests, hot reload |
| `assemblyai-sdk-patterns` | Singleton client, type-safe wrappers, error handling, retry logic, multi-tenant |

### Core Workflows (S05-S06)
| Skill | What It Does |
|-------|-------------|
| `assemblyai-core-workflow-a` | Async transcription — speaker diarization, sentiment, entities, PII redaction, content safety |
| `assemblyai-core-workflow-b` | Streaming transcription via WebSocket + LeMUR (summarize, Q&A, action items, custom tasks) |

### Troubleshooting (S07-S09)
| Skill | What It Does |
|-------|-------------|
| `assemblyai-common-errors` | Real error messages with fixes — auth, download errors, rate limits, streaming codes, LeMUR |
| `assemblyai-debug-bundle` | Diagnostic script + programmatic transcript inspection for support tickets |
| `assemblyai-rate-limits` | Exponential backoff, p-queue concurrency control, streaming reconnection |

### Security & Production (S10-S12)
| Skill | What It Does |
|-------|-------------|
| `assemblyai-security-basics` | API key management, temporary tokens for browsers, PII redaction, data retention |
| `assemblyai-prod-checklist` | Go-live checklist, webhook-based processing, health checks, monitoring alerts |
| `assemblyai-upgrade-migration` | SDK migration (old `@assemblyai/sdk` to `assemblyai`), model transitions, breaking changes |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `assemblyai-ci-integration` | GitHub Actions with mocked unit tests + live integration tests, cost-controlled strategy |
| `assemblyai-deploy-integration` | Deploy to Vercel, Cloud Run, Fly.io with webhook endpoints and streaming tokens |
| `assemblyai-webhooks-events` | Webhook handler for transcription completion, idempotent processing, local testing |
| `assemblyai-performance-tuning` | Model selection (Best vs Nano), batch processing, caching, webhook vs polling |
| `assemblyai-cost-tuning` | Real pricing calculator, feature budgeting, usage tracking, cost reduction strategies |
| `assemblyai-reference-architecture` | Layered architecture with transcription, LeMUR, and streaming services |

## Key SDK Patterns Used

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({ apiKey: process.env.ASSEMBLYAI_API_KEY! });

// Async transcription (polls until done)
const transcript = await client.transcripts.transcribe({ audio: './file.mp3' });

// Submit with webhook (returns immediately)
await client.transcripts.submit({ audio: url, webhook_url: '...' });

// Streaming via WebSocket
const transcriber = client.streaming.createService({ speech_model: 'nova-3' });

// LeMUR — LLM on transcripts
await client.lemur.summary({ transcript_ids: [id] });
await client.lemur.questionAnswer({ transcript_ids: [id], questions: [...] });
await client.lemur.actionItems({ transcript_ids: [id] });
await client.lemur.task({ transcript_ids: [id], prompt: '...' });
```

## License

MIT
