# Firecrawl Skill Pack

> 30 Claude Code skills for Firecrawl — turn any website into LLM-ready markdown with scrape, crawl, map, and extract APIs

## What It Does

Firecrawl converts websites into clean markdown or structured JSON for LLM consumption. It handles JavaScript rendering, anti-bot bypassing, and pagination automatically. This skill pack teaches Claude Code every Firecrawl pattern from hello-world to enterprise content pipelines.

**SDK:** `@mendable/firecrawl-js` (npm) / `firecrawl-py` (PyPI)
**API:** `api.firecrawl.dev/v1` — scrape, crawl, map, extract, batch scrape
**Pricing:** Credit-based (1 credit = 1 page scraped)

## Installation

```bash
/plugin install firecrawl-pack@claude-code-plugins-plus
```

## Skills (30)

### Getting Started (S01-S04)
| Skill | What It Covers |
|-------|---------------|
| `firecrawl-install-auth` | Install `@mendable/firecrawl-js`, configure `FIRECRAWL_API_KEY`, verify connection |
| `firecrawl-hello-world` | Four minimal examples: scrape, crawl, map, extract |
| `firecrawl-local-dev-loop` | Self-hosted Docker for zero-credit dev, vitest mocks, integration tests |
| `firecrawl-sdk-patterns` | Singleton client, typed wrappers, retry with backoff, Zod validation |

### Core Workflows (S05-S06)
| Skill | What It Covers |
|-------|---------------|
| `firecrawl-core-workflow-a` | `scrapeUrl` + `crawlUrl` + `asyncCrawlUrl` with polling and content processing |
| `firecrawl-core-workflow-b` | `extract` with JSON schemas, `batchScrapeUrls`, `mapUrl` + selective scrape |

### Operations (S07-S12)
| Skill | What It Covers |
|-------|---------------|
| `firecrawl-common-errors` | Fix 401/402/429/500 errors, empty markdown, stuck crawls, wrong package name |
| `firecrawl-debug-bundle` | Collect SDK version, API health, credit balance, diagnostic scrape for support |
| `firecrawl-rate-limits` | Exponential backoff, p-queue concurrency, proactive throttling, batch endpoints |
| `firecrawl-security-basics` | API key storage, webhook HMAC-SHA256 verification, key rotation, content sanitization |
| `firecrawl-prod-checklist` | Pre-deploy validation: credentials, crawl limits, error handling, monitoring, rollback |
| `firecrawl-upgrade-migration` | v0 to v1/v2 migration: crawlerOptions to flat options, new methods, breaking changes |

### Pro (P13-P18)
| Skill | What It Covers |
|-------|---------------|
| `firecrawl-ci-integration` | GitHub Actions workflow, integration tests, mock-based unit tests, credit-aware CI |
| `firecrawl-deploy-integration` | Vercel serverless, Cloud Run, self-hosted Docker Compose, webhook endpoints |
| `firecrawl-webhooks-events` | `crawl.started/page/completed` events, signature verification, polling fallback |
| `firecrawl-performance-tuning` | Format selection, waitFor tuning, LRU caching, batch vs individual, map-first pattern |
| `firecrawl-cost-tuning` | Crawl limits, map+selective scrape, caching, credit monitoring, budget enforcement |
| `firecrawl-reference-architecture` | Scrape/crawl/map/extract pipeline, content processing, chunking, storage patterns |

### Flagship (F19-F24)
| Skill | What It Covers |
|-------|---------------|
| `firecrawl-multi-env-setup` | Dev/staging/prod config, self-hosted Docker for dev, credit-safe wrappers |
| `firecrawl-observability` | Scrape metrics, credit burn tracking, content quality scoring, Prometheus alerts |
| `firecrawl-incident-runbook` | Quick triage, decision tree by error code, communication templates, postmortem |
| `firecrawl-data-handling` | Markdown cleaning, Zod-validated extraction, deduplication, RAG chunking, storage |
| `firecrawl-enterprise-rbac` | Per-team API keys, domain allowlists, credit budgets, gateway proxy pattern |
| `firecrawl-migration-deep-dive` | Migrate from Puppeteer/Playwright/Cheerio to Firecrawl with adapter pattern |

### Flagship+ (X25-X30)
| Skill | What It Covers |
|-------|---------------|
| `firecrawl-advanced-troubleshooting` | Layer-by-layer isolation, empty scrape debugging, screenshot diagnosis, timing analysis |
| `firecrawl-load-scale` | Throughput measurement, batch scaling, p-queue workers, parallel async crawls |
| `firecrawl-reliability-patterns` | Circuit breaker, crawl-to-scrape fallback, content validation, credit guard |
| `firecrawl-policy-guardrails` | Domain blocklists, credit budgets, content quality gates, per-domain rate limits |
| `firecrawl-architecture-variants` | On-demand vs scheduled pipeline vs real-time RAG ingestion decision guide |
| `firecrawl-known-pitfalls` | 10 anti-patterns with BAD/GOOD code: unbounded crawl, wrong import, no validation |

## Quick Start

```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Scrape a page to markdown
const page = await firecrawl.scrapeUrl("https://docs.example.com", {
  formats: ["markdown"],
  onlyMainContent: true,
});

// Crawl an entire site
const site = await firecrawl.crawlUrl("https://docs.example.com", {
  limit: 50,
  scrapeOptions: { formats: ["markdown"] },
});

// Discover all URLs instantly
const map = await firecrawl.mapUrl("https://docs.example.com");

// Extract structured data with LLM
const data = await firecrawl.scrapeUrl("https://example.com/pricing", {
  formats: ["extract"],
  extract: { schema: { type: "object", properties: { plans: { type: "array" } } } },
});
```

## Key Links

- [Firecrawl Docs](https://docs.firecrawl.dev)
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Node SDK on npm](https://www.npmjs.com/package/@mendable/firecrawl-js)
- [GitHub](https://github.com/mendableai/firecrawl)

## License

MIT
