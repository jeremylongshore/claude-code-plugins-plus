---
name: clickhouse-local-dev-loop
description: |
  Run ClickHouse locally with Docker, configure test fixtures, and iterate fast.
  Use when setting up a local ClickHouse dev environment, writing integration
  tests against ClickHouse, or running ClickHouse in Docker Compose for local work.
  Trigger with "clickhouse local dev", "clickhouse docker", "clickhouse dev
  environment", "run clickhouse locally", "clickhouse docker compose".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(docker-compose:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---

# ClickHouse Local Dev Loop

## Overview

Run ClickHouse in Docker for local development with fast schema iteration, seed
data, and integration testing using vitest. This skill scaffolds a
Docker-Compose-based dev loop: an auto-migrating init script, a seed generator,
a reusable client singleton, and a truncate-between-tests integration harness —
so schema changes and query work stay a `docker compose up` away.

## Prerequisites

- Docker or Docker Compose installed and running (`docker info` succeeds).
- Node.js 18+ with the `@clickhouse/client` package for the seed/test scripts.
- A local project directory you can Write files into. No cloud account or
  network access is required — everything runs on `localhost`.

## Authentication

This is a **local dev** setup with no external ClickHouse Cloud service. The
container's credentials are declared inline in `docker-compose.yml`
(`CLICKHOUSE_USER: default`, `CLICKHOUSE_PASSWORD: dev_password`) and consumed by
the client via env vars (`CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`,
`CLICKHOUSE_HOST`, `CLICKHOUSE_DATABASE`). Keep real per-developer overrides in a
git-ignored `.env.local`; commit only a `.env.example`. Never reuse
`dev_password` outside local development.

## Instructions

Follow the seven-step build. The lean skeleton is below; the
[full walkthrough](references/implementation.md) carries the complete file
contents for every step.

1. **Docker Compose setup** — Write a `docker-compose.yml` exposing `8123`
   (HTTP) and `9000` (native TCP), mounting `./init-db` for auto-migration and a
   named volume for persistence:

   ```yaml
   services:
     clickhouse:
       image: clickhouse/clickhouse-server:latest
       ports: ["8123:8123", "9000:9000"]
       volumes:
         - clickhouse-data:/var/lib/clickhouse
         - ./init-db:/docker-entrypoint-initdb.d
       environment:
         CLICKHOUSE_PASSWORD: dev_password
         CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
   volumes:
     clickhouse-data:
   ```

   Then `docker compose up -d` and verify with
   `curl http://localhost:8123/ping` → `Ok.`

2. **Init script** — Write `init-db/001-schema.sql` with your
   `CREATE DATABASE` / `CREATE TABLE ... ENGINE = MergeTree()` DDL. ClickHouse
   auto-runs it on the container's first start.
3. **Seed data** — Write `scripts/seed.ts` that batch-inserts synthetic rows via
   `client.insert({ format: 'JSONEachRow' })`.
4. **Project structure** — lay out `init-db/`, `scripts/`, `src/`, `tests/`, and
   the `.env.local` / `.env.example` pair.
5. **Client singleton** — Write `src/db.ts` exposing a memoized `getClient()`
   that reads connection settings from env vars with `localhost` fallbacks.
6. **Integration testing** — Write a vitest `tests/setup.ts` that TRUNCATEs
   tables in `beforeEach` and closes the client in `afterAll`, then write
   per-feature test files.
7. **Package scripts** — Edit `package.json` to add `db:up`, `db:down`,
   `db:reset`, `db:seed`, `db:shell`, and `test` scripts.

Read the [full walkthrough](references/implementation.md) for the exact,
copy-pasteable contents of each file.

## Output

Running this skill produces a working local ClickHouse dev loop:

- A running `clickhouse-server` container reachable at `http://localhost:8123`
  (HTTP) and `localhost:9000` (native), answering `curl .../ping` with `Ok.`
- An auto-created `app` database and schema from `init-db/001-schema.sql`.
- Seedable data via `npm run db:seed` (default: 1000 synthetic events).
- A green vitest integration suite that inserts and queries against the live
  container, resetting table state between tests.
- One-command lifecycle scripts (`db:up`, `db:down`, `db:reset`, `db:seed`,
  `db:shell`, `test`) wired into `package.json`.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused :8123` | Container not running | `docker compose up -d` |
| `READONLY` | User lacks write perms | Set `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` |
| `Too many parts` | Tiny frequent inserts | Batch inserts or increase `parts_to_throw_insert` |
| `Memory limit exceeded` | Large query on small container | Add `--memory 4g` to Docker |

## Examples

Bring the stack up, seed it, and confirm the rows landed:

```bash
docker compose up -d
curl http://localhost:8123/ping                 # → "Ok.\n"
npm run db:seed                                   # seeds 1000 events
curl 'http://localhost:8123/?query=SELECT+count()+FROM+app.events'   # → 1000
```

Open an interactive SQL shell:

```bash
docker exec -it <container> clickhouse-client --password dev_password
```

See [more examples](references/examples.md) — server-state inspection, HTTP
queries, environment reset, and a passing integration-test run.

## Resources

- [Full implementation walkthrough](references/implementation.md) — all seven
  build steps with complete file contents.
- [Examples](references/examples.md) — cold-start, shell, HTTP query, reset, and
  test-run recipes.
- [ClickHouse Docker Image](https://hub.docker.com/r/clickhouse/clickhouse-server)
- [clickhouse-client CLI](https://clickhouse.com/docs/interfaces/cli)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

Once the local loop is green, see the `clickhouse-sdk-patterns` skill for
production-ready client patterns (connection pooling, retries, typed query
helpers, and async inserts) that build on the `getClient()` singleton above.
