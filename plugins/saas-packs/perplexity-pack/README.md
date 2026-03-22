# Perplexity Skill Pack

> Claude Code skill pack for Perplexity Sonar API — AI-powered search with web-grounded answers and citations (30 skills)

## What This Does

Gives Claude Code deep knowledge of the Perplexity Sonar API: the OpenAI-compatible endpoint at `api.perplexity.ai` that performs live web searches and returns cited, source-grounded answers. Skills cover the full lifecycle from first API call to production monitoring.

**API Endpoint:** `https://api.perplexity.ai/chat/completions` (OpenAI-compatible)
**Models:** `sonar` | `sonar-pro` | `sonar-reasoning-pro` | `sonar-deep-research`
**Auth:** Bearer token with `pplx-` prefixed API key
**SDK:** Standard `openai` package with custom `baseURL` (no Perplexity-specific SDK)

## Installation

```bash
/plugin install perplexity-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `perplexity-install-auth` | Configure OpenAI client with Perplexity base URL and API key |
| `perplexity-hello-world` | First search query with citation parsing and streaming |
| `perplexity-local-dev-loop` | Dev workflow with fixture-based mocking and live test gating |
| `perplexity-sdk-patterns` | Typed client wrapper, retry logic, citation formatter |
| `perplexity-core-workflow-a` | Single-query search with citations and domain filtering |
| `perplexity-core-workflow-b` | Multi-turn research sessions and batch query pipelines |
| `perplexity-common-errors` | 401/402/429/400 error reference with real error JSON |
| `perplexity-debug-bundle` | Diagnostic bundle: DNS, auth, model access, latency |
| `perplexity-rate-limits` | Exponential backoff, PQueue rate limiting, token bucket |
| `perplexity-security-basics` | API key rotation, PII query sanitization, domain restrictions |
| `perplexity-prod-checklist` | Production readiness checklist with health check and fallback |
| `perplexity-upgrade-migration` | Legacy model migration map (pplx-7b -> sonar) |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `perplexity-ci-integration` | GitHub Actions with mocked unit tests and gated live tests |
| `perplexity-deploy-integration` | Vercel edge function, Cloud Run with Redis cache, Docker |
| `perplexity-webhooks-events` | Streaming SSE, batch queue pipeline, scheduled news monitor |
| `perplexity-performance-tuning` | Model routing by complexity, query-aware cache TTL, streaming |
| `perplexity-cost-tuning` | Model routing saving 60-70%, token limits, cache, budget tracking |
| `perplexity-reference-architecture` | Search service + citation pipeline + research orchestrator |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `perplexity-multi-env-setup` | Dev/staging/prod configs with per-env model and key management |
| `perplexity-observability` | Latency, citation quality, cost tracking, Prometheus alerts |
| `perplexity-incident-runbook` | Triage script, decision tree, model fallback, postmortem template |
| `perplexity-data-handling` | Query PII sanitization, citation validation, context management |
| `perplexity-enterprise-rbac` | Per-team API keys, model policy gateway, domain restrictions |
| `perplexity-migration-deep-dive` | Migrate from Google CSE/Bing to Perplexity with adapter pattern |

### Flagship+ Skills (X25-X30)
| Skill | What It Does |
|-------|-------------|
| `perplexity-advanced-troubleshooting` | Layer diagnostics, citation stability, latency profiling |
| `perplexity-load-scale` | k6 load tests calibrated for 50 RPM, capacity calculator |
| `perplexity-reliability-patterns` | Circuit breaker, model fallback chain, stream timeout, stale cache |
| `perplexity-policy-guardrails` | Content moderation, usage quotas, citation quality scoring |
| `perplexity-architecture-variants` | Three blueprints: widget (<500/day), cached (5K), pipeline (5K+) |
| `perplexity-known-pitfalls` | 10 real anti-patterns with BAD/GOOD code comparisons |

## Quick Start

```typescript
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});

const response = await perplexity.chat.completions.create({
  model: "sonar",
  messages: [{ role: "user", content: "What are the latest AI developments?" }],
});

console.log(response.choices[0].message.content);
console.log("Sources:", (response as any).citations);
```

## Key API Parameters

| Parameter | Values | Purpose |
|-----------|--------|---------|
| `model` | `sonar`, `sonar-pro`, `sonar-reasoning-pro`, `sonar-deep-research` | Model selection |
| `search_recency_filter` | `hour`, `day`, `week`, `month` | Limit source freshness |
| `search_domain_filter` | `["python.org"]` or `["-reddit.com"]` | Allow/deny domains (max 20) |
| `return_related_questions` | `true` | Get follow-up suggestions |
| `return_images` | `true` | Get relevant images (Tier-2+) |
| `stream` | `true` | SSE streaming response |

## License

MIT
