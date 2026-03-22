---
name: hex-reference-architecture
description: |
  Implement Hex reference architecture with best-practice project layout.
  Use when designing new Hex integrations, reviewing project structure,
  or establishing architecture standards for Hex applications.
  Trigger with phrases like "hex architecture", "hex best practices",
  "hex project structure", "how to organize hex", "hex layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
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

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
- [Airflow Provider](https://github.com/hex-inc/airflow-provider-hex)
- [Orchestration Blog](https://hex.tech/blog/announcing-orchestration-public-api/)
