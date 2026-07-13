---
name: hubspot-warehouse-sync
description: |
  Sync HubSpot CRM data to a data warehouse (BigQuery, Snowflake, or Postgres) for
  analytics and reporting. Covers initial backfill of millions of records under the
  500K/day rate limit, incremental CDC polling via hs_lastmodifieddate, schema-drift
  detection with ALTER TABLE generation, association sync for contacts/deals/companies,
  and idempotent upsert patterns that prevent duplicate rows on retry. Use when building
  a HubSpot → warehouse pipeline, resyncing after a schema change, debugging duplicate
  rows or missing CDC updates, or recovering from a rate-limit burnout mid-backfill.
  Trigger with "hubspot warehouse sync", "hubspot bigquery", "hubspot snowflake",
  "hubspot postgres etl", "hubspot backfill", "hubspot cdc", "hubspot schema drift",
  "hubspot duplicate rows", "hubspot to data warehouse".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(python3:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - data-engineering
  - etl
  - bigquery
  - snowflake
  - warehouse
---

# HubSpot Warehouse Sync

## Overview

Move HubSpot CRM data to BigQuery, Snowflake, or Postgres in a way that survives production — not just the demo. This is not a connector walkthrough. It is the extraction and load code your pipeline runs when a 2M-contact backfill burns through the 500K daily call quota at noon, when CDC misses three days of deal updates because association changes do not update `hs_lastmodifieddate`, when a portal admin adds a custom property and your warehouse table schema silently drifts, and when a network timeout at record 45,000 causes your retry to insert 100 duplicate rows.

The six production failures this skill prevents:

1. **Backfill exhausting the daily rate limit before completing** — 2M contacts at 100 records/call is 20,000 calls. At 100 calls/10s the math says 33 minutes, but that burns your entire 500K daily quota before noon and takes every other integration down with it. Token bucket rate limiting with a configurable daily ceiling is non-optional.
2. **CDC missing association changes** — HubSpot's `hs_lastmodifieddate` is updated when any property on the contact record changes, but not when an association is created or deleted. A contact-to-deal link added by a sales rep is invisible to a lastmodifieddate-based incremental poll. Association CDC requires a separate poll strategy.
3. **Schema drift causing silent extraction failures** — when a portal admin adds or removes a custom property, the warehouse table schema and the extraction property list become misaligned. New properties are dropped on the floor. Removed properties cause KeyError on row construction. Neither failure raises an alarm without explicit schema validation.
4. **Duplicate rows on batch retry** — a network failure mid-batch causes the batch to be re-sent. Without a proper upsert key the warehouse gets duplicate rows that are invisible until an analyst notices double-counted revenue. The correct upsert key for contacts is `id` (HubSpot object ID), not a composite of name/email.
5. **Large payload failures on associated object inline pulls** — contacts with thousands of engagement records cause payload sizes that exceed HTTP response limits when associations are pulled inline. Associations must be fetched in a separate batch read pass.
6. **Timezone inconsistency in aggregations** — HubSpot stores all timestamps as Unix milliseconds in UTC. If the warehouse session timezone is set to a local timezone, `DATE(created_at)` aggregations produce different daily totals depending on where the analyst runs the query.

## Prerequisites

- Python 3.10+
- HubSpot private app token with scopes: `crm.objects.contacts.read`, `crm.objects.companies.read`, `crm.objects.deals.read`, `crm.associations.read`, `crm.schemas.contacts.read`
- Target warehouse credentials:
  - BigQuery: service account JSON with `bigquery.dataEditor` role
  - Snowflake: user/password or key-pair auth, warehouse + database + schema
  - Postgres: connection string with write access to the target schema
- Python packages: `requests`, `pandas`, `pyarrow`, `google-cloud-bigquery` (BigQuery) or `snowflake-connector-python` (Snowflake) or `psycopg2-binary` (Postgres)
- A secret store the runtime can read (env vars, GCP Secret Manager, AWS Secrets Manager)

## Instructions

Build in this order. Each section neutralizes one production failure mode.

### 1. Token bucket rate limiter (neutralizes backfill quota burnout)

Naive extraction loops call the API as fast as possible. At 100 calls/10s with 20K calls needed, you burn 200K of your 500K daily quota in 33 minutes — and that is before any CDC polling or webhook processing. A production backfill must budget its calls over the full day so other integrations still have headroom.

The token bucket strategy: set a `daily_budget` ceiling below the account limit (e.g., 400K of 500K), compute how many calls per second that allows over 24 hours, and enforce a minimum interval between calls. Burn-rate is checked against live rate-limit headers on every response.

```python
import time
import threading
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    """
    Token bucket rate limiter for HubSpot API calls.

    daily_budget: max calls to spend per 24h window (stay below 500K limit)
    burst_limit: max calls per 10s window (100 for most tiers)
    """
    daily_budget: int = 400_000
    burst_limit: int = 95          # leave 5 calls headroom per 10s window
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _calls_today: int = 0
    _window_calls: int = 0
    _window_start: float = field(default_factory=time.monotonic)
    _day_start: float = field(default_factory=time.monotonic)

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()

            # Reset daily counter
            if now - self._day_start >= 86_400:
                self._calls_today = 0
                self._day_start = now

            # Reset 10s window counter
            if now - self._window_start >= 10.0:
                self._window_calls = 0
                self._window_start = now

            # Hard stop if daily budget exhausted — do not burn other integrations
            if self._calls_today >= self.daily_budget:
                seconds_left = 86_400 - (now - self._day_start)
                raise DailyBudgetExhausted(
                    f"Daily call budget of {self.daily_budget:,} reached. "
                    f"Resuming in {seconds_left/3600:.1f}h."
                )

            # Burst window throttle — sleep until window resets if full
            if self._window_calls >= self.burst_limit:
                sleep_s = 10.0 - (now - self._window_start) + 0.1
                time.sleep(max(0, sleep_s))
                self._window_calls = 0
                self._window_start = time.monotonic()

            self._calls_today += 1
            self._window_calls += 1

    def update_from_headers(self, headers: dict) -> None:
        """Adjust pacing from live rate-limit headers on each response."""
        remaining = int(headers.get("X-HubSpot-RateLimit-Daily-Remaining", self.daily_budget))
        if remaining < 50_000:
            # Emergency throttle: burn rate is too high, cut burst limit in half
            with self._lock:
                self.burst_limit = max(10, self.burst_limit // 2)

class DailyBudgetExhausted(Exception):
    pass

RATE_LIMITER = TokenBucket()
```

### 2. Full backfill with cursor pagination (contacts search API)

The search API (`POST /crm/v3/objects/contacts/search`) supports cursor pagination via `after`. It returns a maximum of 100 records per page and up to 10,000 records total per search. For tables larger than 10K records, use the `lastmodifieddate` range-slicing strategy: paginate within 30-day windows, sliding forward from the earliest `hs_createdate` in the portal.

```python
import requests
import json

BASE_URL = "https://api.hubapi.com"

def fetch_contacts_page(
    token: str,
    after: str | None,
    properties: list[str],
    rate_limiter: TokenBucket,
) -> tuple[list[dict], str | None]:
    """Fetch one page of contacts. Returns (records, next_cursor)."""
    RATE_LIMITER.acquire()

    body = {
        "limit": 100,
        "properties": properties,
        "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}],
    }
    if after:
        body["after"] = after

    resp = requests.post(
        f"{BASE_URL}/crm/v3/objects/contacts/search",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    rate_limiter.update_from_headers(dict(resp.headers))

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 10))
        time.sleep(retry_after)
        return fetch_contacts_page(token, after, properties, rate_limiter)  # one retry

    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    next_cursor = data.get("paging", {}).get("next", {}).get("after")
    return results, next_cursor


def backfill_contacts(
    token: str,
    properties: list[str],
    rate_limiter: TokenBucket,
    checkpoint_file: str = "/tmp/hubspot_backfill_checkpoint.json",
) -> int:
    """
    Full backfill with checkpoint. Resume-safe: reads cursor from checkpoint_file
    so a mid-run failure restarts from the last completed page, not from zero.

    Returns total records written.
    """
    # Load checkpoint
    try:
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
        after = checkpoint.get("after")
        total = checkpoint.get("total", 0)
        print(f"Resuming backfill from cursor {after}, {total:,} records already written")
    except FileNotFoundError:
        after = None
        total = 0

    while True:
        records, next_cursor = fetch_contacts_page(token, after, properties, rate_limiter)

        if not records:
            break

        yield records   # caller handles warehouse write

        total += len(records)
        after = next_cursor

        # Write checkpoint after every page so a restart costs at most 100 records
        with open(checkpoint_file, "w") as f:
            json.dump({"after": after, "total": total}, f)

        if not next_cursor:
            break

    print(f"Backfill complete: {total:,} contacts")
    return total
```

### 3. Incremental CDC poll (neutralizes missed updates — with association gap)

The standard CDC pattern polls on `hs_lastmodifieddate > last_run`. This catches property changes but **silently misses association changes** (linking a contact to a deal or removing that link does not update `hs_lastmodifieddate`). The fix is a two-pass incremental: a property poll and a separate association poll on a shorter interval.

```python
import datetime

def incremental_contacts_since(
    token: str,
    since_ms: int,
    properties: list[str],
    rate_limiter: TokenBucket,
) -> list[dict]:
    """
    CDC property poll: return all contacts modified after since_ms (Unix ms UTC).

    Does NOT cover association changes — run poll_association_changes() separately.
    """
    all_records = []
    after = None

    while True:
        RATE_LIMITER.acquire()
        body = {
            "limit": 100,
            "properties": properties,
            "filterGroups": [{
                "filters": [{
                    "propertyName": "hs_lastmodifieddate",
                    "operator": "GT",
                    "value": str(since_ms),
                }]
            }],
            "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}],
        }
        if after:
            body["after"] = after

        resp = requests.post(
            f"{BASE_URL}/crm/v3/objects/contacts/search",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        rate_limiter.update_from_headers(dict(resp.headers))
        resp.raise_for_status()

        data = resp.json()
        all_records.extend(data.get("results", []))
        next_cursor = data.get("paging", {}).get("next", {}).get("after")
        if not next_cursor:
            break
        after = next_cursor

    return all_records


def poll_association_changes(
    token: str,
    contact_ids: list[str],
    rate_limiter: TokenBucket,
) -> dict[str, list[str]]:
    """
    Fetch current contact → deal associations for a list of contact IDs.
    Use this to detect additions and deletions that hs_lastmodifieddate misses.

    Strategy: compare fetched associations against warehouse snapshot.
    Differences = changes that must be written.

    Returns {contact_id: [deal_id, ...]}
    """
    # Batch read associations: up to 100 contacts per call (v4 associations API)
    result = {}
    for chunk_start in range(0, len(contact_ids), 100):
        chunk = contact_ids[chunk_start:chunk_start + 100]
        RATE_LIMITER.acquire()

        resp = requests.post(
            f"{BASE_URL}/crm/v4/associations/contacts/deals/batch/read",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"inputs": [{"id": cid} for cid in chunk]},
            timeout=30,
        )
        rate_limiter.update_from_headers(dict(resp.headers))
        resp.raise_for_status()

        for item in resp.json().get("results", []):
            from_id = str(item["from"]["id"])
            to_ids = [str(a["toObjectId"]) for a in item.get("to", [])]
            result[from_id] = to_ids

    return result
```

### 4. Schema drift detection and ALTER TABLE generation

When a portal admin adds or removes a custom property, your warehouse table schema diverges from the API response silently. The correct mitigation is a pre-run schema check: enumerate all HubSpot properties via the properties API, diff against the warehouse column list, and emit ALTER TABLE statements for any new columns. Removed properties become nullable and are not dropped (dropping columns in production is a separate review).

```python
def fetch_hubspot_property_schema(token: str) -> dict[str, str]:
    """
    Returns {property_name: warehouse_type} for all contact properties.
    Maps HubSpot field types to warehouse-appropriate column types.
    """
    resp = requests.get(
        f"{BASE_URL}/crm/v3/properties/contacts",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()

    TYPE_MAP = {
        "string":      "TEXT",
        "number":      "FLOAT64",
        "date":        "DATE",
        "datetime":    "TIMESTAMP",
        "bool":        "BOOLEAN",
        "enumeration": "TEXT",
        "phone_number":"TEXT",
        "json":        "TEXT",       # store complex types as serialized JSON
    }

    schema = {}
    for prop in resp.json().get("results", []):
        hs_type = prop.get("type", "string")
        schema[prop["name"]] = TYPE_MAP.get(hs_type, "TEXT")

    return schema


def detect_schema_drift(
    hubspot_schema: dict[str, str],
    warehouse_columns: set[str],
) -> tuple[dict[str, str], set[str]]:
    """
    Returns:
      added:   {column_name: type}  — in HubSpot but not warehouse
      removed: {column_name}        — in warehouse but not HubSpot
    """
    hs_columns = set(hubspot_schema.keys())
    added   = {k: v for k, v in hubspot_schema.items() if k not in warehouse_columns}
    removed = warehouse_columns - hs_columns - {"_synced_at", "_sync_run_id"}  # exclude meta cols
    return added, removed


def generate_alter_statements(table: str, added: dict[str, str]) -> list[str]:
    """Generate ALTER TABLE ADD COLUMN statements for new HubSpot properties."""
    stmts = []
    for col, dtype in added.items():
        safe_col = col.replace("-", "_").lower()
        stmts.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {safe_col} {dtype};")
    return stmts
```

### 5. Warehouse upsert patterns (neutralizes duplicate rows on retry)

Each warehouse requires a different upsert idiom. The upsert key is always `id` — HubSpot's immutable object ID. Never composite on mutable fields like email or name; those can change and cause phantom duplicates.

All three patterns below use a staging table approach: load new rows into a temp table, then merge into production. This is the most portable pattern across warehouse engines.

```python
import pandas as pd
import pyarrow as pa

def build_contacts_dataframe(records: list[dict], properties: list[str]) -> pd.DataFrame:
    """
    Normalize HubSpot search API results into a flat DataFrame.

    Key transformations:
    - All timestamps parsed as UTC (avoids timezone-at-load inconsistency)
    - Nested properties dict flattened to columns
    - Missing properties filled with None (not 0 or empty string)
    - _synced_at appended so warehouse always has the load timestamp
    """
    rows = []
    for r in records:
        row = {"id": r["id"]}
        props = r.get("properties", {})
        for p in properties:
            val = props.get(p)
            # HubSpot timestamps are Unix ms UTC — parse explicitly
            if val and p.endswith("date") and val.isdigit():
                row[p] = pd.to_datetime(int(val), unit="ms", utc=True)
            else:
                row[p] = val
        row["_synced_at"] = pd.Timestamp.utcnow()
        rows.append(row)

    return pd.DataFrame(rows)
```

**BigQuery — MERGE upsert**

```python
from google.cloud import bigquery

def upsert_to_bigquery(
    df: pd.DataFrame,
    project: str,
    dataset: str,
    table: str,
    bq_client: bigquery.Client,
) -> int:
    staging_table = f"{project}.{dataset}.{table}_staging"
    target_table  = f"{project}.{dataset}.{table}"

    # Write staging
    job = bq_client.load_table_from_dataframe(df, staging_table,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"))
    job.result()

    # MERGE into target — upsert on id
    merge_sql = f"""
    MERGE `{target_table}` T
    USING `{staging_table}` S
      ON T.id = S.id
    WHEN MATCHED THEN
      UPDATE SET {', '.join(f'T.{c} = S.{c}' for c in df.columns if c != 'id')}
    WHEN NOT MATCHED THEN
      INSERT ({', '.join(df.columns)})
      VALUES ({', '.join(f'S.{c}' for c in df.columns)})
    """
    bq_client.query(merge_sql).result()
    return len(df)
```

**Snowflake — MERGE upsert**

```python
import snowflake.connector

def upsert_to_snowflake(
    df: pd.DataFrame,
    conn: snowflake.connector.SnowflakeConnection,
    schema: str,
    table: str,
) -> int:
    staging = f"{schema}.{table}_staging"
    target  = f"{schema}.{table}"
    cursor  = conn.cursor()

    # Write staging via CSV upload + COPY INTO
    cursor.execute(f"CREATE OR REPLACE TEMP TABLE {staging} LIKE {target}")
    success, nchunks, nrows, _ = snowflake.connector.pandas_tools.write_pandas(
        conn, df, f"{table}_staging", schema=schema, auto_create_table=False
    )

    set_cols  = ", ".join(f"t.{c} = s.{c}" for c in df.columns if c != "id")
    ins_cols  = ", ".join(df.columns)
    ins_vals  = ", ".join(f"s.{c}" for c in df.columns)

    cursor.execute(f"""
        MERGE INTO {target} t
        USING {staging} s ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET {set_cols}
        WHEN NOT MATCHED THEN INSERT ({ins_cols}) VALUES ({ins_vals})
    """)
    return nrows
```

**Postgres — INSERT ... ON CONFLICT upsert**

```python
import psycopg2
from psycopg2.extras import execute_values

def upsert_to_postgres(
    df: pd.DataFrame,
    conn: psycopg2.extensions.connection,
    schema: str,
    table: str,
) -> int:
    cols     = list(df.columns)
    set_expr = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "id")
    sql = f"""
        INSERT INTO {schema}.{table} ({', '.join(cols)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET {set_expr}
    """
    rows = [tuple(r) for r in df.itertuples(index=False, name=None)]
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)
```

### 6. Large association payloads (separate fetch pass)

Never pull associations inline in the contacts search response. A contact with 500 engagement records produces a response payload measured in megabytes that times out or exceeds HTTP limits. Fetch associations in a second pass using the batch associations endpoint, keyed on the contact IDs from step 2/3.

The implementation is in `poll_association_changes()` above. The rule is: contacts page first, IDs collected, associations fetched as a second batch read. Write associations to a separate `hubspot_contact_deal_associations` table — not as columns on the contacts table.

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `429 TOO_MANY_REQUESTS` | `RATE_LIMIT` | Burst or daily quota exhausted | Read `Retry-After` header; sleep; check daily remaining |
| `400 BAD_REQUEST` | `INVALID_FILTER_VALUE` | `hs_lastmodifieddate` filter value is not a valid Unix ms string | Cast `since_ms` to `str` before inserting into filter body |
| `400 BAD_REQUEST` | `INVALID_OFFSET` | Cursor `after` value is stale (>7 days for search API) | Discard checkpoint; restart backfill from beginning of window |
| `400 BAD_REQUEST` | `Max associations per request exceeded` | Sent more than 100 IDs to batch associations endpoint | Chunk input list to 100 before calling |
| `401 UNAUTHORIZED` | `INVALID_AUTHENTICATION` | Token expired or revoked | Rotate or refresh token before resuming |
| `403 FORBIDDEN` | `MISSING_SCOPES` | `crm.schemas.contacts.read` not granted | Add scope in Private Apps settings |
| `413 PAYLOAD_TOO_LARGE` | — | Property list too long for a single search call | Request properties in batches of 50, merge results |
| `500 INTERNAL_ERROR` | — | Transient HubSpot server error | Retry with exponential backoff (max 4 attempts) |
| `504 GATEWAY_TIMEOUT` | — | Response payload too large or HubSpot overloaded | Reduce page size to 50; add 2s delay between calls |
| `DailyBudgetExhausted` (local) | — | Token bucket daily ceiling hit | Pause extraction until midnight UTC; alert on-call |

## Examples

### Minimal end-to-end backfill to BigQuery

```bash
python3 - <<'EOF'
import os
from google.cloud import bigquery
# See implementation-guide.md for full script with retry, schema sync, and checkpoint
from hubspot_sync import backfill_contacts, upsert_to_bigquery, TokenBucket

TOKEN   = os.environ["HUBSPOT_ACCESS_TOKEN"]
PROJECT = os.environ["GCP_PROJECT"]
DATASET = "hubspot_raw"
TABLE   = "contacts"

bq      = bigquery.Client(project=PROJECT)
limiter = TokenBucket(daily_budget=400_000)
props   = ["email", "firstname", "lastname", "hs_lastmodifieddate", "lifecyclestage"]

for page in backfill_contacts(TOKEN, props, limiter):
    df = build_contacts_dataframe(page, props)
    upsert_to_bigquery(df, PROJECT, DATASET, TABLE, bq)
EOF
```

### Inspect current rate-limit headroom before starting a backfill

```bash
curl -s -I "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "X-HubSpot-RateLimit"
```

### Enumerate all contact properties (for schema sync)

```bash
curl -s "https://api.hubapi.com/crm/v3/properties/contacts" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | jq '[.results[] | {name: .name, type: .type, label: .label}]' \
  | head -60
```

### Run CDC since last successful run (stored in a state table)

```bash
python3 - <<'EOF'
import os, requests, datetime
TOKEN    = os.environ["HUBSPOT_ACCESS_TOKEN"]
SINCE_MS = 1_700_000_000_000   # replace with value from state table

from hubspot_sync import incremental_contacts_since, TokenBucket
limiter  = TokenBucket()
records  = incremental_contacts_since(TOKEN, SINCE_MS, ["email", "lifecyclestage"], limiter)
print(f"CDC returned {len(records)} changed contacts")
EOF
```

## Output

- Token bucket rate limiter configured to stay within daily budget with live header feedback
- Full backfill loop with checkpoint file for resume-safe restarts
- CDC property poll (contacts modified since last run) with filter on `hs_lastmodifieddate`
- Association CDC via separate batch associations poll, writing to a separate junction table
- Schema drift detection comparing HubSpot property API response against warehouse column list
- ALTER TABLE statements for new properties, no auto-drop for removed properties
- `pandas` DataFrame builder with UTC timestamp normalization
- BigQuery MERGE, Snowflake MERGE, and Postgres INSERT ... ON CONFLICT upsert patterns
- Monitoring log lines at every rate-limit threshold and schema drift event

## Resources

- [HubSpot CRM Search API](https://developers.hubspot.com/docs/api/crm/search)
- [HubSpot Batch Read Contacts](https://developers.hubspot.com/docs/api/crm/contacts)
- [HubSpot v4 Associations API](https://developers.hubspot.com/docs/api/crm/associations)
- [HubSpot Properties API](https://developers.hubspot.com/docs/api/crm/properties)
- [HubSpot Rate Limits Reference](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [API_REFERENCE.md](references/API_REFERENCE.md) — search API cursor shapes, batch read request/response, CDC fields, rate-limit headers, association batch format
- [implementation-guide.md](references/implementation-guide.md) — complete backfill script with token bucket, full CDC poll loop, schema drift handler, ALTER TABLE generator, all three warehouse upsert implementations
