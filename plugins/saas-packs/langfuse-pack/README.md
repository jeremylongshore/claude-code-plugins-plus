# Langfuse Skill Pack

> Claude Code skill pack for [Langfuse](https://langfuse.com) LLM observability -- 24 skills covering tracing, evaluation, prompt management, and production operations.

## What is Langfuse?

Langfuse is an open-source LLM engineering platform providing:

- **Tracing**: End-to-end observability for LLM calls, chains, and agents (OpenTelemetry-based in SDK v4+)
- **Evaluation**: Score outputs with user feedback, automated evals, LLM-as-a-Judge, and dataset experiments
- **Prompt Management**: Version, deploy, and A/B test prompts with labels and variables
- **Analytics**: Monitor costs, latency, and token usage with built-in and custom dashboards
- **Datasets**: Create test sets, run experiments, and track quality regressions
- **Self-hosted or Cloud**: Deploy anywhere or use managed cloud at [cloud.langfuse.com](https://cloud.langfuse.com)

## Installation

```bash
/plugin install langfuse-pack@claude-code-plugins-plus
```

## SDK Coverage

All skills cover both SDK versions:

| SDK | Packages | Status |
|-----|----------|--------|
| v3 (legacy) | `langfuse` | Maintenance mode |
| v4+/v5 (current) | `@langfuse/client`, `@langfuse/tracing`, `@langfuse/otel`, `@langfuse/openai` | Recommended |

## Skills (24)

### Getting Started (S01-S04)
| Skill | What It Does |
|-------|-------------|
| `langfuse-install-auth` | Install SDK (v3 or v4+), configure API keys, verify connection |
| `langfuse-hello-world` | First trace with `startActiveObservation`, `observe` wrapper, and v3 legacy |
| `langfuse-local-dev-loop` | Hot reload dev workflow, immediate trace flush, optional self-hosted Docker |
| `langfuse-sdk-patterns` | Singleton client, `observe` wrapper, `startActiveObservation`, error-safe tracing |

### Core Workflows (S05-S06)
| Skill | What It Does |
|-------|-------------|
| `langfuse-core-workflow-a` | Trace LLM calls: OpenAI drop-in wrapper, RAG pipelines, streaming, Anthropic, LangChain |
| `langfuse-core-workflow-b` | Evaluation: scores (numeric/categorical/boolean), prompt management, datasets, experiment runner, LLM-as-a-Judge |

### Troubleshooting (S07-S10)
| Skill | What It Does |
|-------|-------------|
| `langfuse-common-errors` | Top 10 errors (401, missing traces, 429, import errors) with tested solutions |
| `langfuse-debug-bundle` | Collect diagnostic bundle (env, SDK version, connectivity, redacted logs) |
| `langfuse-rate-limits` | Batching optimization, exponential backoff, p-queue concurrency, sampling |
| `langfuse-security-basics` | Credential validation, PII scrubbing, self-hosted hardening, secret scanning |

### Production (S11-S12)
| Skill | What It Does |
|-------|-------------|
| `langfuse-prod-checklist` | Production config, shutdown handlers, pre-deploy verification script, full checklist |
| `langfuse-upgrade-migration` | v3 to v4 migration: import changes, tracing API, env vars, prompt API, codemods |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `langfuse-ci-integration` | GitHub Actions, prompt regression tests, experiment quality gates, prompt deployment |
| `langfuse-deploy-integration` | Deploy with Vercel/Lambda/Cloud Run/Docker, self-hosted server, health checks |
| `langfuse-webhooks-events` | Prompt change webhooks (HMAC verified), Slack alerts, CI/CD triggers |
| `langfuse-performance-tuning` | Benchmarking, batch tuning, payload truncation, sampling, memory management |
| `langfuse-cost-tuning` | Token/cost tracking, Metrics API queries, smart model routing, budget alerts |
| `langfuse-reference-architecture` | Singleton + OTel, context propagation, cross-service tracing, multi-env, circuit breaker |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `langfuse-multi-env-setup` | Dev/staging/prod config, secret management (AWS/GCP/Vault), CI/CD integration, Zod validation |
| `langfuse-observability` | Prometheus metrics, Grafana dashboards, alert rules, Langfuse Metrics API |
| `langfuse-incident-runbook` | Triage script, severity classification, fallback mode, resolution procedures, post-mortem |
| `langfuse-data-handling` | Data export (traces/scores/datasets), GDPR requests, anonymization, retention policies |
| `langfuse-enterprise-rbac` | Roles/permissions, scoped API keys, SSO/SAML, self-hosted hardening, audit logging |
| `langfuse-migration-deep-dive` | Cross-instance migration, data export/import, dual-write zero-downtime, validation |

## Usage

Skills trigger automatically when you discuss Langfuse topics:

- "Help me set up Langfuse" -> `langfuse-install-auth`
- "Add tracing to my OpenAI calls" -> `langfuse-core-workflow-a`
- "Set up evaluation for my LLM app" -> `langfuse-core-workflow-b`
- "Debug this Langfuse error" -> `langfuse-common-errors`
- "Track LLM costs with Langfuse" -> `langfuse-cost-tuning`
- "Migrate from langfuse v3 to v4" -> `langfuse-upgrade-migration`

## License

MIT
