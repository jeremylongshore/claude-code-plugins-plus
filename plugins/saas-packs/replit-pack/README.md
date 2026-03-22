# Replit Skill Pack

> 30 production-grade Claude Code skills for building, deploying, and operating applications on Replit.

Real `.replit` and `replit.nix` configuration. Real Replit Database, Object Storage, and Auth APIs. Real deployment patterns for Autoscale, Reserved VM, and Static hosting. Every code example runs on Replit as written.

## Installation

```bash
/plugin install replit-pack@claude-code-plugins-plus
```

## What You Get

**Platform configuration** — `.replit` TOML format (run/build/deploy/env/modules), `replit.nix` package management, Nix channel selection, and port binding that actually works with Replit's proxy.

**Three storage systems** — PostgreSQL via `DATABASE_URL` with auto dev/prod separation, Key-Value Database (`@replit/database` / `from replit import db`) with its 50 MiB / 5K key limits, and Object Storage (`@replit/object-storage`) for file uploads and backups.

**Replit Auth** — Zero-setup authentication via `X-Replit-User-Id`, `X-Replit-User-Name`, and other headers injected by Replit's proxy. Express and Flask middleware patterns included.

**Three deployment types** — Static (free, CDN-backed), Autoscale (scales to zero, pay per request), and Reserved VM (always-on, from $0.20/day). Custom domains with auto-SSL.

**Platform-aware patterns** — Ephemeral filesystem handling, SIGTERM graceful shutdown, cold start optimization, container lifecycle management, and REPL_IDENTITY token verification.

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `replit-install-auth` | .replit + replit.nix setup, Secrets (AES-256), Replit Auth headers |
| `replit-hello-world` | Working starter with Express, KV Database, Object Storage, Auth |
| `replit-local-dev-loop` | Hot reload, Webview, port config, dev/prod databases, Replit Agent |
| `replit-sdk-patterns` | Singleton clients, typed wrappers, retry/backoff for all Replit services |
| `replit-core-workflow-a` | Full-stack app: Express + PostgreSQL + Auth + Object Storage |
| `replit-core-workflow-b` | Teams admin: member management, seat audit, deployment promotion |
| `replit-common-errors` | Top 10 errors: container sleep, port binding, Nix, DB limits, auth |
| `replit-debug-bundle` | Diagnostic script collecting env, packages, DB status, network health |
| `replit-rate-limits` | Platform limits (KV, storage, egress) + app-level rate limiting |
| `replit-security-basics` | Secrets, REPL_IDENTITY tokens, Auth trust model, public Repl safety |
| `replit-prod-checklist` | Deploy checklist: config, secrets, health checks, rollback, custom domain |
| `replit-upgrade-migration` | Nix channel upgrades, KV-to-PostgreSQL migration, deployment type changes |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `replit-ci-integration` | GitHub Actions, deploy-on-push, post-deploy health verification |
| `replit-deploy-integration` | Autoscale vs Reserved VM vs Static, custom domains, rollbacks |
| `replit-webhooks-events` | Webhook receivers, Replit Extensions API, Agents & Automations |
| `replit-performance-tuning` | Cold start reduction, Nix caching, build optimization, memory management |
| `replit-cost-tuning` | Deployment sizing, seat audit, egress control, Autoscale vs VM economics |
| `replit-reference-architecture` | Production project structure, data layer strategy, platform constraints |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `replit-multi-env-setup` | Dev/staging/prod with dual databases, branch strategy, secret isolation |
| `replit-observability` | Health endpoints, structured logging, uptime monitoring, cold start detection |
| `replit-incident-runbook` | Triage, decision tree, remediation by error type, rollback, postmortem |
| `replit-data-handling` | PostgreSQL + KV + Object Storage patterns, sanitization, secure responses |
| `replit-enterprise-rbac` | Teams roles, custom groups, SSO/SAML, deployment permissions, audit logs |
| `replit-migration-deep-dive` | Migrate from Heroku/Railway/Docker, database import, post-migration checklist |

### Flagship+ Skills (X25-X30)
| Skill | What It Does |
|-------|-------------|
| `replit-advanced-troubleshooting` | Layer-by-layer diagnosis, Nix build debugging, crash loop analysis, memory leaks |
| `replit-load-scale` | Load testing with k6/autocannon, VM sizing, connection pool tuning, capacity planning |
| `replit-reliability-patterns` | Graceful startup/shutdown, persistent state, keep-alive, DB resilience |
| `replit-policy-guardrails` | Secret scanning, resource limits, endpoint protection, security audit checklist |
| `replit-architecture-variants` | Single-file to multi-service blueprints with growth path |
| `replit-known-pitfalls` | 10 real anti-patterns: ephemeral FS, public secrets, localhost binding, Nix deps |

## Key Replit Concepts

| Concept | Details |
|---------|---------|
| `.replit` | TOML config: run/build commands, env vars, deployment target, Nix channel |
| `replit.nix` | Nix expression defining system packages (runtimes, libraries, CLI tools) |
| Secrets | AES-256 encrypted env vars, auto-sync between Workspace and Deployments |
| Auth headers | `X-Replit-User-Id`, `X-Replit-User-Name`, etc. injected by Replit proxy |
| KV Database | `@replit/database` — 50 MiB, 5K keys, dict-like API |
| PostgreSQL | `DATABASE_URL` env var, auto dev/prod separation |
| Object Storage | `@replit/object-storage` — file uploads, backups, large data |
| Deployments | Static (free), Autoscale (pay per request), Reserved VM (fixed cost) |

## License

MIT
