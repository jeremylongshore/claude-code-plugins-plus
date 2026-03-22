# Clay Skill Pack

> Claude Code skill pack for Clay.com data enrichment platform (30 skills)

Clay is a data enrichment and lead research platform that aggregates 150+ data providers (Apollo, Clearbit, Hunter, ZoomInfo, People Data Labs) into a table-based workflow with waterfall enrichment, Claygent AI research, and CRM synchronization. This skill pack covers the full integration surface: webhooks, HTTP API columns, Claygent prompts, CRM sync, credit optimization, and production pipeline architecture.

**Links:** [Clay University](https://university.clay.com) | [Clay.com](https://www.clay.com) | [Community](https://community.clay.com)

---

## Installation

```bash
/plugin install clay-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `clay-install-auth` | Set up Clay API keys, webhook URLs, and provider connections |
| `clay-hello-world` | Send your first record to Clay and get enriched data back |
| `clay-local-dev-loop` | Local dev feedback loop with ngrok, webhooks, and HTTP API callbacks |
| `clay-sdk-patterns` | Production-ready TypeScript/Python wrappers for Clay webhooks and Enterprise API |
| `clay-core-workflow-a` | Lead enrichment pipeline: webhook intake, waterfall email finding, ICP scoring |
| `clay-core-workflow-b` | Claygent AI research, personalized outreach copy, campaign export |
| `clay-common-errors` | Top 12 Clay errors: webhook 422s, credit exhaustion, Claygent failures |
| `clay-debug-bundle` | Collect diagnostic evidence for Clay support tickets |
| `clay-rate-limits` | Handle 429s, webhook throttling, plan-level rate limits, provider limits |
| `clay-security-basics` | API key rotation, webhook signature verification, PII protection |
| `clay-prod-checklist` | Production readiness checklist: data quality gates, credit controls, monitoring |
| `clay-upgrade-migration` | Navigate the March 2026 pricing overhaul (Data Credits + Actions split) |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `clay-ci-integration` | GitHub Actions CI for Clay webhook handlers with data schema validation |
| `clay-deploy-integration` | Deploy Clay receivers to Vercel, Cloud Run, or Docker |
| `clay-webhooks-events` | Inbound webhooks and outbound HTTP API column callbacks with idempotency |
| `clay-performance-tuning` | Column ordering, conditional runs, waterfall depth optimization |
| `clay-cost-tuning` | Connect own API keys (70-80% savings), credit budgeting, sampling |
| `clay-reference-architecture` | Table schema design, ICP scoring formulas, CRM sync patterns |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `clay-multi-env-setup` | Per-environment tables, webhook URLs, and safety guards |
| `clay-observability` | Credit burn dashboards, enrichment hit rate monitoring, Prometheus metrics |
| `clay-incident-runbook` | Triage scripts, decision trees, postmortem templates for Clay incidents |
| `clay-data-handling` | GDPR/CCPA compliance, data retention, PII classification, export controls |
| `clay-enterprise-rbac` | Workspace roles, credit budgets per table, API key isolation, access audits |
| `clay-migration-deep-dive` | Migrate from ZoomInfo/Apollo/Clearbit to Clay with parallel run validation |

### Flagship+ Skills (X25-X30)
| Skill | Description |
|-------|-------------|
| `clay-advanced-troubleshooting` | Layer isolation, HTTP API column debugging, Claygent failure analysis |
| `clay-load-scale` | High-volume (10K-100K+/mo) with queue architecture and webhook rotation |
| `clay-reliability-patterns` | Credit circuit breakers, dead letter queues, graceful degradation |
| `clay-policy-guardrails` | Spending caps, privacy enforcement, input validation, export restrictions |
| `clay-architecture-variants` | Direct vs webhook+HTTP API vs queue-based pipeline comparison |
| `clay-known-pitfalls` | Top 10 Clay gotchas: 50K webhook limit, waterfall misconfiguration, auto-update traps |

## Key Concepts

| Concept | What It Is |
|---------|------------|
| **Webhook (inbound)** | POST JSON to a Clay table's unique URL to create rows |
| **HTTP API column (outbound)** | Clay POSTs enriched data to your endpoint after enrichment |
| **Waterfall enrichment** | Try multiple providers sequentially until data is found |
| **Claygent** | AI research agent (GPT-4) that scrapes websites and extracts data |
| **Data Credits** | Clay's currency for buying enrichment data from providers |
| **Actions** | Clay's currency for platform operations (1 per enrichment) |
| **Own API keys** | Connect your provider keys for 0 Data Credits per enrichment |

## Usage

Skills trigger automatically when you discuss Clay topics. For example:

- "Help me set up Clay" triggers `clay-install-auth`
- "Enrich a list of leads" triggers `clay-core-workflow-a`
- "Debug this Clay error" triggers `clay-common-errors`
- "Optimize Clay costs" triggers `clay-cost-tuning`
- "Write Claygent prompts" triggers `clay-core-workflow-b`

## License

MIT
