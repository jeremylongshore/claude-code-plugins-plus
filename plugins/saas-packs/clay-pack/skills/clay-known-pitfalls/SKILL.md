---
name: clay-known-pitfalls
description: |
  Identify and avoid Clay anti-patterns and common integration mistakes.
  Use when reviewing Clay code for issues, onboarding new developers,
  or auditing existing Clay integrations for best practices violations.
  Trigger with phrases like "clay mistakes", "clay anti-patterns",
  "clay pitfalls", "clay what not to do", "clay code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Known Pitfalls

## Overview
Real gotchas when using Clay's data enrichment platform. Clay's credit-based waterfall enrichment model, table-based workflow, and multi-provider data sourcing create specific failure modes.

## Prerequisites
- Clay account with API access
- Understanding of waterfall enrichment logic
- Familiarity with Clay's credit billing model

## Instructions

### Step 1: Prevent Credit Burn from Waterfall Misconfiguration

Clay's waterfall enrichment tries multiple providers sequentially. Misconfigured waterfalls burn credits on every provider even after finding valid data.

```
# BAD: waterfall with no stop conditions
Enrichment Column: "Company Revenue"
  Provider 1: Clearbit -> found data -> 1 credit
  Provider 2: ZoomInfo -> also runs -> 1 credit (wasted)
  Provider 3: Apollo -> also runs -> 1 credit (wasted)
  Total: 3 credits for 1 data point

# GOOD: configure waterfall to stop on first match
Enrichment Column: "Company Revenue"
  Provider 1: Clearbit -> found data -> STOP
  Total: 1 credit
  
# In Clay UI: enable "Stop on first result" for each waterfall step
# In API: set fallback_only=true on subsequent providers
```

### Step 2: Avoid Blank Row Processing

Clay charges credits per row processed, even if the input data is blank or invalid.

```python
import requests

# BAD: sending rows with missing emails
rows = [
    {"email": "valid@company.com"},
    {"email": ""},           # blank = wasted credit
    {"email": "not-email"},  # invalid = wasted credit
]
# All 3 rows consume credits

# GOOD: filter before sending to Clay
valid_rows = [
    row for row in rows
    if row.get("email") and "@" in row["email"]
]
response = requests.post(
    "https://api.clay.com/v1/tables/{table_id}/rows",
    json={"rows": valid_rows},
    headers={"Authorization": f"Bearer {api_key}"}
)
```

### Step 3: Handle CSV Import Column Mapping

Clay auto-maps CSV columns by name. Slight naming differences cause silent data mismatches.

```
# BAD: CSV has "Company Name", Clay table expects "company_name"
# Import succeeds but column maps to wrong field or creates duplicate

# GOOD: match CSV headers exactly to Clay table columns
# Before import, normalize headers:
import pandas as pd
df = pd.read_csv("leads.csv")
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
df.to_csv("leads_normalized.csv", index=False)
```

### Step 4: Rate Limit Clay Table API Calls

Clay's API has per-minute rate limits. Bulk operations without throttling get 429 errors.

```python
import time

# BAD: blast all rows at once
for row in thousands_of_rows:
    requests.post(f"{clay_api}/tables/{table_id}/rows", json=row)

# GOOD: batch with rate limiting
BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 2  # seconds

for i in range(0, len(rows), BATCH_SIZE):
    batch = rows[i:i + BATCH_SIZE]
    response = requests.post(
        f"{clay_api}/tables/{table_id}/rows",
        json={"rows": batch},
        headers=headers
    )
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 30))
        time.sleep(retry_after)
    else:
        time.sleep(DELAY_BETWEEN_BATCHES)
```

### Step 5: Don't Rely on Real-Time Enrichment Results

Clay enrichments run asynchronously. Polling for results immediately after row creation returns empty fields.

```python
# BAD: read immediately after write
requests.post(f"{clay_api}/tables/{table_id}/rows", json=row_data)
result = requests.get(f"{clay_api}/tables/{table_id}/rows/{row_id}")
print(result.json()["enriched_field"])  # None -- enrichment hasn't run

# GOOD: poll with backoff or use webhooks
import time
for attempt in range(10):
    result = requests.get(f"{clay_api}/tables/{table_id}/rows/{row_id}")
    if result.json().get("enriched_field"):
        break
    time.sleep(min(2 ** attempt, 30))
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credits burning fast | Waterfall not stopping on match | Enable "stop on first result" |
| Blank enrichment results | Input rows have invalid data | Pre-validate before sending |
| Column mapping errors | CSV header mismatch | Normalize headers before import |
| 429 rate limit errors | Too many API calls/minute | Batch requests with delays |
| Empty enrichment fields | Reading before enrichment completes | Poll with backoff or use webhooks |

## Examples

### Credit Usage Monitoring
```python
usage = requests.get(
    f"{clay_api}/v1/usage",
    headers=headers
).json()
remaining = usage["credits_remaining"]
if remaining < 100:
    print(f"WARNING: Only {remaining} credits left")
```

## Resources
- [Clay API Docs](https://docs.clay.com/api)
- [Clay Waterfall Guide](https://docs.clay.com/enrichment/waterfall)
