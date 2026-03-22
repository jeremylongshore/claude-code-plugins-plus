# Vercel Skill Pack

> 30 production-grade Claude Code skills for Vercel deployments, serverless functions, Edge Runtime, and platform operations.

Deploy, scale, and operate Vercel applications with real API endpoints (`api.vercel.com/v9/*`), real CLI commands (`vercel deploy`, `vercel env`, `vercel rollback`), real Edge Function patterns (`export const config = { runtime: 'edge' }`), and real error codes (`FUNCTION_INVOCATION_FAILED`, `FUNCTION_THROTTLED`). Every skill contains working code, not placeholders.

**Links:** [Vercel Docs](https://vercel.com/docs) | [Vercel REST API](https://vercel.com/docs/rest-api) | [Install](#installation)

---

## Installation

```bash
/plugin install vercel-pack@claude-code-plugins-plus
```

## What's Inside

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `vercel-install-auth` | Install CLI, create scoped access tokens, link projects, pull env vars |
| S02 | `vercel-hello-world` | Deploy minimal project with static page + serverless API route |
| S03 | `vercel-local-dev-loop` | Run `vercel dev`, manage `.env` files, test functions locally with Vitest |
| S04 | `vercel-sdk-patterns` | Typed REST API client wrapper with pagination, retry, and error classes |
| S05 | `vercel-deploy-preview` | Create preview deployments via CLI and API, configure deployment protection |
| S06 | `vercel-edge-functions` | Build Edge Functions with geo headers, middleware, streaming, Edge Config |
| S07 | `vercel-common-errors` | Diagnose BUILD_FAILED, FUNCTION_INVOCATION_TIMEOUT, 404s, and env var issues |
| S08 | `vercel-debug-bundle` | Collect deployment state, function logs, and platform status for support tickets |
| S09 | `vercel-rate-limits` | Handle API 429s with retry, implement WAF rate limiting with @vercel/firewall |
| S10 | `vercel-security-basics` | Security headers, CSP, deployment protection, token rotation, secret scoping |
| S11 | `vercel-prod-checklist` | Production deploy checklist with domain setup, health checks, instant rollback |
| S12 | `vercel-upgrade-migration` | Upgrade CLI, Node.js runtime, Next.js versions with breaking change detection |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `vercel-ci-integration` | GitHub Actions workflows for preview on PR, production on merge, test gating |
| P14 | `vercel-deploy-integration` | Production deploy methods, instant rollback, rolling releases, deploy hooks |
| P15 | `vercel-webhooks-events` | Handle deployment.ready/error webhooks with HMAC signature verification |
| P16 | `vercel-performance-tuning` | Edge caching, ISR, cold start elimination, bundle optimization, image optimization |
| P17 | `vercel-cost-tuning` | Fluid Compute pricing, function memory right-sizing, spend management |
| P18 | `vercel-reference-architecture` | Layered project structure with typed env vars, lazy DB, health checks |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `vercel-multi-env-setup` | Scoped env vars per environment, custom environments, branch-specific domains |
| F20 | `vercel-observability` | Vercel Analytics, runtime logs, log drains, OpenTelemetry, Sentry integration |
| F21 | `vercel-incident-runbook` | 5-minute triage, instant rollback procedure, communication templates, postmortem |
| F22 | `vercel-data-handling` | PII redaction, GDPR data subject requests, data residency via function regions |
| F23 | `vercel-enterprise-rbac` | Team roles, Access Groups, SAML SSO, audit logging, middleware-level auth |
| F24 | `vercel-migration-deep-dive` | Migrate from Netlify/AWS/Cloudflare with config mapping and DNS cutover |

### Flagship+ Skills (X25-X30)

| # | Skill | What It Does |
|---|-------|-------------|
| X25 | `vercel-advanced-troubleshooting` | Request tracing, cold start analysis, bundle inspection, edge crash debugging |
| X26 | `vercel-load-scale` | k6/autocannon load tests, Fluid Compute concurrency tuning, capacity planning |
| X27 | `vercel-reliability-patterns` | Circuit breakers, retry with backoff, stale cache fallback, idempotency keys |
| X28 | `vercel-policy-guardrails` | ESLint rules, pre-commit credential scanning, CI policy checks, deploy freezes |
| X29 | `vercel-architecture-variants` | 5 architecture blueprints from static site to multi-zone enterprise |
| X30 | `vercel-known-pitfalls` | 15 anti-patterns with severity ratings, detection scripts, and fixes |

## Usage

Skills trigger automatically when you discuss Vercel topics:

- "Help me set up Vercel" triggers `vercel-install-auth`
- "Deploy my app to production" triggers `vercel-prod-checklist`
- "My Vercel function is timing out" triggers `vercel-common-errors`
- "Set up edge middleware for auth" triggers `vercel-edge-functions`
- "Why is my Vercel bill so high?" triggers `vercel-cost-tuning`

## Key API Endpoints Covered

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List projects | GET | `/v9/projects` |
| Create deployment | POST | `/v13/deployments` |
| List deployments | GET | `/v6/deployments` |
| Manage env vars | GET/POST/PATCH/DELETE | `/v9/projects/{id}/env` |
| Add domain | POST | `/v9/projects/{id}/domains` |
| Promote deployment | POST | `/v9/projects/{id}/promote` |

## License

MIT
