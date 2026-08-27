---
name: hex-reference-architecture
description: 'Implement Hex reference architecture with best-practice project layout.

  Use when designing new Hex integrations, reviewing project structure,

  or establishing architecture standards for Hex applications.

  Trigger with phrases like "hex architecture", "hex best practices",

  "hex project structure", "how to organize hex", "hex layout".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex Reference Architecture

## Architecture

```
┌────────────────────────────────────────┐
│          Orchestration Layer            │
│  (Airflow, Dagster, GitHub Actions,    │
│   Cron, Custom API)                    │
├────────────────────────────────────────┤
│           Hex API Client               │
│  (Run, Poll, Cancel, List)             │
├────────────────────────────────────────┤
│            Hex Platform                │
│  ┌──────────┐  ┌───────────────────┐  │
│  │ Projects  │  │ Data Connections  │  │
│  │ (SQL,     │  │ (Snowflake,      │  │
│  │  Python,  │  │  BigQuery,       │  │
│  │  R)       │  │  Postgres, etc.) │  │
│  └──────────┘  └───────────────────┘  │
└────────────────────────────────────────┘
```

## Project Structure

```
hex-orchestrator/
├── src/hex/
│   ├── client.ts         # API client
│   ├── orchestrator.ts   # Pipeline runner
│   ├── scheduler.ts      # Cron-based triggers
│   └── types.ts          # TypeScript interfaces
├── src/notify/
│   └── slack.ts          # Completion notifications
├── tests/
├── config/
│   └── pipelines.json    # Pipeline definitions
└── .env.example
```

## Integration Patterns

| Pattern | When | Tool |
|---------|------|------|
| CI-triggered refresh | On deploy | GitHub Actions |
| Scheduled pipeline | Daily/weekly reports | Cron, Airflow |
| On-demand run | User-triggered analysis | API endpoint |
| Orchestrated pipeline | Multi-step ETL | Airflow, Dagster |

## Overview

This architecture separates project triggers, parameter validation, scoped execution, bounded orchestration, aggregate observability, and cancellation/rollback. Workspace data remains inside approved project boundaries and never becomes architectural telemetry.

## Prerequisites

- A project/data owner for each source, environment allowlist, secret manager, and owner for every execution edge.
- Separate sandbox/staging/production configuration plus rollback for project, schedule, queue, and client controls.

## Instructions

1. Map every trigger-to-project edge with owner, data class, allowed parameters, authorization scope, retry behavior, observability, and rollback.
2. Start with a sandbox project and fail closed on unknown project, parameter schema, destination, or response shape.
3. Make asynchronous execution idempotent and bounded; quarantine uncertainty rather than resubmitting or exporting output for debugging.
4. Canary one project with aggregate signals before promotion and retain the prior revision.
5. Re-evaluate controls whenever credentials, project ownership, schedules, or parameters change.

## Output

Produce an architecture record with owners, opaque project IDs, policy revisions, idempotency/retry behavior, observability, test evidence, and rollback revision. Exclude SQL, output, credentials, and identities.

## Error Handling

Stop on unknown scope/destination, failed redaction, non-idempotent retry, or authorization drift. Quarantine the event and restore the prior controlled path instead of adding a broad fallback.

## Examples

`source=scheduled-sandbox; project=proj-sandbox-12; params=r4; trigger=approved; probe=pass; rollback=arch-r17` is a reviewable architecture receipt.

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
- [Airflow Provider](https://github.com/hex-inc/airflow-provider-hex)
- [Orchestration Blog](https://hex.tech/blog/announcing-orchestration-public-api/)
