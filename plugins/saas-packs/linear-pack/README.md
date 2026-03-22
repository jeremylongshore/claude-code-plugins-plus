# Linear Skill Pack

> 24 production-grade skills for building Linear integrations with the `@linear/sdk` TypeScript SDK and GraphQL API

**Install:** `/plugin install linear-pack@claude-code-plugins-plus`

## What This Does

Covers the full lifecycle of Linear integrations: SDK setup, issue/project/cycle management, webhooks, CI/CD pipelines, performance tuning, multi-environment deployment, observability, data sync, RBAC, and migration from Jira/Asana/GitHub Issues.

Every skill uses real Linear API patterns: `LinearClient`, `rawRequest()` for custom GraphQL, cursor-based pagination (`fetchNext()`/`fetchPrevious()`), typed error handling (`LinearError`, `InvalidInputLinearError`), HMAC-SHA256 webhook verification, and OAuth 2.0 with PKCE and refresh tokens.

## Skills

### Standard (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `linear-install-auth` | Install `@linear/sdk`, API key setup, OAuth 2.0 with PKCE, token refresh |
| `linear-hello-world` | First issue creation, team queries, workflow state exploration, raw GraphQL |
| `linear-local-dev-loop` | Project scaffolding, vitest integration tests, ngrok webhook tunneling |
| `linear-sdk-patterns` | Client singleton, cursor pagination, N+1 elimination, filtering, error types |
| `linear-core-workflow-a` | Issue CRUD, state transitions, parent/sub-issues, relations, comments, labels |
| `linear-core-workflow-b` | Projects, milestones, cycles, sprint planning, velocity, roadmap queries |
| `linear-common-errors` | Error response structure, auth failures, 429 handling, complexity limits |
| `linear-debug-bundle` | Debug client wrapper, request tracer, health check, env validator, REPL console |
| `linear-rate-limits` | Leaky bucket model, headers, exponential backoff, request queue, batch mutations |
| `linear-security-basics` | Key management, OAuth + PKCE, token refresh, webhook HMAC verification, rotation |
| `linear-prod-checklist` | Pre-deploy checklist, health check endpoint, deployment verification script |
| `linear-upgrade-migration` | SDK version upgrade, compatibility layers, breaking change patterns |

### Pro (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `linear-ci-integration` | GitHub Actions test workflows, PR-to-issue linking, CI failure issue creation |
| `linear-deploy-integration` | Deploy tracking with Linear comments, state transitions, rollback tracking |
| `linear-webhooks-events` | Webhook receiver, HMAC verification, event router, idempotency, all entity types |
| `linear-performance-tuning` | N+1 elimination, TTL caching, batch mutations, webhook cache invalidation |
| `linear-cost-tuning` | Usage auditing, polling-to-webhook migration, complexity reduction, coalescing |
| `linear-reference-architecture` | Simple, service-oriented, event-driven, and CQRS architecture patterns |

### Flagship (F19-F24)

| Skill | What It Does |
|-------|-------------|
| `linear-multi-env-setup` | Per-environment config, secret managers (Vault/AWS/GCP), environment guards |
| `linear-observability` | Prometheus metrics, pino logging, health checks, alerting rules |
| `linear-incident-runbook` | SEV1-4 classification, auth/rate-limit/webhook runbooks, communication templates |
| `linear-data-handling` | Full sync, incremental webhook sync, JSON export, consistency checks, conflict resolution |
| `linear-enterprise-rbac` | Role-to-scope mapping, permission guards, SAML SSO, SCIM provisioning, audit logging |
| `linear-migration-deep-dive` | Jira/Asana export, workflow mapping, markup conversion, batch import, validation |

## Key Linear API Facts

| Property | Value |
|----------|-------|
| API endpoint | `https://api.linear.app/graphql` |
| SDK package | `@linear/sdk` on npm |
| Auth methods | API key (`lin_api_*`), OAuth 2.0 (PKCE supported) |
| Rate limits | 5,000 req/hr + 250,000 complexity pts/hr (leaky bucket) |
| Max query complexity | 10,000 points per single query |
| Webhook signature | HMAC-SHA256 in `Linear-Signature` header |
| Webhook entities | Issues, Comments, Attachments, Documents, Projects, Cycles, Labels, Users, SLAs |
| OAuth scopes | `read`, `write`, `issues:create`, `admin`, `initiative:*`, `customer:*` |
| Pagination | Relay-style cursor (`first`/`after`, `last`/`before`) |

## License

MIT
