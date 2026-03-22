# Bright Data Skill Pack

> Claude Code skill pack for Bright Data web scraping, proxies, and data collection (18 skills)

## What It Does

Gives Claude Code deep knowledge of Bright Data's proxy infrastructure, Scraping Browser, SERP API, Web Scraper API, and Datasets API. Every skill contains real proxy configuration code using `brd.superproxy.io`, actual API endpoints, and production-tested patterns — no fake SDK imports.

## Installation

```bash
/plugin install brightdata-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `brightdata-install-auth` | Configure zone credentials, SSL cert, proxy authentication |
| `brightdata-hello-world` | First scrape through Web Unlocker proxy with geo-targeting |
| `brightdata-local-dev-loop` | Dev environment with response caching and mocked proxy tests |
| `brightdata-sdk-patterns` | Proxy client singleton, retry wrapper, sticky sessions, cheerio parsing |
| `brightdata-core-workflow-a` | Scraping Browser with Playwright/Puppeteer over CDP WebSocket |
| `brightdata-core-workflow-b` | SERP API structured search results and Web Scraper API async triggers |
| `brightdata-common-errors` | Diagnose 407, 502, SSL, timeout, and X-Luminati-Error headers |
| `brightdata-debug-bundle` | Collect proxy connectivity, zone status, and error logs for support |
| `brightdata-rate-limits` | Concurrent request limiter, backoff for proxy errors, trigger rate limits |
| `brightdata-security-basics` | Zone isolation, credential rotation, git secret scanning |
| `brightdata-prod-checklist` | Zone verification, health checks, monitoring alerts, rollback |
| `brightdata-upgrade-migration` | Migrate between zones, products, and Datasets API versions |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `brightdata-ci-integration` | GitHub Actions with mocked unit tests and live proxy integration tests |
| `brightdata-deploy-integration` | Deploy to Vercel, Fly.io, Cloud Run with secrets management |
| `brightdata-webhooks-events` | Web Scraper API webhook delivery, notification endpoints, dedup |
| `brightdata-performance-tuning` | Connection pooling, response caching, concurrent scraping, bulk API |
| `brightdata-cost-tuning` | Product selection cost matrix, caching ROI, usage monitoring |
| `brightdata-reference-architecture` | Multi-product client, scraping pipeline, cron scheduler |

## Key Concepts

- **No SDK** — Bright Data uses HTTP proxy protocol (`brd.superproxy.io:33335`) and REST APIs
- **Zone credentials** — Customer ID + Zone Name + Zone Password, not API keys
- **Products**: Web Unlocker (anti-bot bypass), Scraping Browser (JS rendering), SERP API (search results), Web Scraper API (async bulk), Datasets (pre-built)
- **Geo-targeting** — append `-country-us` or `-city-newyork` to proxy username

## License

MIT
