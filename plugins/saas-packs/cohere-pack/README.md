# Cohere Skill Pack

> 24 production-ready Claude Code skills for Cohere API v2 — Chat, Embed, Rerank, Classify, RAG, and tool-use agents.

## What This Covers

Every skill uses **real Cohere API v2 code**: `CohereClientV2` from `cohere-ai`, actual model IDs (`command-a-03-2025`, `embed-v4.0`, `rerank-v3.5`), real streaming events (`content-delta`, `citation-start`, `tool-call-start`), real error types (`CohereError`, `CohereTimeoutError`), and real rate limits (trial: 20 calls/min, production: 1000 calls/min).

## Installation

```bash
/plugin install cohere-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `cohere-install-auth` | Install `cohere-ai` SDK, configure `CO_API_KEY`, verify connection |
| `cohere-hello-world` | Chat, Embed, Rerank, and streaming examples in 4 copy-paste snippets |
| `cohere-local-dev-loop` | Project structure, vitest mocks, integration tests, hot reload |
| `cohere-sdk-patterns` | Singleton client, retry with backoff, streaming generator, batch embed, JSON output |
| `cohere-core-workflow-a` | Full RAG pipeline: Embed docs, search with cosine similarity, Rerank, Chat with citations |
| `cohere-core-workflow-b` | Tool-use agents: define tools, single-step calling, multi-step agent loop, streaming tools |
| `cohere-common-errors` | Every real error (400/401/429/5xx) with exact messages and fixes |
| `cohere-debug-bundle` | Diagnostic script: SDK version, endpoint connectivity, request logging |
| `cohere-rate-limits` | Trial vs production limits, exponential backoff, p-queue, proactive throttling |
| `cohere-security-basics` | Key management, PII scrubbing, safety modes, logging safety, pre-commit hooks |
| `cohere-prod-checklist` | Go-live checklist, health check endpoint, circuit breaker, canary deploy |
| `cohere-upgrade-migration` | API v1 to v2 migration: every breaking change with before/after code |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `cohere-ci-integration` | GitHub Actions with mocked unit tests + gated integration tests |
| `cohere-deploy-integration` | Deploy to Vercel (streaming SSE), Fly.io, Cloud Run with secrets |
| `cohere-webhooks-events` | SSE event types, RAG streaming with citations, connector registration |
| `cohere-performance-tuning` | Model tiering by latency, batch embed (96/call), int8 vectors, embedding cache |
| `cohere-cost-tuning` | Token-based pricing, model routing, budget tracking, rerank-before-embed |
| `cohere-reference-architecture` | Layered project layout with RAG service, agent service, tool registry |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `cohere-multi-env-setup` | Per-env model selection, secret management (AWS/GCP/Vault), env guards |
| `cohere-observability` | Prometheus metrics, OpenTelemetry traces, token tracking, alert rules |
| `cohere-incident-runbook` | Triage commands, decision tree, per-error-code remediation, postmortem template |
| `cohere-data-handling` | PII detection/redaction before API calls, safe embedding, audit logging |
| `cohere-enterprise-rbac` | Multi-team API keys, model access enforcement, per-team budget limits |
| `cohere-migration-deep-dive` | Migrate from OpenAI/Anthropic: adapter pattern, embedding re-vectorization, A/B testing |

## Key Models Referenced

| Model | ID | Use Case |
|-------|----|----------|
| Command A | `command-a-03-2025` | Best chat/generation (256K context) |
| Command R+ | `command-r-plus-08-2024` | Complex RAG (128K context) |
| Command R | `command-r-08-2024` | Cost-effective RAG (128K context) |
| Command R7B | `command-r7b-12-2024` | Fast/cheap (128K context) |
| Embed v4 | `embed-v4.0` | Latest embeddings (128K context) |
| Rerank v3.5 | `rerank-v3.5` | Search reranking (100+ languages) |

## Usage

Skills trigger automatically when you discuss Cohere topics:

- "Set up Cohere in my project" -> `cohere-install-auth`
- "Build a RAG pipeline with Cohere" -> `cohere-core-workflow-a`
- "Create a Cohere agent with tools" -> `cohere-core-workflow-b`
- "Fix this Cohere error" -> `cohere-common-errors`
- "Migrate from OpenAI to Cohere" -> `cohere-migration-deep-dive`

## License

MIT
