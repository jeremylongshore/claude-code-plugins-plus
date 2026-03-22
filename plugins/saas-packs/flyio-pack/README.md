# Fly.io Skill Pack

> 18 production-ready Claude Code skills for Fly.io edge compute -- real flyctl commands, Machines API code, and fly.toml configuration.

## What This Is

A complete skill pack for deploying, scaling, and operating apps on Fly.io. Every skill contains real `flyctl` commands, Machines API (`https://api.machines.dev`) TypeScript code, and production `fly.toml` configuration. No placeholder CLI commands, no fake SDK imports.

## Installation

```bash
/plugin install flyio-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `flyio-install-auth` | Install flyctl, configure auth tokens, verify Machines API access |
| S02 | `flyio-hello-world` | `fly launch` a Docker app, deploy via Machines API, verify with cURL |
| S03 | `flyio-local-dev-loop` | Docker local builds, `fly proxy` for remote services, dev fly.toml |
| S04 | `flyio-sdk-patterns` | Typed Machines API client, multi-region deploy, blue-green via API |
| S05 | `flyio-core-workflow-a` | fly.toml config, secrets, scaling across regions, app lifecycle |
| S06 | `flyio-core-workflow-b` | Fly Postgres, persistent volumes, 6PN private networking |
| S07 | `flyio-common-errors` | Health check failures, build errors, volume mounts, .internal DNS |
| S08 | `flyio-debug-bundle` | Collect status, machine state, logs, volumes, doctor into tarball |
| S09 | `flyio-rate-limits` | Machines API limits, retry with backoff, batch operations |
| S10 | `flyio-security-basics` | Encrypted secrets, deploy tokens, TLS certs, WireGuard VPN |
| S11 | `flyio-prod-checklist` | Health checks, auto-scaling, monitoring, rollback procedure |
| S12 | `flyio-upgrade-migration` | Apps v1 to v2, flyctl upgrade, Postgres major version upgrade |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `flyio-ci-integration` | GitHub Actions with deploy tokens, staging/production workflows |
| P14 | `flyio-deploy-integration` | Blue-green via Machines API, canary release, multi-region rollout |
| P15 | `flyio-webhooks-events` | Machine state polling, health check handlers, structured log processing |
| P16 | `flyio-performance-tuning` | Suspend vs stop, VM sizing, multi-region latency, connection pooling |
| P17 | `flyio-cost-tuning` | Pricing reference, auto-stop config, resource audit, right-sizing |
| P18 | `flyio-reference-architecture` | Multi-region web + Postgres + Redis + worker architecture |

## Key Fly.io Concepts

- **Machines API**: `https://api.machines.dev` with `Authorization: Bearer <token>`
- **flyctl**: CLI for `fly launch`, `fly deploy`, `fly scale`, `fly secrets`
- **fly.toml**: App config -- services, auto-stop, concurrency, VM sizing
- **6PN**: Private networking via `.internal` DNS between apps in same org
- **Regions**: 30+ worldwide, Anycast routing to nearest
- **Fly Postgres**: Managed Postgres running as a Fly app with automated replication

## License

MIT
