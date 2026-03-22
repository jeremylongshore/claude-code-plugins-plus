# Exa Skill Pack

> 30 Claude Code skills for Exa neural search API integration — from first query to production RAG pipelines

**Exa** is a neural search API at `api.exa.ai` that retrieves web content using semantic similarity. Unlike traditional search engines, Exa understands query meaning and returns contextually relevant results with full text, highlights, and AI-generated summaries.

**SDK:** `exa-js` (npm) / `exa-py` (PyPI) | **Auth:** `x-api-key` header | **Rate limit:** 10 QPS default

## Installation

```bash
/plugin install exa-pack@claude-code-plugins-plus
```

## What You Get

| Tier | Skills | Focus |
|------|--------|-------|
| **Standard** (S01-S12) | Install, hello world, search, similarity, SDK patterns, errors, debug, rate limits, security, dev loop, checklist, upgrades | Core integration |
| **Pro** (P13-P18) | CI/CD, deployment, event monitoring, performance, cost, reference architecture | Production readiness |
| **Flagship** (F19-F24) | Multi-env, observability, incident runbook, data handling, RBAC, migration | Enterprise operations |
| **Flagship+** (X25-X30) | Advanced debugging, load testing, reliability, policy guardrails, architecture variants, pitfalls | Scale and resilience |

## Core Exa Methods Covered

| Method | Skill | Purpose |
|--------|-------|---------|
| `exa.search()` | core-workflow-a | Metadata-only search (URL, title, score) |
| `exa.searchAndContents()` | core-workflow-a | Search + text/highlights/summary extraction |
| `exa.findSimilar()` | core-workflow-b | Find pages similar to a seed URL |
| `exa.findSimilarAndContents()` | core-workflow-b | Similarity search + content extraction |
| `exa.getContents()` | core-workflow-b | Retrieve content for known URLs |
| `exa.answer()` | core-workflow-b | AI-generated answer with web citations |
| `exa.streamAnswer()` | core-workflow-b | Streaming answer with citations |

## Search Types

| Type | Latency | Best For |
|------|---------|----------|
| `instant` | < 150ms | Real-time autocomplete |
| `fast` | < 425ms | Speed-critical UI |
| `auto` | 300-1500ms | General purpose (default) |
| `neural` | 500-2000ms | Semantic/conceptual queries |
| `deep` | 2-5s | Maximum coverage |
| `deep-reasoning` | 5-15s | Complex research |

## Quick Start

```typescript
import Exa from "exa-js";
const exa = new Exa(process.env.EXA_API_KEY);

// Search with content extraction
const results = await exa.searchAndContents(
  "best practices for building RAG pipelines",
  {
    type: "neural",
    numResults: 5,
    text: { maxCharacters: 2000 },
    highlights: { maxCharacters: 500 },
    summary: { query: "key takeaways" },
  }
);
```

## Skills Reference

### Standard (S01-S12)
| Skill | Trigger |
|-------|---------|
| `exa-install-auth` | "install exa", "setup exa", "exa API key" |
| `exa-hello-world` | "exa example", "first exa query" |
| `exa-local-dev-loop` | "exa dev setup", "exa test setup" |
| `exa-sdk-patterns` | "exa patterns", "exa best practices" |
| `exa-core-workflow-a` | "exa search", "exa neural search", "searchAndContents" |
| `exa-core-workflow-b` | "exa find similar", "exa answer", "getContents" |
| `exa-common-errors` | "exa error", "exa 429", "debug exa" |
| `exa-debug-bundle` | "exa debug", "exa support bundle" |
| `exa-rate-limits` | "exa rate limit", "exa throttling" |
| `exa-security-basics` | "exa security", "secure exa key" |
| `exa-prod-checklist` | "exa production", "exa go-live" |
| `exa-upgrade-migration` | "upgrade exa", "update exa-js" |

### Pro (P13-P18)
| Skill | Trigger |
|-------|---------|
| `exa-ci-integration` | "exa CI", "exa GitHub Actions" |
| `exa-deploy-integration` | "deploy exa", "exa Vercel", "exa Docker" |
| `exa-webhooks-events` | "exa monitor", "exa content alerts" |
| `exa-performance-tuning` | "exa performance", "exa latency" |
| `exa-cost-tuning` | "exa cost", "reduce exa costs" |
| `exa-reference-architecture` | "exa architecture", "exa RAG pipeline" |

### Flagship (F19-F24)
| Skill | Trigger |
|-------|---------|
| `exa-multi-env-setup` | "exa environments", "exa dev prod" |
| `exa-observability` | "exa monitoring", "exa metrics" |
| `exa-incident-runbook` | "exa incident", "exa outage" |
| `exa-data-handling` | "exa data", "exa cache", "exa RAG context" |
| `exa-enterprise-rbac` | "exa access control", "exa team keys" |
| `exa-migration-deep-dive` | "migrate to exa", "switch to exa" |

### Flagship+ (X25-X30)
| Skill | Trigger |
|-------|---------|
| `exa-advanced-troubleshooting` | "exa deep debug", "exa latency spike" |
| `exa-load-scale` | "exa load test", "exa capacity" |
| `exa-reliability-patterns` | "exa reliability", "exa fallback" |
| `exa-policy-guardrails` | "exa policy", "exa content filter" |
| `exa-architecture-variants` | "exa blueprint", "exa at scale" |
| `exa-known-pitfalls` | "exa mistakes", "exa anti-patterns" |

## Key Resources

- [Exa API Documentation](https://docs.exa.ai)
- [exa-js SDK](https://github.com/exa-labs/exa-js)
- [Exa Dashboard](https://dashboard.exa.ai)
- [Exa Pricing](https://exa.ai/pricing)

## License

MIT
