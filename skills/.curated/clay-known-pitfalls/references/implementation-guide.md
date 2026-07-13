# Clay Known Pitfalls — Implementation Guide

## Waterfall Credit Burn Prevention

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

## Blank Row Filtering

```python
import requests

# BAD: sending rows with missing emails
rows = [
    {"email": "valid@company.com"},
    {"email": ""},           # blank = wasted credit
    {"email": "not-email"},  # invalid = wasted credit
]

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

## CSV Header Normalization

```python
# BAD: CSV has "Company Name", Clay table expects "company_name"
# Import succeeds but column maps to wrong field or creates duplicate

# GOOD: normalize headers before import
import pandas as pd
df = pd.read_csv("leads.csv")
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
df.to_csv("leads_normalized.csv", index=False)
```

## Rate-Limited Batch Processing

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

## Async Enrichment Polling

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

## Credit Usage Monitoring

```python
usage = requests.get(
    f"{clay_api}/v1/usage",
    headers=headers
).json()
remaining = usage["credits_remaining"]
if remaining < 100:
    print(f"WARNING: Only {remaining} credits left")
```
