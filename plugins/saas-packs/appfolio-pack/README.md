# AppFolio Skill Pack

> Claude Code skills for AppFolio Property Manager API integration — properties, tenants, leases, accounting (18 skills)

AppFolio is a cloud-based property management platform. These skills use the real AppFolio Stack REST API with Basic Auth, covering properties, tenants, units, leases, bills, vendors, and owners endpoints. No npm SDK exists -- all code uses direct REST calls via axios.

## Installation

```bash
/plugin install appfolio-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `appfolio-install-auth` | Configure AppFolio Stack API Basic Auth credentials |
| `appfolio-hello-world` | Query properties, tenants, and leases via REST API |
| `appfolio-local-dev-loop` | Mock API server with sample property data, dev scripts |
| `appfolio-sdk-patterns` | Typed REST client, response caching, pagination handling |
| `appfolio-core-workflow-a` | Property management dashboard: portfolio summary, vacancy report |
| `appfolio-core-workflow-b` | Tenant onboarding, lease creation, renewal tracking |
| `appfolio-common-errors` | Diagnose 401/403/404/422/429 errors with diagnostic script |
| `appfolio-debug-bundle` | API connectivity test, response time measurement |
| `appfolio-rate-limits` | Bottleneck throttler, 429 retry with exponential backoff |
| `appfolio-security-basics` | TLS enforcement, credential rotation, PII handling |
| `appfolio-prod-checklist` | Production readiness validation for property management apps |
| `appfolio-upgrade-migration` | API version adapter with pagination support |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `appfolio-ci-integration` | GitHub Actions with mock API tests and sandbox integration |
| `appfolio-deploy-integration` | Cloud Run deployment with Secret Manager |
| `appfolio-webhooks-events` | Handle lease, payment, and maintenance webhook events |
| `appfolio-performance-tuning` | Parallel dashboard fetching, caching, incremental sync |
| `appfolio-cost-tuning` | API usage monitoring, cache-driven cost reduction |
| `appfolio-reference-architecture` | Full integration architecture with sync service pattern |

## Key Concepts

- **No npm SDK** -- AppFolio uses direct REST API with Basic Auth (client_id:client_secret)
- **Stack Partner Program** -- API access requires AppFolio Stack partnership approval
- **Property-centric** -- API organized around properties, units, tenants, leases, bills
- **Webhook-driven** -- React to lease, payment, and maintenance events

## License

MIT
