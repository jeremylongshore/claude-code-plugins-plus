# Lokalise Skill Pack

> Claude Code skill pack for Lokalise translation management — 24 skills covering the full localization lifecycle from SDK setup through production operations.

## Installation

```bash
/plugin install lokalise-pack@claude-code-plugins-plus
```

## What This Pack Does

Provides production-grade guidance for `@lokalise/node-api` SDK (ESM v9+), `lokalise2` CLI, and the Lokalise REST API v2. Every skill contains real SDK code, real API endpoints, real error codes, and real webhook event names.

## Skills

### Getting Started (S01-S04)
| Skill | What It Does |
|-------|-------------|
| `lokalise-install-auth` | Install SDK/CLI, generate API tokens, verify connection |
| `lokalise-hello-world` | Create project, add keys, set translations, export — end to end |
| `lokalise-local-dev-loop` | Push/pull scripts, file watcher, mock translations, framework integration |
| `lokalise-sdk-patterns` | Client singleton, cursor pagination, typed errors, batch ops, retry/rate-limit |

### Core Workflows (S05-S08)
| Skill | What It Does |
|-------|-------------|
| `lokalise-core-workflow-a` | Upload source files, create/update keys, tag and bulk operations |
| `lokalise-core-workflow-b` | Download translations, manage review status, contributors, file formats |
| `lokalise-common-errors` | Diagnose 401/400/404/429/413/500 with curl commands and SDK error wrapper |
| `lokalise-debug-bundle` | Collect env info, API connectivity, project stats, redacted logs into tar.gz |

### Reliability (S09-S12)
| Skill | What It Does |
|-------|-------------|
| `lokalise-rate-limits` | Request queue (170ms spacing), exponential backoff, quota monitoring |
| `lokalise-security-basics` | Token scoping, content sanitization, webhook secret verification, CI secrets |
| `lokalise-prod-checklist` | 9-point pre-deploy checklist: coverage, keys, format, security, OTA, RBAC |
| `lokalise-upgrade-migration` | SDK v8 CJS to v9 ESM migration, pagination changes, breaking change detection |

### Pro (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `lokalise-ci-integration` | GitHub Actions upload/download, PR translation checks, branch-based workflows |
| `lokalise-deploy-integration` | Vercel/Netlify/Cloud Run deploy, OTA for iOS/Android, environment-specific bundles |
| `lokalise-webhooks-events` | Create webhooks, handle 10+ event types, secret verification, idempotency |
| `lokalise-performance-tuning` | Cursor pagination, local caching, batch ops, PQueue throttling, benchmarks |
| `lokalise-cost-tuning` | Seat optimization, TM leverage, MT triage, dead key cleanup, spend monitoring |
| `lokalise-reference-architecture` | Architecture diagram, project structure, OTA vs build-time, TypeScript types |

### Flagship (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `lokalise-multi-env-setup` | Dev/staging/prod isolation, secret management, promotion workflow |
| `lokalise-observability` | API metrics, translation progress gauges, webhook monitoring, Prometheus alerts |
| `lokalise-incident-runbook` | Quick diagnostics, 4 triage paths, fallback translations, communication templates |
| `lokalise-data-handling` | Key metadata, snapshots, branches, export formats, encoding, plural forms |
| `lokalise-enterprise-rbac` | Role hierarchy, language scoping, contributor groups, SSO, permission audit |
| `lokalise-migration-deep-dive` | Migrate from Crowdin/Phrase/POEditor: export, transform, upload, validate |

## Key Facts

| Fact | Value |
|------|-------|
| SDK | `@lokalise/node-api` v9+ (ESM) |
| CLI | `lokalise2` (Go binary) |
| API Base | `https://api.lokalise.com/api2` |
| Rate Limit | 6 requests/second per token |
| Max Keys Per Request | 500 |
| File Upload | Async — returns process ID, poll until `finished` |
| File Download | Returns S3 bundle URL (ZIP), valid ~30 minutes |
| Webhook Timeout | 8 seconds — respond 200 immediately, process async |
| Auth Header | `X-Api-Token` |
| Webhook Auth | `X-Secret` header (random string, verify on every request) |

## Usage

Skills activate automatically when you discuss Lokalise topics:

- "Help me set up Lokalise" activates `lokalise-install-auth`
- "Debug this Lokalise error" activates `lokalise-common-errors`
- "Set up CI for translations" activates `lokalise-ci-integration`
- "Handle Lokalise webhooks" activates `lokalise-webhooks-events`
- "Optimize Lokalise costs" activates `lokalise-cost-tuning`

## License

MIT
