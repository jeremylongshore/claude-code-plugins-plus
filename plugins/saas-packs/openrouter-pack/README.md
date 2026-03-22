# OpenRouter Skill Pack

> Flagship+ tier: 30 production-grade skills for OpenRouter LLM gateway mastery

## Overview

Complete Claude Code skill pack for [OpenRouter](https://openrouter.ai) -- the unified API for 300+ LLM models from OpenAI, Anthropic, Google, Meta, Mistral, and more. Every skill contains real API calls to `https://openrouter.ai/api/v1`, real model IDs, real provider routing, and real cost/credit management code.

## Installation

```bash
# Via Claude Code
/plugin install openrouter-pack@claude-code-plugins-plus
```

## What's Covered

- **OpenAI SDK compatibility** -- change `base_url` and `api_key`, everything works
- **Real model IDs** -- `anthropic/claude-3.5-sonnet`, `openai/gpt-4o`, `google/gemini-2.0-flash-001`, etc.
- **Provider routing** -- `provider.order`, `allow_fallbacks`, `:floor` variant
- **Native fallbacks** -- `models` array with `route: "fallback"`
- **Credit system** -- `/api/v1/auth/key`, `/api/v1/generation?id=`, management keys
- **Production patterns** -- streaming, tool calling, caching, rate limiting, error handling

## Skills Included (30)

### Onboarding & Foundations (6)
| Skill | Description |
|-------|-------------|
| `openrouter-install-auth` | API key setup, environment config, key rotation |
| `openrouter-hello-world` | First request in Python/TypeScript/curl |
| `openrouter-model-catalog` | Query `/api/v1/models`, filter by capability and price |
| `openrouter-sdk-patterns` | Production client wrappers with retries and middleware |
| `openrouter-openai-compat` | Drop-in OpenAI SDK compatibility, transforms, migration |
| `openrouter-pricing-basics` | Token pricing, cost calculation, `:floor` variants |

### Operations & Debugging (6)
| Skill | Description |
|-------|-------------|
| `openrouter-common-errors` | Every error code (401/402/429/5xx) with exact fixes |
| `openrouter-debug-bundle` | Generation metadata, debug scripts, diagnostic bundles |
| `openrouter-rate-limits` | Rate limit tiers, headers, client-side token bucket |
| `openrouter-model-availability` | Health probes, catalog checks, availability monitoring |
| `openrouter-prod-checklist` | Security/reliability/observability validation script |
| `openrouter-upgrade-migration` | Migration from direct APIs, feature flags, comparison tests |

### Routing & Reliability (6)
| Skill | Description |
|-------|-------------|
| `openrouter-fallback-config` | Native model fallback, provider fallback, client-side chains |
| `openrouter-routing-rules` | Rules engine for model selection by user tier/task/budget |
| `openrouter-streaming-setup` | SSE streaming in Python/TypeScript, browser forwarding |
| `openrouter-caching-strategy` | In-memory/Redis caching, Anthropic prompt caching |
| `openrouter-load-balancing` | Multi-key rotation, circuit breakers, concurrent requests |
| `openrouter-reference-architecture` | Simple/standard/enterprise architecture patterns |

### Enterprise & Compliance (6)
| Skill | Description |
|-------|-------------|
| `openrouter-team-setup` | Management API key provisioning, per-user budgets |
| `openrouter-cost-controls` | Credit limits, budget middleware, cost-saving variants |
| `openrouter-usage-analytics` | Analytics DB, cost reports, weekly summaries |
| `openrouter-data-privacy` | PII redaction, placeholder substitution, provider selection |
| `openrouter-audit-logging` | Generation metadata logging, audit queries, PII scrubbing |
| `openrouter-compliance-review` | SOC2/GDPR checklist, BYOK, data classification |

### Advanced Patterns (6)
| Skill | Description |
|-------|-------------|
| `openrouter-model-routing` | Task-based routing, complexity classification, cost-aware selection |
| `openrouter-function-calling` | Tool definitions, multi-turn tool loop, JSON mode |
| `openrouter-context-optimization` | Context-aware model selection, trimming, chunking |
| `openrouter-multi-provider` | Cross-provider comparison, BYOK, feature normalization |
| `openrouter-performance-tuning` | Latency benchmarking, streaming metrics, connection pooling |
| `openrouter-known-pitfalls` | 10 real-world mistakes with code-level fixes |

## Quick Start

After installation, these skills activate automatically when you:
- Set up OpenRouter API integration
- Configure model fallbacks and provider routing
- Optimize LLM costs and manage credits
- Debug API requests and handle errors
- Implement streaming, tool calling, or caching

## Key API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/chat/completions` | Send completion requests (OpenAI-compatible) |
| `GET /api/v1/models` | List all available models with pricing |
| `GET /api/v1/auth/key` | Check credit balance and rate limits |
| `GET /api/v1/generation?id=` | Get exact cost and metadata for a request |
| `POST /api/v1/keys` | Provision API keys (management key required) |

## Links

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter API Reference](https://openrouter.ai/docs/api/reference/overview)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter Status](https://status.openrouter.ai)
- [Tons of Skills Marketplace](https://tonsofskills.com)

## License

MIT
