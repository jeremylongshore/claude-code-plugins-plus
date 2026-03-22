# Sentry Skill Pack

Complete Sentry integration for Claude Code — 30 skills covering SDK v8, error tracking, performance monitoring, source maps, release management, distributed tracing, and production operations.

## Installation

```bash
/plugin install sentry-pack@claude-code-plugins-plus
```

## What This Pack Does

Every skill contains real Sentry code: actual `Sentry.init()` configurations, real API endpoints (`sentry.io/api/0/`), real SDK patterns (`captureException`, `startSpan`, `withScope`), real CLI commands (`sentry-cli releases`, `sourcemaps upload`), and real error tables with causes and fixes. No placeholders.

## Skills (30)

### Onboarding (6)

| Skill | What it does |
|-------|-------------|
| `sentry-install-auth` | SDK v8 install, DSN config, `instrument.mjs` setup, ESM `--import` flag |
| `sentry-hello-world` | First error capture, `captureException`, user context, breadcrumbs, dashboard verification |
| `sentry-local-dev-loop` | Dev-optimized init, Sentry Spotlight, conditional DSN, offline mode |
| `sentry-sdk-patterns` | Centralized error handler module, Express/React error boundaries, async patterns, testing mocks |
| `sentry-error-capture` | `captureException`, `withScope`, `beforeSend`, custom fingerprinting, `ignoreErrors` |
| `sentry-performance-tracing` | `startSpan`, `startSpanManual`, distributed tracing, custom measurements, `tracesSampler` |

### Operations (6)

| Skill | What it does |
|-------|-------------|
| `sentry-common-errors` | 8 diagnosed problems: missing events, `beforeSend` bugs, source maps, ESM, 429s, duplicates |
| `sentry-debug-bundle` | Diagnostic report script, network tests, source map explain, health check endpoint |
| `sentry-rate-limits` | `sampleRate`, `tracesSampler`, `ignoreErrors`, `denyUrls`, inbound filters, spike protection |
| `sentry-security-basics` | `sendDefaultPii: false`, `beforeSend` scrubbing, token scopes, allowed domains, audit logging |
| `sentry-prod-checklist` | 30-item checklist: security, source maps, alerting, performance, release management |
| `sentry-upgrade-migration` | v7-to-v8 migration: `@sentry/migr8`, integration functions, Hub removal, ESM, `startSpan` |

### CI/CD (6)

| Skill | What it does |
|-------|-------------|
| `sentry-ci-integration` | GitHub Actions workflow, GitLab CI, `getsentry/action-release`, webpack/vite plugins |
| `sentry-deploy-integration` | `sentry-cli releases deploys`, release health, multi-env tracking, rollback recording |
| `sentry-release-management` | `releases new/finalize`, `set-commits --auto`, `sourcemaps upload --validate`, deploy API |
| `sentry-performance-tuning` | `tracesSampler`, parameterized names, Web Vitals, profiling, SDK overhead measurement |
| `sentry-cost-tuning` | Billing category audit, `ignoreErrors`, `denyUrls`, `beforeSend`, inbound filters, spend alerts |
| `sentry-reference-architecture` | One-project-per-service pattern, shared config package, alert hierarchy, ownership rules |

### Enterprise (6)

| Skill | What it does |
|-------|-------------|
| `sentry-multi-env-setup` | Environment-specific configs, separate DSNs, env-filtered alerts, CI/CD env tagging |
| `sentry-observability` | OpenTelemetry bridge, Winston integration, request ID correlation, custom metrics, PagerDuty/Slack |
| `sentry-incident-runbook` | P0-P3 severity, triage checklist, API investigation, communication templates, postmortem |
| `sentry-data-handling` | PII scrubbing (client + server), GDPR erasure, advanced regex rules, SOC 2/HIPAA patterns |
| `sentry-enterprise-rbac` | Org/team roles, SAML SSO, SCIM provisioning, token scopes, audit log API |
| `sentry-migration-deep-dive` | Rollbar/Bugsnag-to-Sentry mapping, parallel run, alert migration, old SDK removal |

### Advanced (6)

| Skill | What it does |
|-------|-------------|
| `sentry-advanced-troubleshooting` | Transport debugging, systematic event diagnosis, `sourcemaps explain`, memory profiling |
| `sentry-load-scale` | Adaptive sampling, tiered transaction rates, graceful shutdown, multi-region tags, cost modeling |
| `sentry-reliability-patterns` | Circuit breaker, offline queue, dual-write, fallback logging, health check endpoint |
| `sentry-policy-guardrails` | Shared config package, mandatory scrubbing, project naming, CI enforcement, token rotation |
| `sentry-architecture-variants` | Monolith/microservices/serverless/Next.js/multi-tenant/worker patterns with real configs |
| `sentry-known-pitfalls` | 12 pitfalls: late init, string captures, `beforeSend` void, scope leaks, URL prefix mismatch |

## SDK Coverage

- `@sentry/node` v8 — Node.js backend
- `@sentry/browser` — Frontend/SPA
- `@sentry/react`, `@sentry/nextjs`, `@sentry/vue` — Framework SDKs
- `@sentry/aws-serverless`, `@sentry/google-cloud-serverless` — Serverless
- `@sentry/profiling-node` — Continuous profiling
- `@sentry/cli` — Release management, source maps, deploys
- Sentry REST API (`sentry.io/api/0/`) — Issues, releases, stats, teams

## Resources

- [Sentry Documentation](https://docs.sentry.io)
- [Sentry Dashboard](https://sentry.io)
- [SDK v7 to v8 Migration](https://docs.sentry.io/platforms/javascript/migration/v7-to-v8/)
- [Sentry Status](https://status.sentry.io)

## License

MIT
