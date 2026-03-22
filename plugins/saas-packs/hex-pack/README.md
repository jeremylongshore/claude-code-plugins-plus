# Hex Skill Pack

> Claude Code skill pack for Hex data platform API (18 skills)

## What It Does

Gives Claude Code deep knowledge of Hex's public API for triggering notebook project runs, polling status, managing users, and building data pipelines. Skills cover API token authentication, project orchestration with Airflow/Dagster, scheduled runs, and the Admin API for workspace management.

## Installation

```bash
/plugin install hex-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `hex-install-auth` | API token generation, scopes (read vs run), verification |
| `hex-hello-world` | List projects, trigger a run, poll for completion |
| `hex-local-dev-loop` | Typed HexClient class, mocked tests, project structure |
| `hex-sdk-patterns` | Run with retry, Python hextoolkit, Airflow provider |
| `hex-core-workflow-a` | Project orchestration: parameterized runs, pipeline sequencing |
| `hex-core-workflow-b` | Scheduled runs, Admin API (users, groups, connections) |
| `hex-common-errors` | Fix 401/403/404/429, ERRORED/KILLED run status |
| `hex-debug-bundle` | API connectivity test, project listing diagnostic |
| `hex-rate-limits` | RunProject limits (20/min, 60/hr), queue-based triggering |
| `hex-security-basics` | Token scoping, expiration, environment isolation |
| `hex-prod-checklist` | API access, project publishing, orchestration, monitoring |
| `hex-upgrade-migration` | API versioning, Airflow provider updates |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `hex-ci-integration` | GitHub Actions to trigger Hex project on deploy |
| `hex-deploy-integration` | Vercel/Cloud Run orchestration endpoints |
| `hex-webhooks-events` | Run status polling with callbacks, Slack notifications |
| `hex-performance-tuning` | Project caching, parallel runs, adaptive polling |
| `hex-cost-tuning` | Plan comparison, run frequency tracking, cache optimization |
| `hex-reference-architecture` | Full orchestration architecture with pipeline definitions |

## Key Concepts

- **API base** — `https://app.hex.tech/api/v1/`
- **Auth** — OAuth 2.0 Bearer token, generated per-user in workspace settings
- **Core workflow** — RunProject (POST) then poll GetRunStatus until COMPLETED/ERRORED
- **Rate limits** — RunProject: 20/min, 60/hr
- **Orchestration** — Native integrations with Airflow, Dagster, Orchestra
- **Input params** — Pass parameters to published projects at run time

## License

MIT
