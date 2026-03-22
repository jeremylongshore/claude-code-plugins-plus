# SerpApi Skill Pack

> 18 production-ready Claude Code skills for SerpApi -- real search scraping code for Google, Bing, YouTube, News, Shopping, and Maps.

## What This Is

A complete skill pack for building search-powered applications with SerpApi. Every skill contains real SerpApi code: `serpapi.Client`, `getJson`, multi-engine search (Google, Bing, YouTube, News, Shopping, Maps), structured result parsing, credit-based cost management, and SERP monitoring pipelines. No placeholder imports, no fake patterns.

## Installation

```bash
/plugin install serpapi-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `serpapi-install-auth` | Install `serpapi` package, configure API key, verify with Account API |
| S02 | `serpapi-hello-world` | Google search with organic results, answer box, knowledge graph parsing |
| S03 | `serpapi-local-dev-loop` | Record fixtures from real API, mock client, offline testing |
| S04 | `serpapi-sdk-patterns` | Cached client, multi-engine abstraction, async search, typed results |
| S05 | `serpapi-core-workflow-a` | Google Search: organic results, PAA, local pack, filters, pagination |
| S06 | `serpapi-core-workflow-b` | YouTube, Bing, Google News, Shopping, Maps -- engine-specific params |
| S07 | `serpapi-common-errors` | Fix invalid key, exhausted credits, empty results, CAPTCHA issues |
| S08 | `serpapi-debug-bundle` | Account status, recent searches archive, test search diagnostics |
| S09 | `serpapi-rate-limits` | Plan tiers, credit monitoring, request throttling, archive retrieval |
| S10 | `serpapi-security-basics` | Backend proxy pattern, never expose key to frontend, rate limit proxy |
| S11 | `serpapi-prod-checklist` | Credit budget, caching, health check with remaining credits |
| S12 | `serpapi-upgrade-migration` | google-search-results to serpapi package, callback to async migration |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `serpapi-ci-integration` | Fixture-based unit tests (0 credits), live integration on main only |
| P14 | `serpapi-deploy-integration` | Vercel/Cloud Run search proxy, health check with credit status |
| P15 | `serpapi-webhooks-events` | Async search polling, SERP monitoring pipeline, keyword rank tracking |
| P16 | `serpapi-performance-tuning` | Multi-layer caching (LRU + Redis), Google Light API, parallel search |
| P17 | `serpapi-cost-tuning` | Credit calculator, cache hit rate analysis, archive API for free retrieval |
| P18 | `serpapi-reference-architecture` | Search service facade, rank tracker, credit budget manager |

## Key SerpApi Concepts Covered

- **Engines**: `google`, `google_light`, `bing`, `youtube`, `google_news`, `google_shopping`, `google_maps`
- **Parameters**: `q` (most engines), `search_query` (YouTube), `num`, `start`, `location`, `hl`, `gl`
- **Results**: `organic_results`, `answer_box`, `knowledge_graph`, `related_questions`, `local_results`
- **Pricing**: 1 credit/search, Free (100/mo) to Enterprise (50K+/mo)
- **Archive**: Free retrieval of previous searches by `search_id`

## License

MIT
