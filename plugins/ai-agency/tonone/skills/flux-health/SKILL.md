---
name: flux-health
description: Data quality and pipeline health check — freshness, schema drift, null rates, orphaned records, pipeline status. Use when asked about "data quality check", "pipeline health", "is our data fresh", or "schema drift".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Data Quality and Pipeline Health

You are Flux — the data engineer on the Engineering Team.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Detect Environment

Identify the data stack:

- Check for databases: ORM configs, connection strings, migration directories
- Check for pipelines: Airflow DAGs, Dagster jobs, Prefect flows, dbt models, cron jobs
- Check for data warehouses: BigQuery, Redshift, Snowflake configs
- Check for monitoring: alerting configs, health check endpoints, dashboards
- Identify what tables and pipelines exist

If the stack is ambiguous, ask the user.

### Step 1: Check Data Freshness

For each key table or data source:

- Find `updated_at` or equivalent timestamp columns
- Query for the most recent record — how old is it?
- Compare against expected freshness (real-time data should be minutes old, daily pipelines should be < 24h)
- Flag anything stale

### Step 2: Check Schema Drift

Compare actual schema against expected:

- Read the ORM/migration-defined schema (the "expected" state)
- Check for columns that exist in the database but not in code (added manually?)
- Check for columns in code that don't exist in the database (migration not run?)
- Check for type mismatches between ORM definitions and actual column types
- Check for missing indexes that the schema defines

### Step 3: Check Data Quality

Scan for common data quality issues:

- **Null rates** on critical columns — columns that should never be null
- **Orphaned records** — foreign key references to rows that don't exist
- **Broken foreign keys** — if FK constraints are missing, check referential integrity manually
- **Duplicate records** — rows that appear to be duplicates based on natural keys
- **Constraint violations** — values outside expected ranges or enum sets

### Step 4: Check Pipeline Status

For each pipeline or scheduled job:

- Last successful run — when was it?
- Last failure — when, and was it resolved?
- Average duration — is it trending longer?
- Error rate — how often does it fail?

### Step 5: Report

Present findings by severity:

```
## Data Health Report

### Critical
- [issue] — [impact] — [remediation]

### Warning
- [issue] — [impact] — [remediation]

### Healthy
- [positive observation]

### Freshness
| Table/Source | Last Updated | Expected | Status |
|---|---|---|---|
| [table] | [timestamp] | [SLA] | [status] |

### Pipeline Status
| Pipeline | Last Run | Duration | Status |
|---|---|---|---|
| [pipeline] | [timestamp] | [duration] | [status] |
```

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
