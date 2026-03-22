---
name: clari-core-workflow-b
description: |
  Build Clari revenue analytics: pipeline coverage, forecast accuracy,
  and rep performance dashboards from exported data.
  Use when analyzing forecast accuracy, building attainment reports,
  or creating executive revenue dashboards.
  Trigger with phrases like "clari analytics", "clari dashboard",
  "clari forecast accuracy", "clari pipeline coverage".
allowed-tools: Read, Write, Edit, Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Core Workflow: Revenue Analytics

## Overview

Build revenue analytics from Clari export data: forecast accuracy tracking, pipeline coverage analysis, rep performance dashboards, and forecast call change detection.

## Prerequisites

- Completed `clari-core-workflow-a` (export pipeline)
- Historical forecast exports for accuracy tracking
- Pandas/SQL for data analysis

## Instructions

### Step 1: Forecast Accuracy Analysis

```python
import pandas as pd

def calculate_forecast_accuracy(
    forecasts: list[dict], actuals: list[dict]
) -> pd.DataFrame:
    df_forecast = pd.DataFrame(forecasts)
    df_actual = pd.DataFrame(actuals)

    merged = df_forecast.merge(
        df_actual[["ownerEmail", "crmClosed"]],
        on="ownerEmail",
        suffixes=("_forecast", "_actual"),
    )

    merged["accuracy_pct"] = (
        1 - abs(merged["forecastAmount"] - merged["crmClosed_actual"])
        / merged["forecastAmount"]
    ) * 100

    merged["variance"] = merged["crmClosed_actual"] - merged["forecastAmount"]

    return merged[["ownerName", "forecastAmount", "crmClosed_actual",
                    "accuracy_pct", "variance"]].sort_values("accuracy_pct")
```

### Step 2: Pipeline Coverage Report

```python
def pipeline_coverage_report(entries: list[dict]) -> dict:
    df = pd.DataFrame(entries)

    return {
        "total_pipeline": df["crmTotal"].sum(),
        "total_closed": df["crmClosed"].sum(),
        "total_quota": df["quotaAmount"].sum(),
        "total_forecast": df["forecastAmount"].sum(),
        "coverage_ratio": df["crmTotal"].sum() / df["quotaAmount"].sum()
            if df["quotaAmount"].sum() > 0 else 0,
        "close_rate": df["crmClosed"].sum() / df["crmTotal"].sum()
            if df["crmTotal"].sum() > 0 else 0,
        "attainment_pct": df["crmClosed"].sum() / df["quotaAmount"].sum() * 100
            if df["quotaAmount"].sum() > 0 else 0,
        "at_risk_reps": len(df[df["forecastAmount"] < df["quotaAmount"] * 0.7]),
        "on_track_reps": len(df[df["forecastAmount"] >= df["quotaAmount"] * 0.9]),
    }
```

### Step 3: Forecast Change Detection

```python
def detect_forecast_changes(
    current: list[dict], previous: list[dict], threshold_pct: float = 10.0
) -> list[dict]:
    curr = {e["ownerEmail"]: e for e in current}
    prev = {e["ownerEmail"]: e for e in previous}

    changes = []
    for email, curr_entry in curr.items():
        prev_entry = prev.get(email)
        if not prev_entry:
            continue

        prev_amount = prev_entry["forecastAmount"]
        curr_amount = curr_entry["forecastAmount"]

        if prev_amount == 0:
            continue

        change_pct = ((curr_amount - prev_amount) / prev_amount) * 100

        if abs(change_pct) >= threshold_pct:
            changes.append({
                "rep": curr_entry["ownerName"],
                "previous_forecast": prev_amount,
                "current_forecast": curr_amount,
                "change_pct": round(change_pct, 1),
                "direction": "up" if change_pct > 0 else "down",
            })

    return sorted(changes, key=lambda x: abs(x["change_pct"]), reverse=True)
```

### Step 4: SQL Analytics Queries

```sql
-- Forecast accuracy by quarter
SELECT
    time_period,
    owner_name,
    forecast_amount,
    crm_closed AS actual_closed,
    ROUND((1 - ABS(forecast_amount - crm_closed) / NULLIF(forecast_amount, 0)) * 100, 1) AS accuracy_pct
FROM clari_forecasts
WHERE time_period = '2025_Q4'
ORDER BY accuracy_pct DESC;

-- Pipeline coverage trend
SELECT
    time_period,
    SUM(crm_total) / NULLIF(SUM(quota_amount), 0) AS coverage_ratio,
    SUM(crm_closed) / NULLIF(SUM(quota_amount), 0) AS attainment
FROM clari_forecasts
GROUP BY time_period
ORDER BY time_period;
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Division by zero | Zero quota or forecast | Add `NULLIF` guards |
| Missing previous period | First export run | Skip change detection |
| Accuracy > 100% | Overachievement | Cap at 100% or allow for analysis |
| Stale data | Export not refreshed | Run `clari-core-workflow-a` first |

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

## Next Steps

For error troubleshooting, see `clari-common-errors`.
