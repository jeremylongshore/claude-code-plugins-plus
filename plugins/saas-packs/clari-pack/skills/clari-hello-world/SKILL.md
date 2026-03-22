---
name: clari-hello-world
description: |
  Export your first Clari forecast and pipeline snapshot.
  Use when testing Clari API connectivity, pulling forecast data,
  or learning the export API structure.
  Trigger with phrases like "clari hello world", "clari first export",
  "clari test api", "clari forecast export".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Hello World

## Overview

First API calls against Clari: list available forecasts, export a forecast snapshot, and check export job status. The Clari Export API is the primary integration point for getting forecast, quota, and CRM data out of Clari.

## Prerequisites

- Completed `clari-install-auth` setup
- `CLARI_API_KEY` environment variable set
- At least one forecast configured in Clari

## Instructions

### Step 1: List Available Forecasts

```bash
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list \
  | jq '.forecasts[] | {forecastName, forecastId, timePeriods}'
```

### Step 2: Export a Forecast

```python
import requests
import json
import os
import time

api_key = os.environ["CLARI_API_KEY"]
headers = {"apikey": api_key, "Content-Type": "text/plain"}

# Replace with your forecast name from Step 1
forecast_name = "company_forecast"

payload = json.dumps({
    "timePeriod": "2026_Q1",
    "typesToExport": [
        "forecast",
        "quota",
        "forecast_updated",
        "adjustment",
        "crm_total",
        "crm_closed"
    ],
    "currency": "USD",
    "schedule": "NONE",
    "includeHistorical": False,
    "exportFormat": "JSON"
})

response = requests.post(
    f"https://api.clari.com/v4/export/forecast/{forecast_name}",
    headers=headers,
    data=payload,
)
response.raise_for_status()

job = response.json()
print(f"Export job started: {job['jobId']}")
print(f"Status: {job['status']}")
```

### Step 3: Check Export Job Status

```python
# Poll for job completion
job_id = job["jobId"]

while True:
    status_resp = requests.get(
        f"https://api.clari.com/v4/export/jobs/{job_id}",
        headers={"apikey": api_key},
    )
    status = status_resp.json()

    if status["status"] == "COMPLETED":
        print(f"Export ready: {status['downloadUrl']}")
        break
    elif status["status"] == "FAILED":
        print(f"Export failed: {status.get('error', 'Unknown')}")
        break

    print(f"Status: {status['status']}... waiting 5s")
    time.sleep(5)
```

### Step 4: Download and Parse Results

```python
if status["status"] == "COMPLETED":
    download = requests.get(status["downloadUrl"])
    forecast_data = download.json()

    # Print summary
    for entry in forecast_data.get("entries", [])[:5]:
        print(f"  Rep: {entry.get('ownerName')}")
        print(f"  Forecast: ${entry.get('forecastAmount', 0):,.0f}")
        print(f"  Quota: ${entry.get('quotaAmount', 0):,.0f}")
        print()
```

## Output

- List of forecasts with IDs and time periods
- Exported forecast data with rep-level calls
- Quota, adjustments, and CRM totals

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Bad API key | Regenerate token in Clari settings |
| No forecasts listed | Wrong org or no forecasts configured | Contact Clari admin |
| Job stays `PENDING` | Large export | Wait longer, check job status endpoint |
| `404` on forecast name | Name mismatch | Use exact name from list endpoint |

## Resources

- [Clari Export API](https://developer.clari.com/documentation/external_spec)
- [Clari Community - API Guide](https://community.clari.com/product-q-a-6/clari-api-all-you-need-to-know-556)

## Next Steps

Proceed to `clari-local-dev-loop` for development workflow setup.
