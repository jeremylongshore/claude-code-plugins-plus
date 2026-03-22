# Clerk Skill Pack

> 24 production-ready Claude Code skills for Clerk authentication -- real `@clerk/nextjs` v6 API code, not templates.

## What This Is

A complete skill pack for building, deploying, and operating Clerk-authenticated applications. Every skill contains real Clerk v6 code: `clerkMiddleware()`, `auth()`, `createRouteMatcher()`, `verifyWebhook()`, Svix HMAC verification, organization RBAC with `has()`, and more. No placeholder imports, no fake API patterns.

## Installation

```bash
/plugin install clerk-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `clerk-install-auth` | Install `@clerk/nextjs`, configure keys, add ClerkProvider, set up middleware |
| S02 | `clerk-hello-world` | Server/client auth patterns, `auth()` vs `currentUser()`, Express `getAuth()` |
| S03 | `clerk-local-dev-loop` | Dev instance config, test user seeding, Vitest mocks, Playwright fixtures |
| S04 | `clerk-sdk-patterns` | Server/client hooks, org-aware queries, JWT templates for Supabase/Hasura |
| S05 | `clerk-core-workflow-a` | Sign-up/sign-in components, custom forms, OAuth social login, MFA (TOTP) |
| S06 | `clerk-core-workflow-b` | `clerkMiddleware()` with route matchers, `auth.protect()`, session claims, org switching |
| S07 | `clerk-common-errors` | Fix `Missing publishableKey`, redirect loops, hydration mismatch, webhook signature failures |
| S08 | `clerk-debug-bundle` | Environment debug script, health check endpoint, client-side debug panel, support bundle |
| S09 | `clerk-rate-limits` | Rate limit headers, retry with exponential backoff, batching, Redis caching |
| S10 | `clerk-security-basics` | Secret key protection, hardened middleware with CSP headers, session freshness checks |
| S11 | `clerk-prod-checklist` | Live key validation script, security/monitoring/performance checklists, CI gate |
| S12 | `clerk-upgrade-migration` | v5 to v6 migration: async `auth()`, `clerkMiddleware`, import path changes |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `clerk-ci-integration` | GitHub Actions with Clerk secrets, Playwright auth state, test user seeding, Vitest mocks |
| P14 | `clerk-deploy-integration` | Vercel/Netlify/Railway/Docker deployment, env var configuration, post-deploy verification |
| P15 | `clerk-webhooks-events` | `verifyWebhook()` + manual Svix verification, event handlers, idempotency, Express raw body |
| P16 | `clerk-performance-tuning` | Middleware matcher optimization, React `cache()`, lazy-loaded components, Edge Runtime |
| P17 | `clerk-cost-tuning` | MAU pricing model, deferred auth routes, `unstable_cache()` for API call reduction |
| P18 | `clerk-reference-architecture` | Next.js full-stack, microservices with JWT proxy, multi-tenant SaaS, mobile + web shared backend |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `clerk-multi-env-setup` | Separate instances per environment, key mismatch validation, CI/CD environment promotion |
| F20 | `clerk-observability` | Pino structured auth logging, middleware perf tracking, Sentry integration, health checks |
| F21 | `clerk-incident-runbook` | Triage script, emergency auth bypass, key rotation, session revocation, post-incident template |
| F22 | `clerk-data-handling` | GDPR data export, right to be forgotten cascade, consent management via `publicMetadata` |
| F23 | `clerk-enterprise-rbac` | Custom roles/permissions, `auth.protect()` with role matchers, SAML SSO, Backend API role management |
| F24 | `clerk-migration-deep-dive` | Auth0/NextAuth/Firebase export, bulk import with rate limiting, parallel running bridge |

## Usage

Skills trigger automatically when you discuss Clerk topics:

- "Help me set up Clerk" -> `clerk-install-auth`
- "Fix this Clerk error" -> `clerk-common-errors`
- "Deploy my Clerk app" -> `clerk-deploy-integration`
- "Migrate from Auth0 to Clerk" -> `clerk-migration-deep-dive`

## Key Clerk Concepts Covered

- **Middleware**: `clerkMiddleware()` with `createRouteMatcher()` -- no default route protection, explicit `auth.protect()`
- **Server auth**: `auth()` (lightweight JWT parse) vs `currentUser()` (Backend API call, rate-limited)
- **Client auth**: `useUser()`, `useAuth()`, `useClerk()`, `<SignedIn>`, `<SignedOut>`, `<Protect>`
- **Organizations**: `OrganizationSwitcher`, `has({ role })`, `has({ permission })`, org-scoped sessions
- **Webhooks**: Svix HMAC-SHA256 verification, `verifyWebhook()` from `@clerk/backend/webhooks`
- **JWT Templates**: Custom tokens for Supabase, Hasura, Convex integration
- **Express**: `clerkMiddleware()`, `requireAuth()`, `getAuth()` from `@clerk/express`
- **Session tokens v2**: Compact format (default since April 2025), custom claims via Dashboard

## License

MIT
