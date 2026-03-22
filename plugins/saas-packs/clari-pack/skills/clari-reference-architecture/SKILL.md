---
name: clari-reference-architecture
description: |
  Reference architecture for Clari revenue intelligence integrations.
  Use when designing a forecast data platform, planning Clari integration
  architecture, or establishing team patterns for revenue analytics.
  Trigger with phrases like "clari architecture", "clari data platform",
  "clari integration design", "clari best practices".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Reference Architecture

## Overview

Production architecture for Clari revenue intelligence integrations: export pipeline design, data warehouse schema, analytics layer, and alerting.

## Architecture Diagram

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Clari App   │     │  Clari Export    │     │  Data Warehouse  │
│  (SaaS)      │────▶│  API (v4)       │────▶│  (Snowflake/BQ)  │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                       │
                     ┌─────────────────┐     ┌────────▼─────────┐
                     │  Change         │     │  Analytics /     │
                     │  Detection      │────▶│  Dashboard       │
                     └─────────────────┘     │  (Looker/Metabase)│
                            │                └──────────────────┘
                     ┌──────▼──────────┐
                     │  Alerts         │
                     │  (Slack/Email)  │
                     └─────────────────┘
```

## Project Structure

```
clari-data-platform/
├── src/
│   ├── clari_client.py         # API client wrapper
│   ├── export_pipeline.py      # ETL pipeline
│   ├── change_detector.py      # Forecast change tracking
│   ├── models.py               # Data models
│   └── config.py               # Environment config
├── dags/
│   └── clari_export_dag.py     # Airflow DAG
├── sql/
│   ├── schema.sql              # Warehouse table definitions
│   ├── merge.sql               # Upsert logic
│   └── analytics/
│       ├── forecast_accuracy.sql
│       ├── pipeline_coverage.sql
│       └── rep_performance.sql
├── tests/
│   ├── fixtures/               # Sample API responses
│   ├── test_pipeline.py
│   └── test_change_detector.py
├── scripts/
│   ├── run_export.sh
│   └── validate_schema.py
└── monitoring/
    ├── alerts.yaml             # Alert rules
    └── dashboard.json          # Grafana/Looker config
```

## Data Warehouse Schema

```sql
-- Core tables
CREATE TABLE clari_forecasts (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    owner_name VARCHAR NOT NULL,
    owner_email VARCHAR NOT NULL,
    forecast_amount DECIMAL(15,2),
    quota_amount DECIMAL(15,2),
    crm_total DECIMAL(15,2),
    crm_closed DECIMAL(15,2),
    adjustment_amount DECIMAL(15,2),
    time_period VARCHAR NOT NULL,
    forecast_name VARCHAR NOT NULL,
    exported_at TIMESTAMP NOT NULL,
    PRIMARY KEY (owner_email, time_period, forecast_name, exported_at)
);

-- Change tracking
CREATE TABLE clari_forecast_changes (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    owner_email VARCHAR NOT NULL,
    time_period VARCHAR NOT NULL,
    previous_amount DECIMAL(15,2),
    current_amount DECIMAL(15,2),
    change_pct DECIMAL(5,2),
    detected_at TIMESTAMP NOT NULL
);

-- Analytics views
CREATE VIEW v_forecast_accuracy AS
SELECT
    time_period,
    owner_name,
    forecast_amount,
    crm_closed AS actual_closed,
    ROUND((1 - ABS(forecast_amount - crm_closed) / NULLIF(forecast_amount, 0)) * 100, 1) AS accuracy_pct
FROM clari_forecasts
WHERE exported_at = (SELECT MAX(exported_at) FROM clari_forecasts f2 WHERE f2.time_period = clari_forecasts.time_period);
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Export frequency | Daily | Balances freshness vs API load |
| Data format | JSON export | Structured, easy to parse |
| Pipeline orchestration | Airflow | Retry, monitoring, DAG visualization |
| Change detection | Snapshot comparison | Clari has no real-time webhooks |
| Warehouse | Snowflake | SQL analytics, dbt compatibility |

## Resources

- [Clari Developer Portal](https://developer.clari.com)
- [Clari API Reference](https://developer.clari.com/documentation/external_spec)
- [Snowflake Documentation](https://docs.snowflake.com)

## Next Steps

This completes the Clari skill pack. Start with `clari-install-auth` for new integrations.
