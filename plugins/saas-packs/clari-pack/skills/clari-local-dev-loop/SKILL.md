---
name: clari-local-dev-loop
description: |
  Set up local development for Clari API integrations with mock data.
  Use when building forecast dashboards, testing export pipelines,
  or iterating on Clari data transformations locally.
  Trigger with phrases like "clari dev setup", "clari local testing",
  "develop with clari", "clari mock data".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Local Dev Loop

## Overview

Local development workflow for Clari integrations: mock forecast data for offline testing, schedule recurring exports, and build data transformation pipelines.

## Prerequisites

- Completed `clari-install-auth` setup
- Python 3.10+ or Node.js 18+
- Local database or data warehouse access for testing

## Instructions

### Step 1: Project Structure

```
clari-integration/
├── src/
│   ├── clari_client.py       # API client wrapper
│   ├── export_pipeline.py    # Export and transform pipeline
│   ├── models.py             # Data models for forecast data
│   └── config.py             # Environment config
├── tests/
│   ├── fixtures/
│   │   ├── forecast_export.json    # Sample export response
│   │   └── job_status.json         # Sample job status
│   └── test_pipeline.py
├── .env.local                # Dev credentials (git-ignored)
├── .env.example
└── requirements.txt
```

### Step 2: Mock Forecast Data for Testing

```python
# tests/fixtures/forecast_export.json
MOCK_FORECAST = {
    "entries": [
        {
            "ownerName": "Jane Smith",
            "ownerEmail": "jane@example.com",
            "forecastAmount": 250000,
            "quotaAmount": 300000,
            "crmTotal": 180000,
            "crmClosed": 120000,
            "adjustmentAmount": 15000,
            "timePeriod": "2026_Q1"
        },
        {
            "ownerName": "Bob Johnson",
            "ownerEmail": "bob@example.com",
            "forecastAmount": 180000,
            "quotaAmount": 250000,
            "crmTotal": 140000,
            "crmClosed": 90000,
            "adjustmentAmount": 0,
            "timePeriod": "2026_Q1"
        }
    ]
}
```

### Step 3: Test Pipeline Without API Calls

```python
# tests/test_pipeline.py
import pytest
from src.export_pipeline import transform_forecast_data

def test_forecast_aggregation():
    data = MOCK_FORECAST
    result = transform_forecast_data(data)
    assert result["total_forecast"] == 430000
    assert result["total_quota"] == 550000
    assert result["attainment_percent"] == pytest.approx(78.2, rel=0.1)
    assert len(result["reps"]) == 2

def test_handles_empty_export():
    result = transform_forecast_data({"entries": []})
    assert result["total_forecast"] == 0
```

### Step 4: Development Run Script

```bash
#!/bin/bash
# scripts/dev-export.sh
set -euo pipefail

source .env.local

echo "=== Clari Dev Export ==="
python3 src/export_pipeline.py \
  --forecast "company_forecast" \
  --period "2026_Q1" \
  --format json \
  --output ./data/latest-export.json

echo "Export saved to ./data/latest-export.json"
echo "Records: $(jq '.entries | length' ./data/latest-export.json)"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Import error | Missing dependency | `pip install -r requirements.txt` |
| Empty export | Wrong time period | Use a period with submitted forecasts |
| Mock data stale | Schema changed | Re-download a sample from API |
| `.env.local` not loading | Missing dotenv | `pip install python-dotenv` |

## Resources

- [Clari API Reference](https://developer.clari.com/documentation/external_spec)
- [pytest Documentation](https://docs.pytest.org)

## Next Steps

See `clari-sdk-patterns` for production-ready API wrappers.
