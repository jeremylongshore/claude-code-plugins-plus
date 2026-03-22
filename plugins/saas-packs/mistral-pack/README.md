# Mistral AI Skill Pack

> 24 production-ready skills for Mistral AI integration — chat completions, embeddings, function calling, agents, batch API, vision, code generation, and enterprise operations.

**SDK:** `@mistralai/mistralai` (TypeScript, ESM-only) | `mistralai` (Python)
**API Base:** `api.mistral.ai` | **Console:** [console.mistral.ai](https://console.mistral.ai/)
**By:** [Tons of Skills](https://tonsofskills.com) / Intent Solutions

## Installation

```bash
/plugin install mistral-pack@claude-code-plugins-plus
```

## Models Reference

| Model ID | Context | Input $/M | Output $/M | Best For |
|----------|---------|-----------|------------|----------|
| `mistral-small-latest` | 256k | $0.10 | $0.30 | General purpose, fast |
| `mistral-large-latest` | 256k | $0.50 | $1.50 | Complex reasoning |
| `codestral-latest` | 256k | $0.30 | $0.90 | Code generation + FIM |
| `devstral-latest` | 256k | $0.40 | $2.00 | Agentic coding |
| `pixtral-large-latest` | 128k | $2.00 | $6.00 | Vision + text |
| `ministral-latest` | 256k | $0.10 | $0.10 | Edge, simple tasks |
| `mistral-embed` | 8k | $0.10 | — | 1024-dim embeddings |
| `mistral-moderation-latest` | — | — | — | Content moderation |
| Batch API (any model) | — | **50% off** | **50% off** | Non-realtime bulk |

## Skills (24)

### Standard (S01–S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `mistral-install-auth` | SDK installation, API key config, secret manager setup |
| S02 | `mistral-hello-world` | First chat completion, streaming, JSON mode, multi-turn |
| S03 | `mistral-local-dev-loop` | Project scaffold, hot reload, Vitest mocking, integration tests |
| S04 | `mistral-sdk-patterns` | Singleton client, structured output, retry/backoff, usage tracking |
| S05 | `mistral-core-workflow-a` | Chat completions, streaming SSE, guardrails, model selection |
| S06 | `mistral-core-workflow-b` | Embeddings (1024-dim), function calling loop, RAG pipeline |
| S07 | `mistral-common-errors` | HTTP error reference (401/429/400/5xx), circuit breaker, ESM fixes |
| S08 | `mistral-debug-bundle` | Diagnostic bundle script, debug helper, request logger |
| S09 | `mistral-rate-limits` | Token-aware limiter, Retry-After handling, model fallback |
| S10 | `mistral-security-basics` | Key management, prompt injection defense, moderation API |
| S11 | `mistral-prod-checklist` | Pre-deploy verification, health check, circuit breaker, rollout |
| S12 | `mistral-upgrade-migration` | v0.x to v1.x migration, automated transforms, model deprecations |

### Pro (P13–P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `mistral-ci-integration` | GitHub Actions workflow, prompt regression tests, cost estimation |
| P14 | `mistral-deploy-integration` | Vercel Edge, Docker, Cloud Run, self-hosted vLLM deployment |
| P15 | `mistral-webhooks-events` | Agents API, Batch API, event bus, BullMQ jobs, Python async |
| P16 | `mistral-performance-tuning` | Model selection, streaming, caching, prompt optimization, FIM |
| P17 | `mistral-cost-tuning` | Pricing calculator, smart model router, budget manager, batch savings |
| P18 | `mistral-reference-architecture` | Layered structure, Zod config, error classes, service layer, prompts |

### Flagship (F19–F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `mistral-multi-env-setup` | Per-env config, secret managers (GCP/AWS), feature flags, guards |
| F20 | `mistral-observability` | Prometheus metrics, Grafana panels, alerting rules, structured logs |
| F21 | `mistral-incident-runbook` | Triage script, decision tree, per-error mitigation, postmortem |
| F22 | `mistral-data-handling` | PII redaction, fine-tune sanitization, conversation TTL, GDPR erasure |
| F23 | `mistral-enterprise-rbac` | Workspace isolation, scoped keys, model gateway, spending limits |
| F24 | `mistral-migration-deep-dive` | OpenAI/Anthropic adapter, feature-flag rollout, A/B validation |

## Usage

Skills activate automatically based on context:

- "Set up Mistral" activates `mistral-install-auth`
- "Debug this Mistral error" activates `mistral-common-errors`
- "Deploy my Mistral app" activates `mistral-deploy-integration`
- "Migrate from OpenAI" activates `mistral-migration-deep-dive`
- "Optimize Mistral costs" activates `mistral-cost-tuning`

## Key Capabilities Covered

- **Chat Completions** — streaming, multi-turn, JSON mode, JSON Schema mode
- **Embeddings** — text + code, 1024 dimensions, batch processing
- **Function Calling** — tool definitions, execution loop, parallel calls
- **Agents API** — stateful conversations, built-in tools, handoffs
- **Batch API** — 50% cost reduction for bulk workloads
- **Vision** — image understanding with Pixtral models
- **Code Generation** — Codestral, Fill-in-the-Middle (FIM)
- **Moderation** — `mistral-moderation-latest`, custom guardrails
- **Fine-Tuning** — dataset preparation, job management
- **Self-Hosting** — vLLM deployment for data sovereignty

## License

MIT
