---
name: clari-core-workflow-a
description: |
  Build a Clari forecast export pipeline to your data warehouse.
  Use when exporting forecast calls, quota data, and CRM totals
  from Clari to Snowflake, BigQuery, or a local database.
  Trigger with phrases like "clari forecast export", "clari data pipeline",
  "clari to snowflake", "clari to bigquery", "export clari data".
allowed-tools: Read, Write, Edit, Bash(python3:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Core Workflow: Forecast Export Pipeline

## Overview

Primary workflow: build an automated pipeline that exports forecast submissions, quota, adjustments, and CRM data from Clari to your data warehouse. Supports Snowflake, BigQuery, and PostgreSQL as targets.

## Prerequisites

- Completed `clari-install-auth` and `clari-sdk-patterns` setup
- Target database or data warehouse with write access
- Python 3.10+ with `requests` and your DB driver

## Instructions

### Step 1: Define Export Configuration

```python
# config.py
from dataclasses import dataclass

@dataclass
class ExportConfig:
    forecast_name: str          # From Clari forecast list
    time_periods: list[str]     # e.g., ["2026_Q1", "2025_Q4"]
    export_types: list[str] = None
    currency: str = "USD"
    include_historical: bool = True

    def __post_init__(self):
        if self.export_types is None:
            self.export_types = [
                "forecast",           # Submitted forecast call
                "forecast_updated",   # Updated forecast history
                "quota",              # Quota values
                "adjustment",         # Manager adjustments
                "crm_total",          # Total CRM pipeline
                "crm_closed",         # Closed-won CRM amounts
            ]
```

### Step 2: Build the Export Pipeline

```python
# export_pipeline.py
from clari_client import ClariClient
from config import ExportConfig
import json
from datetime import datetime

def run_export(config: ExportConfig) -> list[dict]:
    client = ClariClient()
    all_entries = []

    for period in config.time_periods:
        print(f"Exporting {config.forecast_name} for {period}...")

        data = client.export_and_download(
            forecast_name=config.forecast_name,
            time_period=period,
        )

        entries = data.get("entries", [])
        for entry in entries:
            entry["_exported_at"] = datetime.utcnow().isoformat()
            entry["_forecast_name"] = config.forecast_name

        all_entries.extend(entries)
        print(f"  {len(entries)} records exported")

    return all_entries

def transform_forecast_data(entries: list[dict]) -> dict:
    total_forecast = sum(e.get("forecastAmount", 0) for e in entries)
    total_quota = sum(e.get("quotaAmount", 0) for e in entries)
    total_closed = sum(e.get("crmClosed", 0) for e in entries)

    return {
        "total_forecast": total_forecast,
        "total_quota": total_quota,
        "total_closed": total_closed,
        "attainment_percent": (total_closed / total_quota * 100) if total_quota else 0,
        "coverage_ratio": (total_forecast / total_quota) if total_quota else 0,
        "rep_count": len(entries),
        "reps": entries,
    }
```

### Step 3: Load to Snowflake

```python
# load_snowflake.py
import snowflake.connector

def load_to_snowflake(entries: list[dict], table: str = "CLARI_FORECASTS"):
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database="REVENUE_DATA",
        schema="CLARI",
    )

    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            owner_name VARCHAR,
            owner_email VARCHAR,
            forecast_amount FLOAT,
            quota_amount FLOAT,
            crm_total FLOAT,
            crm_closed FLOAT,
            adjustment_amount FLOAT,
            time_period VARCHAR,
            exported_at TIMESTAMP,
            forecast_name VARCHAR
        )
    """)

    for entry in entries:
        cursor.execute(f"""
            INSERT INTO {table} VALUES (
                %(ownerName)s, %(ownerEmail)s, %(forecastAmount)s,
                %(quotaAmount)s, %(crmTotal)s, %(crmClosed)s,
                %(adjustmentAmount)s, %(timePeriod)s,
                %(_exported_at)s, %(_forecast_name)s
            )
        """, entry)

    conn.commit()
    print(f"Loaded {len(entries)} records to {table}")
```

### Step 4: Schedule with Cron or Airflow

```python
# Run daily export
if __name__ == "__main__":
    config = ExportConfig(
        forecast_name="company_forecast",
        time_periods=["2026_Q1"],
    )
    entries = run_export(config)
    summary = transform_forecast_data(entries)
    print(f"Pipeline complete: {summary['rep_count']} reps, "
          f"${summary['total_forecast']:,.0f} forecast, "
          f"{summary['attainment_percent']:.1f}% attainment")
    load_to_snowflake(entries)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Empty entries | No submitted forecasts for period | Verify period has data in Clari UI |
| Job timeout | Large export | Increase `max_poll_attempts` |
| Snowflake auth error | Wrong credentials | Check env vars |
| Duplicate records | Re-run without dedup | Add upsert logic with `MERGE` |

## Resources

- [Clari Export API](https://developer.clari.com/documentation/external_spec)
- [Snowflake Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector)

## Next Steps

For pipeline analytics and deal inspection, see `clari-core-workflow-b`.
