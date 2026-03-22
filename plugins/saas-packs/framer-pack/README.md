# Framer Skill Pack

> Claude Code skill pack for Framer design tool integration (18 skills)

## What It Does

Gives Claude Code deep knowledge of Framer's Plugin SDK, Server API, CMS Managed Collections, Code Components, and Code Overrides. Every skill uses real `framer-plugin` and `framer-api` APIs with actual React + Framer Motion code.

## Installation

```bash
/plugin install framer-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `framer-install-auth` | Set up framer-plugin SDK or framer-api Server API with API keys |
| `framer-hello-world` | First plugin, code component, code override, and Server API script |
| `framer-local-dev-loop` | Vite hot-reload plugin dev, component testing, Server API development |
| `framer-sdk-patterns` | Type-safe CMS ops, plugin state hooks, component patterns, override factory |
| `framer-core-workflow-a` | CMS Managed Collections — sync external data, field types, incremental sync |
| `framer-core-workflow-b` | Code Components with property controls, Code Overrides for animations |
| `framer-common-errors` | Fix plugin not showing, framer undefined, blank components, CORS |
| `framer-debug-bundle` | Collect versions, connectivity, and config for support |
| `framer-rate-limits` | Batch CMS writes, debounced plugin ops, Server API retry |
| `framer-security-basics` | API key management, plugin sandbox security, key rotation |
| `framer-prod-checklist` | Plugin, component, Server API, and publishing checklist |
| `framer-upgrade-migration` | Plugin SDK upgrades, API version migration, rollback |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `framer-ci-integration` | GitHub Actions for plugin builds and automated CMS sync + publish |
| `framer-deploy-integration` | Deploy Server API backends to Vercel, Fly.io for CMS sync |
| `framer-webhooks-events` | WebSocket subscriptions, external webhook-to-Framer sync bridge |
| `framer-performance-tuning` | Batch CMS ops, memoized components, persistent connections |
| `framer-cost-tuning` | Plan selection, CMS item budgeting, publish frequency optimization |
| `framer-reference-architecture` | Full architecture for plugins + Server API + components + CI/CD |

## Key Concepts

- **Plugin SDK** (`framer-plugin`) — runs inside Framer editor iframe for canvas manipulation
- **Server API** (`framer-api`) — headless WebSocket access for CMS sync and publishing
- **Managed Collections** — plugin-controlled CMS collections for external data sync
- **Code Components** — React components with property controls for the Framer canvas
- **Code Overrides** — Framer Motion animation behaviors applied to any layer

## License

MIT
