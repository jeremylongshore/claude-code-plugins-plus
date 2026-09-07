---
name: clickhouse-ci-integration
description: |
  Run ClickHouse integration tests in CI with GitHub Actions and Docker
  containers. Use when setting up automated testing against a real ClickHouse
  instance, configuring CI pipelines, or implementing schema validation in CI.
  Trigger with "clickhouse CI", "clickhouse GitHub Actions", "clickhouse
  integration tests", "test clickhouse in CI", "clickhouse automated testing".
allowed-tools: Read, Write, Edit, Bash(gh:*)
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
# ClickHouse CI Integration

## Overview

Run integration tests against a real ClickHouse server in GitHub Actions using
Docker service containers. No mocks needed for schema and query validation —
the workflow spins up `clickhouse/clickhouse-server`, applies your schema, and
runs unit + integration tests against the live instance.

This skill produces four artifacts: a GitHub Actions workflow, a shared test
setup, integration/schema test files, and the `package.json` scripts that tie
them together. SKILL.md gives you the workflow skeleton and the moving parts;
the full copy-paste-ready test harness lives in
[references/implementation.md](references/implementation.md) and
[references/examples.md](references/examples.md).

## Prerequisites

- GitHub repository with Actions enabled
- `@clickhouse/client` in project dependencies
- Test suite (vitest or jest)

## Instructions

Read any existing `.github/workflows/` and `package.json` first, then create or
edit the four artifacts below.

### Step 1: Add the workflow with a ClickHouse service container

Create `.github/workflows/clickhouse-tests.yml`. The core is a `services.clickhouse`
block with a health check plus a schema-apply step before tests run:

```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports: ["8123:8123", "9000:9000"]
    options: >-
      --health-cmd "wget --no-verbose --tries=1 --spider http://localhost:8123/ping || exit 1"
      --health-interval 10s --health-timeout 5s --health-retries 5
```

Full workflow (checkout, Node setup, `npm ci`, schema-apply loop, unit +
integration steps, and credential handling): [references/implementation.md](references/implementation.md) Step 1.

### Step 2: Wire the shared test setup

Add `tests/setup-integration.ts` — it creates a `@clickhouse/client`, pings on
`beforeAll` to fail fast if the service is unreachable, `TRUNCATE`s between
tests, and closes on `afterAll`. See
[references/implementation.md](references/implementation.md) Step 2 for the file.

### Step 3: Write the integration and schema tests

Add `tests/events.integration.test.ts` (insert → aggregate → assert, plus
parameterized-query and empty-result cases) and
`tests/schema.integration.test.ts` (asserts column types + table engine via
`system.columns` / `system.tables`). Both files:
[references/examples.md](references/examples.md).

### Step 4: Add package scripts and (optionally) a version matrix

Edit `package.json` to add `test`, `test:integration`, and `test:ci` scripts.
To catch behavioral drift before a server upgrade, add a `strategy.matrix` over
several `clickhouse-version` values. Both:
[references/implementation.md](references/implementation.md) Steps 3–4.

## Output

Running this skill leaves the repository with:

- `.github/workflows/clickhouse-tests.yml` — CI job with a ClickHouse service container
- `tests/setup-integration.ts` — shared client + per-test cleanup
- `tests/events.integration.test.ts` — query/insert behavior tests
- `tests/schema.integration.test.ts` — column-type + engine assertions
- Updated `package.json` scripts (`test`, `test:integration`, `test:ci`)

On push/PR, the workflow reports pass/fail per job; with the matrix, one job per
ClickHouse version. Coverage and JUnit output are emitted for CI reporting.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Service not healthy | Slow container start | Increase `health-retries` |
| Schema not found | Init scripts not run | Run schema step before tests |
| Flaky test order | Shared state | Use `beforeEach` with TRUNCATE |
| Port conflict | Another process | Use random port mapping |

## Examples

Minimal integration-test shape — insert rows, aggregate, assert:

```typescript
await client.insert({ table: 'events', values: rows, format: 'JSONEachRow' });
const rs = await client.query({
  query: 'SELECT event_type, count() AS cnt FROM events GROUP BY event_type',
  format: 'JSONEachRow',
});
expect(await rs.json()).toHaveLength(2);
```

Full, runnable example files — the events integration suite (aggregation,
parameterized-query injection guard, empty-result handling) and the schema
validation suite (column types + `MergeTree` engine assertions) — are in
[references/examples.md](references/examples.md).

## Resources

- [GitHub Actions Service Containers](https://docs.github.com/en/actions/using-containerized-services)
- [ClickHouse Docker Image](https://hub.docker.com/r/clickhouse/clickhouse-server)
- [Vitest Documentation](https://vitest.dev/)
- [references/implementation.md](references/implementation.md) — full workflow, test setup, package scripts, version matrix
- [references/examples.md](references/examples.md) — complete integration + schema test files

## Next Steps

For deployment patterns, see the `clickhouse-deploy-integration` skill, which
covers migration ordering and production rollout once your CI suite is green.
