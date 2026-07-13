# HubSpot Warehouse Sync — Implementation Guide

Complete Python scripts for production-grade HubSpot → warehouse extraction. Covers token bucket rate limiting, full backfill with checkpoint, incremental CDC poll with association gap handling, schema drift detection with ALTER TABLE generation, and warehouse-specific upsert patterns for BigQuery, Snowflake, and Postgres. The SKILL.md contains the conceptual model and failure taxonomy; this file is the runnable code.

---

## Project Layout

```
hubspot_sync/
├── __init__.py
├── rate_limiter.py          # Token bucket + daily budget enforcement
├── extract.py               # Backfill, CDC poll, association batch
├── schema.py                # Property enumeration, drift detection, ALTER generation
├── load_bigquery.py         # BigQuery MERGE upsert
├── load_snowflake.py        # Snowflake MERGE upsert
├── load_postgres.py         # Postgres INSERT ... ON CONFLICT
├── transform.py             # DataFrame builder, UTC normalization
└── state.py                 # Checkpoint read/write, last-run timestamp management
```

Install dependencies:

```bash
pip install requests pandas pyarrow google-cloud-bigquery \
    snowflake-connector-python psycopg2-binary python-dotenv
```

---

## rate_limiter.py — Token Bucket with Daily Budget

```python
"""
Token bucket rate limiter for HubSpot API calls.

Enforces two constraints simultaneously:
  1. Burst limit: at most `burst_limit` calls per 10-second rolling window
  2. Daily budget: at most `daily_budget` calls per 24-hour window

The daily budget is set below the account limit so other integrations retain
headroom. At 500K/day Professional tier, use daily_budget=400_000.

Live rate-limit headers on each response are inspected via update_from_headers().
If the daily remaining drops below 50K (indicating other integrations or retry
storms are burning quota faster than expected), the burst limit is halved as an
emergency throttle. This halving is sticky until the day resets.
"""
import time
import threading
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class DailyBudgetExhausted(Exception):
    """Raised when the daily API call budget has been reached."""
    def __init__(self, calls_used: int, budget: int, hours_remaining: float):
        self.calls_used = calls_used
        self.budget = budget
        self.hours_remaining = hours_remaining
        super().__init__(
            f"Daily HubSpot API budget exhausted: {calls_used:,}/{budget:,} calls used. "
            f"Resuming in {hours_remaining:.1f}h (midnight UTC)."
        )


@dataclass
class TokenBucket:
    daily_budget: int = 400_000   # stay below 500K Professional limit
    burst_limit: int = 95          # 100/10s window; leave 5 calls headroom

    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _calls_today: int = field(default=0, init=False)
    _window_calls: int = field(default=0, init=False)
    _window_start: float = field(default_factory=time.monotonic, init=False)
    _day_start: float = field(default_factory=time.monotonic, init=False)

    def acquire(self) -> None:
        """
        Block until a call slot is available, then consume one slot.
        Raises DailyBudgetExhausted if the daily ceiling has been reached.
        """
        with self._lock:
            now = time.monotonic()

            # Reset daily counter at midnight UTC
            if now - self._day_start >= 86_400.0:
                logger.info("Daily rate-limit window reset. Calls yesterday: %d", self._calls_today)
                self._calls_today = 0
                self._day_start = now

            # Reset 10-second window counter
            if now - self._window_start >= 10.0:
                self._window_calls = 0
                self._window_start = now

            # Daily budget enforcement — hard stop
            if self._calls_today >= self.daily_budget:
                hours_remaining = (86_400.0 - (now - self._day_start)) / 3_600.0
                raise DailyBudgetExhausted(self._calls_today, self.daily_budget, hours_remaining)

            # Burst window throttle — sleep until window resets
            if self._window_calls >= self.burst_limit:
                sleep_s = 10.0 - (now - self._window_start) + 0.05
                logger.debug("Burst limit reached; sleeping %.2fs", sleep_s)
                time.sleep(max(0.0, sleep_s))
                self._window_calls = 0
                self._window_start = time.monotonic()

            self._calls_today += 1
            self._window_calls += 1

    def update_from_headers(self, headers: dict) -> None:
        """
        Inspect live rate-limit headers after each response.

        If daily remaining drops below 50K, the burst limit is halved
        as an emergency measure to slow extraction and protect other integrations.
        """
        daily_remaining_str = headers.get("X-HubSpot-RateLimit-Daily-Remaining", "")
        if not daily_remaining_str.isdigit():
            return

        daily_remaining = int(daily_remaining_str)
        logger.debug("HubSpot daily remaining: %d", daily_remaining)

        with self._lock:
            if daily_remaining < 50_000:
                new_burst = max(10, self.burst_limit // 2)
                if new_burst != self.burst_limit:
                    logger.warning(
                        "Daily remaining below 50K (%d). Emergency throttle: burst_limit %d → %d",
                        daily_remaining, self.burst_limit, new_burst
                    )
                    self.burst_limit = new_burst
```

---

## extract.py — Backfill and Incremental CDC

```python
"""
Contact extraction: full backfill with checkpoint and incremental CDC poll.

Backfill strategy:
  For up to 10K contacts: use the search API with ascending hs_lastmodifieddate sort.
  For more than 10K contacts: use 30-day hs_createdate range windows, each paginated
  fully before advancing to the next window. Overlapping windows by 60s on each
  boundary prevents boundary misses. The upsert key (id) deduplicates the overlap.

CDC strategy:
  Property changes: search API with hs_lastmodifieddate GT last_run_ms.
  Association changes: batch associations read for all recently-modified contact IDs,
  compared against warehouse snapshot. Differences = insertions and deletions.
"""
import json
import logging
import time
import datetime
from typing import Generator

import requests

from .rate_limiter import TokenBucket

logger = logging.getLogger(__name__)

BASE_URL = "https://api.hubapi.com"
MAX_SEARCH_LIMIT = 100   # HubSpot hard limit per search page
MAX_BATCH_IDS = 100      # HubSpot hard limit for batch read and batch associations
MAX_RETRIES = 4
BASE_BACKOFF_S = 1.0


def _hs_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _request_with_retry(
    method: str,
    url: str,
    token: str,
    limiter: TokenBucket,
    **kwargs,
) -> requests.Response:
    """
    Make an API call with token-bucket gating and exponential backoff.
    Re-raises on non-retryable errors (400, 401, 403) immediately.
    Retries on 429 and 5xx up to MAX_RETRIES times.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        limiter.acquire()
        resp = requests.request(
            method, url, headers=_hs_headers(token), timeout=30, **kwargs
        )
        limiter.update_from_headers(dict(resp.headers))

        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", BASE_BACKOFF_S * 2 ** attempt))
            logger.warning("429 rate limit; sleeping %.1fs (attempt %d/%d)", retry_after, attempt, MAX_RETRIES)
            time.sleep(retry_after)
            continue

        if resp.status_code >= 500:
            delay = BASE_BACKOFF_S * (2 ** attempt)
            logger.warning("HubSpot %d; retrying in %.1fs (attempt %d/%d)", resp.status_code, delay, attempt, MAX_RETRIES)
            time.sleep(delay)
            continue

        # 400 / 401 / 403 are not retriable — surface immediately
        resp.raise_for_status()
        return resp

    raise RuntimeError(f"Max retries ({MAX_RETRIES}) exceeded for {method} {url}")


# ---------------------------------------------------------------------------
# Full backfill (< 10K contacts)
# ---------------------------------------------------------------------------

def backfill_contacts_small(
    token: str,
    properties: list[str],
    limiter: TokenBucket,
    checkpoint_file: str = "/tmp/hs_backfill_small.json",
) -> Generator[list[dict], None, None]:
    """
    Paginate through ALL contacts via the search API.
    Safe for portals with < 10,000 contacts.
    Yields one page (list of records) at a time.
    Writes checkpoint after each page for resume-safe restarts.
    """
    try:
        with open(checkpoint_file) as f:
            cp = json.load(f)
        after, total = cp.get("after"), cp.get("total", 0)
        logger.info("Resuming backfill from cursor %s (%d written)", after, total)
    except FileNotFoundError:
        after, total = None, 0

    while True:
        body: dict = {
            "limit": MAX_SEARCH_LIMIT,
            "properties": properties,
            "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}],
        }
        if after:
            body["after"] = after

        resp = _request_with_retry("POST", f"{BASE_URL}/crm/v3/objects/contacts/search",
                                   token, limiter, json=body)
        data = resp.json()
        records = data.get("results", [])
        if not records:
            break

        yield records
        total += len(records)
        after = data.get("paging", {}).get("next", {}).get("after")

        with open(checkpoint_file, "w") as f:
            json.dump({"after": after, "total": total}, f)

        logger.info("Backfill page: %d records (running total: %d)", len(records), total)
        if not after:
            break

    logger.info("Backfill complete: %d total contacts", total)


# ---------------------------------------------------------------------------
# Full backfill (> 10K contacts) — 30-day range-slice strategy
# ---------------------------------------------------------------------------

def _ms_windows(start_dt: datetime.datetime, end_dt: datetime.datetime,
                window_days: int = 30, overlap_s: int = 60) -> list[tuple[int, int]]:
    """
    Generate [from_ms, to_ms] pairs covering start_dt to end_dt in window_days chunks.
    Each window overlaps the next by overlap_s seconds to prevent boundary misses.
    """
    windows = []
    t = start_dt
    delta = datetime.timedelta(days=window_days)
    while t < end_dt:
        t_end = min(t + delta, end_dt)
        from_ms = int(t.timestamp() * 1000) - (overlap_s * 1000 if windows else 0)
        to_ms   = int(t_end.timestamp() * 1000)
        windows.append((max(0, from_ms), to_ms))
        t = t_end
    return windows


def backfill_contacts_large(
    token: str,
    properties: list[str],
    limiter: TokenBucket,
    portal_created_at: datetime.datetime,
    checkpoint_file: str = "/tmp/hs_backfill_large.json",
) -> Generator[list[dict], None, None]:
    """
    Range-slice backfill for portals with > 10K contacts.
    Slices on hs_createdate in 30-day windows.
    Resumes at the last completed window index on restart.
    """
    end_dt = datetime.datetime.now(tz=datetime.timezone.utc)
    windows = _ms_windows(
        portal_created_at.replace(tzinfo=datetime.timezone.utc),
        end_dt
    )

    try:
        with open(checkpoint_file) as f:
            cp = json.load(f)
        start_window = cp.get("next_window", 0)
    except FileNotFoundError:
        start_window = 0

    for window_idx in range(start_window, len(windows)):
        from_ms, to_ms = windows[window_idx]
        logger.info("Backfill window %d/%d: %d → %d", window_idx + 1, len(windows), from_ms, to_ms)
        after = None

        while True:
            body: dict = {
                "limit": MAX_SEARCH_LIMIT,
                "properties": properties,
                "filterGroups": [{
                    "filters": [
                        {"propertyName": "hs_createdate", "operator": "GTE", "value": str(from_ms)},
                        {"propertyName": "hs_createdate", "operator": "LT",  "value": str(to_ms)},
                    ]
                }],
                "sorts": [{"propertyName": "hs_createdate", "direction": "ASCENDING"}],
            }
            if after:
                body["after"] = after

            resp = _request_with_retry("POST", f"{BASE_URL}/crm/v3/objects/contacts/search",
                                       token, limiter, json=body)
            data = resp.json()
            records = data.get("results", [])
            if records:
                yield records

            after = data.get("paging", {}).get("next", {}).get("after")
            if not after:
                break

        # Checkpoint after each full window
        with open(checkpoint_file, "w") as f:
            json.dump({"next_window": window_idx + 1}, f)


# ---------------------------------------------------------------------------
# Incremental CDC poll (property changes only)
# ---------------------------------------------------------------------------

def incremental_contacts_since(
    token: str,
    since_ms: int,
    properties: list[str],
    limiter: TokenBucket,
) -> Generator[list[dict], None, None]:
    """
    CDC property poll: yield pages of contacts modified after since_ms (Unix ms UTC).

    NOTE: Does NOT capture association changes. Association changes do not update
    hs_lastmodifieddate. Run poll_association_changes() separately for those.
    """
    after = None
    page_count = 0

    while True:
        body: dict = {
            "limit": MAX_SEARCH_LIMIT,
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

        resp = _request_with_retry("POST", f"{BASE_URL}/crm/v3/objects/contacts/search",
                                   token, limiter, json=body)
        data = resp.json()
        records = data.get("results", [])
        if not records:
            break

        page_count += 1
        logger.debug("CDC page %d: %d records", page_count, len(records))
        yield records

        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

    logger.info("CDC complete: %d pages returned", page_count)


# ---------------------------------------------------------------------------
# Association CDC poll (covers what hs_lastmodifieddate misses)
# ---------------------------------------------------------------------------

def poll_contact_deal_associations(
    token: str,
    contact_ids: list[str],
    limiter: TokenBucket,
) -> dict[str, list[str]]:
    """
    Fetch current contact → deal associations for a list of contact IDs.

    Returns {contact_id: [deal_id, ...]} for all input IDs.
    Contacts with no deals are included with an empty list.

    Compare against warehouse snapshot to find insertions (in result but not warehouse)
    and deletions (in warehouse but not in result).
    """
    result: dict[str, list[str]] = {cid: [] for cid in contact_ids}

    for i in range(0, len(contact_ids), MAX_BATCH_IDS):
        chunk = contact_ids[i:i + MAX_BATCH_IDS]
        resp = _request_with_retry(
            "POST",
            f"{BASE_URL}/crm/v4/associations/contacts/deals/batch/read",
            token,
            limiter,
            json={"inputs": [{"id": cid} for cid in chunk]},
        )
        for item in resp.json().get("results", []):
            from_id = str(item["from"]["id"])
            result[from_id] = [str(a["toObjectId"]) for a in item.get("to", [])]

    return result
```

---

## schema.py — Drift Detection and ALTER TABLE Generation

```python
"""
Schema drift detection for HubSpot → warehouse sync.

Workflow:
1. Enumerate all HubSpot contact properties via /crm/v3/properties/contacts
2. Fetch the current warehouse column list (table-specific)
3. Diff: identify added (in HubSpot, not in warehouse) and removed (in warehouse, not in HubSpot)
4. Generate ALTER TABLE ADD COLUMN statements for added properties
5. Log removed properties — do NOT auto-drop; that requires a manual review

Caller is responsible for executing the ALTER statements before the load job runs.
"""
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.hubapi.com"

HS_TO_WAREHOUSE_TYPE: dict[str, str] = {
    "string":       "TEXT",
    "number":       "FLOAT64",
    "date":         "DATE",
    "datetime":     "TIMESTAMP",
    "bool":         "BOOLEAN",
    "enumeration":  "TEXT",
    "phone_number": "TEXT",
    "json":         "TEXT",
}

# Columns managed by the sync pipeline — exclude from drift detection
PIPELINE_COLUMNS = {"_synced_at", "_sync_run_id", "archived", "archived_at"}


def fetch_hubspot_property_schema(token: str) -> dict[str, str]:
    """
    Returns {property_name: warehouse_column_type} for all contact properties.
    """
    resp = requests.get(
        f"{BASE_URL}/crm/v3/properties/contacts",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()

    schema: dict[str, str] = {}
    for prop in resp.json().get("results", []):
        hs_type = prop.get("type", "string")
        schema[prop["name"]] = HS_TO_WAREHOUSE_TYPE.get(hs_type, "TEXT")

    logger.info("HubSpot schema: %d properties enumerated", len(schema))
    return schema


def detect_schema_drift(
    hubspot_schema: dict[str, str],
    warehouse_columns: set[str],
) -> tuple[dict[str, str], set[str]]:
    """
    Compare HubSpot property schema against warehouse column set.

    Returns:
      added:   {property_name: warehouse_type}  columns in HubSpot but not in warehouse
      removed: {property_name}                   columns in warehouse but not in HubSpot
    """
    hs_columns = set(hubspot_schema.keys())
    candidate_removals = warehouse_columns - hs_columns - PIPELINE_COLUMNS

    added   = {k: v for k, v in hubspot_schema.items() if k not in warehouse_columns}
    removed = candidate_removals

    if added:
        logger.warning("Schema drift — %d new HubSpot properties not in warehouse: %s",
                       len(added), list(added.keys()))
    if removed:
        logger.warning("Schema drift — %d warehouse columns not in HubSpot (removed properties?): %s",
                       len(removed), list(removed))

    return added, removed


def generate_alter_statements(
    table_fqn: str,
    added: dict[str, str],
    dialect: str = "standard",  # "bigquery" | "snowflake" | "postgres" | "standard"
) -> list[str]:
    """
    Generate ALTER TABLE ADD COLUMN statements for new HubSpot properties.

    Uses IF NOT EXISTS to make statements idempotent (re-runnable on restart).
    Property names are sanitized: hyphens → underscores, lowercased.

    dialect:
      "bigquery"   — BigQuery syntax (no schema prefix in column type)
      "snowflake"  — Snowflake syntax (IF NOT EXISTS supported)
      "postgres"   — Postgres syntax (IF NOT EXISTS supported ≥ Postgres 9.6)
      "standard"   — ANSI SQL (omits IF NOT EXISTS for compatibility)
    """
    stmts = []
    for raw_name, dtype in sorted(added.items()):
        col = raw_name.replace("-", "_").lower()

        if dialect == "bigquery":
            # BigQuery uses FLOAT64 natively
            stmts.append(f"ALTER TABLE `{table_fqn}` ADD COLUMN IF NOT EXISTS `{col}` {dtype};")
        elif dialect == "snowflake":
            sf_type = dtype.replace("FLOAT64", "FLOAT").replace("TIMESTAMP", "TIMESTAMP_TZ")
            stmts.append(f'ALTER TABLE {table_fqn} ADD COLUMN IF NOT EXISTS "{col}" {sf_type};')
        elif dialect == "postgres":
            pg_type = dtype.replace("FLOAT64", "DOUBLE PRECISION").replace("TIMESTAMP", "TIMESTAMPTZ")
            stmts.append(f"ALTER TABLE {table_fqn} ADD COLUMN IF NOT EXISTS {col} {pg_type};")
        else:
            stmts.append(f"ALTER TABLE {table_fqn} ADD COLUMN {col} {dtype};")

    return stmts


def apply_schema_changes(
    stmts: list[str],
    conn,  # any connection with .cursor() and .execute()
    dry_run: bool = False,
) -> None:
    """
    Execute ALTER TABLE statements against a warehouse connection.
    dry_run=True logs the statements without executing — use for validation.
    """
    for stmt in stmts:
        if dry_run:
            logger.info("[DRY RUN] Would execute: %s", stmt)
        else:
            logger.info("Executing schema change: %s", stmt)
            with conn.cursor() as cur:
                cur.execute(stmt)
            conn.commit()
```

---

## transform.py — DataFrame Builder with UTC Normalization

```python
"""
Transform HubSpot API records into a pandas DataFrame ready for warehouse load.

Key transformations:
  1. UTC timestamp parsing — HubSpot timestamps arrive as ISO 8601 strings or as
     Unix ms strings in filter values. Both are parsed as UTC explicitly. Never let
     pandas infer timezone from local system settings.
  2. Flat property extraction — the nested {id, properties: {...}} API shape is
     flattened to one row per record.
  3. Boolean coercion — HubSpot returns booleans as the strings "true"/"false".
  4. Pipeline metadata columns — _synced_at (UTC) and _sync_run_id appended to
     every row so loads are traceable in the warehouse.
"""
import uuid
import logging
import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_SYNC_RUN_ID = str(uuid.uuid4())   # stable within one pipeline run


def _parse_hs_timestamp(value: Optional[str]) -> Optional[pd.Timestamp]:
    """Parse a HubSpot timestamp (ISO 8601 string or Unix ms string) as UTC."""
    if not value:
        return None
    if value.isdigit():
        return pd.Timestamp(int(value), unit="ms", tz="UTC")
    try:
        ts = pd.Timestamp(value)
        return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    except Exception:
        return None


_BOOL_PROPERTIES = frozenset([
    "hs_is_contact", "hs_email_optout", "hs_marketable_status",
])

_TIMESTAMP_SUFFIXES = ("date", "timestamp", "_at", "_time")


def build_contacts_dataframe(
    records: list[dict],
    properties: list[str],
    hubspot_schema: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Normalize HubSpot search/batch API records into a flat DataFrame.

    records: list of {id, properties: {...}, createdAt, updatedAt, archived, archivedAt}
    properties: the list of property names requested (determines column order)
    hubspot_schema: {property_name: warehouse_type} from schema.py — used to
      infer which string columns should be parsed as timestamps or booleans.

    Returns a DataFrame with one row per record, all timestamps in UTC,
    plus pipeline metadata columns _synced_at and _sync_run_id.
    """
    rows = []
    for r in records:
        props = r.get("properties", {})
        row: dict = {"id": r["id"]}

        for p in properties:
            val = props.get(p)
            wh_type = (hubspot_schema or {}).get(p, "TEXT")

            if val is None:
                row[p] = None
            elif wh_type in ("TIMESTAMP", "DATE") or any(p.endswith(s) for s in _TIMESTAMP_SUFFIXES):
                row[p] = _parse_hs_timestamp(val)
            elif wh_type == "BOOLEAN" or p in _BOOL_PROPERTIES:
                row[p] = val.lower() == "true" if isinstance(val, str) else bool(val)
            elif wh_type == "FLOAT64" and isinstance(val, str):
                try:
                    row[p] = float(val)
                except ValueError:
                    row[p] = None
            else:
                row[p] = val

        # Envelope fields
        row["archived"]     = r.get("archived", False)
        row["archived_at"]  = _parse_hs_timestamp(r.get("archivedAt"))

        # Pipeline metadata
        row["_synced_at"]      = pd.Timestamp.now(tz="UTC")
        row["_sync_run_id"]    = _SYNC_RUN_ID

        rows.append(row)

    df = pd.DataFrame(rows)
    logger.debug("Built DataFrame: %d rows × %d columns", len(df), len(df.columns))
    return df


def build_associations_dataframe(
    associations: dict[str, list[str]],
) -> pd.DataFrame:
    """
    Normalize association batch read results into a flat junction table DataFrame.

    associations: {contact_id: [deal_id, ...]} from extract.poll_contact_deal_associations()
    Returns rows of (contact_id, deal_id, _synced_at, _sync_run_id).
    Contacts with no deals produce no rows (the junction table represents only existing links).
    """
    rows = [
        {
            "contact_id": cid,
            "deal_id": did,
            "_synced_at": pd.Timestamp.now(tz="UTC"),
            "_sync_run_id": _SYNC_RUN_ID,
        }
        for cid, deal_ids in associations.items()
        for did in deal_ids
    ]
    return pd.DataFrame(rows)
```

---

## load_bigquery.py — BigQuery MERGE Upsert

```python
"""
BigQuery upsert via staging table + MERGE statement.

Pattern:
  1. Write new/changed records to a staging table (WRITE_TRUNCATE — staging is ephemeral)
  2. MERGE staging into the production table on id
  3. Drop staging (or leave it; WRITE_TRUNCATE on next run handles cleanup)

The MERGE statement is atomic — either all rows apply or none do. This makes
retries safe: a second MERGE on the same staging data produces the same result.

Requires: google-cloud-bigquery, pyarrow
Service account must have bigquery.dataEditor on the dataset.
"""
import logging

import pandas as pd
from google.cloud import bigquery

logger = logging.getLogger(__name__)


def upsert_to_bigquery(
    df: pd.DataFrame,
    bq: bigquery.Client,
    project: str,
    dataset: str,
    table: str,
) -> int:
    """
    Upsert df into {project}.{dataset}.{table} via staging MERGE.
    Returns number of rows processed.
    Raises on any BigQuery job error.
    """
    if df.empty:
        return 0

    target  = f"{project}.{dataset}.{table}"
    staging = f"{project}.{dataset}.{table}_staging"

    # Step 1: write staging (overwrite any prior staging data)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=False,
    )
    # BigQuery infers schema from DataFrame dtypes via pyarrow; explicit schema
    # can be provided via job_config.schema for tighter control
    load_job = bq.load_table_from_dataframe(df, staging, job_config=job_config)
    load_job.result()   # raises google.api_core.exceptions.GoogleAPIError on failure

    # Step 2: MERGE into production
    non_key_cols = [c for c in df.columns if c != "id"]
    set_clause   = ",\n    ".join(f"T.`{c}` = S.`{c}`" for c in non_key_cols)
    ins_cols     = ", ".join(f"`{c}`" for c in df.columns)
    ins_vals     = ", ".join(f"S.`{c}`" for c in df.columns)

    merge_sql = f"""
    MERGE `{target}` T
    USING `{staging}` S
      ON T.id = S.id
    WHEN MATCHED THEN
      UPDATE SET
        {set_clause}
    WHEN NOT MATCHED THEN
      INSERT ({ins_cols})
      VALUES ({ins_vals})
    """
    query_job = bq.query(merge_sql)
    query_job.result()

    logger.info("BigQuery MERGE: %d rows into %s", len(df), target)
    return len(df)


def get_bigquery_columns(bq: bigquery.Client, project: str, dataset: str, table: str) -> set[str]:
    """Return the set of column names for a BigQuery table."""
    try:
        tbl = bq.get_table(f"{project}.{dataset}.{table}")
        return {f.name for f in tbl.schema}
    except Exception:
        return set()
```

---

## load_snowflake.py — Snowflake MERGE Upsert

```python
"""
Snowflake upsert via temporary staging table + MERGE statement.

Pattern:
  1. CREATE OR REPLACE TEMP TABLE staging LIKE target (column definitions copied)
  2. write_pandas() to upload DataFrame via internal stage
  3. MERGE staging into target on id
  4. Temp table auto-drops at session close

Requires: snowflake-connector-python[pandas]
User needs INSERT, UPDATE, CREATE TEMP TABLE privileges on the schema.
"""
import logging

import pandas as pd
import snowflake.connector
import snowflake.connector.pandas_tools as sf_pandas

logger = logging.getLogger(__name__)


def upsert_to_snowflake(
    df: pd.DataFrame,
    conn: snowflake.connector.SnowflakeConnection,
    schema: str,
    table: str,
) -> int:
    if df.empty:
        return 0

    staging = f"{schema}.{table}_staging"
    target  = f"{schema}.{table}"
    cur     = conn.cursor()

    # Snowflake TIMESTAMP_TZ for timezone-aware columns
    # Coerce pandas Timestamp columns to strings for Snowflake compatibility
    df_load = df.copy()
    for col in df_load.select_dtypes(include=["datetimetz"]).columns:
        df_load[col] = df_load[col].dt.strftime("%Y-%m-%d %H:%M:%S.%f+00:00")

    # Step 1: create temp staging table mirroring production schema
    cur.execute(f"CREATE OR REPLACE TEMP TABLE {staging} LIKE {target}")

    # Step 2: bulk load via write_pandas (uses PUT + COPY INTO internally)
    success, nchunks, nrows, _ = sf_pandas.write_pandas(
        conn,
        df_load,
        table_name=f"{table}_staging",
        schema=schema,
        auto_create_table=False,
        overwrite=True,
        quote_identifiers=False,
    )
    if not success:
        raise RuntimeError(f"Snowflake write_pandas failed: {nchunks} chunks, {nrows} rows")

    # Step 3: MERGE
    non_key = [c for c in df.columns if c != "id"]
    set_clause = ", ".join(f't."{c}" = s."{c}"' for c in non_key)
    ins_cols   = ", ".join(f'"{c}"' for c in df.columns)
    ins_vals   = ", ".join(f's."{c}"' for c in df.columns)

    cur.execute(f"""
        MERGE INTO {target} t
        USING {staging} s ON t."id" = s."id"
        WHEN MATCHED THEN UPDATE SET {set_clause}
        WHEN NOT MATCHED THEN INSERT ({ins_cols}) VALUES ({ins_vals})
    """)

    logger.info("Snowflake MERGE: %d rows into %s", nrows, target)
    cur.close()
    return nrows


def get_snowflake_columns(
    conn: snowflake.connector.SnowflakeConnection,
    schema: str,
    table: str,
) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"DESCRIBE TABLE {schema}.{table}")
    cols = {row[0].lower() for row in cur.fetchall()}
    cur.close()
    return cols
```

---

## load_postgres.py — Postgres INSERT ... ON CONFLICT Upsert

```python
"""
Postgres upsert via INSERT ... ON CONFLICT (id) DO UPDATE SET.

This is the simplest warehouse upsert — no staging table needed. The ON CONFLICT
clause handles concurrent inserts safely (Postgres uses row-level locking).

Requires: psycopg2-binary
User needs INSERT, UPDATE on the target table.
The table must have a UNIQUE or PRIMARY KEY constraint on the `id` column.

CREATE TABLE hubspot.contacts (
    id TEXT PRIMARY KEY,
    email TEXT,
    firstname TEXT,
    ...
    _synced_at TIMESTAMPTZ,
    _sync_run_id TEXT
);
"""
import logging
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


def upsert_to_postgres(
    df: pd.DataFrame,
    conn: psycopg2.extensions.connection,
    schema: str,
    table: str,
    batch_size: int = 500,
) -> int:
    """
    Upsert df rows into {schema}.{table} in batches.
    The table must have PRIMARY KEY or UNIQUE on `id`.
    Returns total rows processed.
    """
    if df.empty:
        return 0

    cols = list(df.columns)
    set_expr = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "id")
    sql = (
        f"INSERT INTO {schema}.{table} ({', '.join(cols)})\n"
        f"VALUES %s\n"
        f"ON CONFLICT (id) DO UPDATE SET {set_expr}"
    )

    # Convert timezone-aware timestamps to offset-aware strings Postgres accepts
    df_load = df.copy()
    for col in df_load.select_dtypes(include=["datetimetz"]).columns:
        df_load[col] = df_load[col].apply(
            lambda ts: ts.isoformat() if pd.notna(ts) else None
        )

    rows: list[tuple[Any, ...]] = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df_load.itertuples(index=False, name=None)
    ]

    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            execute_values(cur, sql, batch)
            total += len(batch)
        conn.commit()

    logger.info("Postgres upsert: %d rows into %s.%s", total, schema, table)
    return total


def get_postgres_columns(
    conn: psycopg2.extensions.connection,
    schema: str,
    table: str,
) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        return {row[0] for row in cur.fetchall()}
```

---

## state.py — Checkpoint and Last-Run Timestamp Management

```python
"""
Persist sync state between pipeline runs.

State file format (JSON):
{
  "last_run_ms": 1700000000000,    # Unix ms UTC of last successful CDC completion
  "last_backfill_cursor": "abc",   # search API cursor for in-progress backfill (null if complete)
  "last_schema_hash": "sha256:..." # hash of HubSpot property list at last schema sync
}
"""
import json
import hashlib
import logging
import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = "/tmp/hubspot_sync_state.json"


def load_state(path: str = DEFAULT_STATE_FILE) -> dict:
    try:
        with open(path) as f:
            state = json.load(f)
        logger.info("Loaded sync state: last_run_ms=%s", state.get("last_run_ms"))
        return state
    except FileNotFoundError:
        logger.info("No state file found at %s — starting fresh", path)
        return {}


def save_state(state: dict, path: str = DEFAULT_STATE_FILE) -> None:
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    logger.debug("Saved sync state to %s", path)


def current_ms() -> int:
    return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)


def schema_hash(hubspot_schema: dict[str, str]) -> str:
    """Stable hash of the HubSpot property schema for drift detection."""
    payload = json.dumps(hubspot_schema, sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]
```

---

## Complete Orchestration Script

```python
#!/usr/bin/env python3
"""
hubspot_to_warehouse.py

Full pipeline orchestrator. Run once for initial backfill, then on cron for CDC.

Usage:
  python3 hubspot_to_warehouse.py --target bigquery --mode backfill
  python3 hubspot_to_warehouse.py --target bigquery --mode cdc
  python3 hubspot_to_warehouse.py --target postgres --mode backfill --schema-sync-only

Environment variables required (see .env.example):
  HUBSPOT_ACCESS_TOKEN
  TARGET=bigquery|snowflake|postgres
  GCP_PROJECT, HUBSPOT_DATASET (BigQuery)
  SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, ... (Snowflake)
  PG_DSN (Postgres)
"""
import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from hubspot_sync.rate_limiter import TokenBucket, DailyBudgetExhausted
from hubspot_sync.extract     import backfill_contacts_large, incremental_contacts_since
from hubspot_sync.extract     import poll_contact_deal_associations
from hubspot_sync.schema      import (fetch_hubspot_property_schema, detect_schema_drift,
                                      generate_alter_statements, apply_schema_changes)
from hubspot_sync.transform   import build_contacts_dataframe, build_associations_dataframe
from hubspot_sync.state       import load_state, save_state, current_ms, schema_hash

PROPERTIES = [
    "email", "firstname", "lastname", "phone", "company",
    "lifecyclestage", "hs_lead_status", "hubspot_owner_id",
    "hs_lastmodifieddate", "hs_createdate",
    "num_associated_deals", "hs_email_optout",
]


def get_warehouse_connector(target: str):
    if target == "bigquery":
        from google.cloud import bigquery
        from hubspot_sync.load_bigquery import upsert_to_bigquery, get_bigquery_columns
        bq = bigquery.Client(project=os.environ["GCP_PROJECT"])
        project = os.environ["GCP_PROJECT"]
        dataset = os.environ.get("HUBSPOT_DATASET", "hubspot_raw")

        def upsert(df, table="contacts"):
            return upsert_to_bigquery(df, bq, project, dataset, table)

        def get_cols(table="contacts"):
            return get_bigquery_columns(bq, project, dataset, table)

        def alter(stmts):
            # BigQuery DDL is run via the query API, not a cursor
            for stmt in stmts:
                bq.query(stmt).result()

        return upsert, get_cols, alter

    elif target == "snowflake":
        import snowflake.connector
        from hubspot_sync.load_snowflake import upsert_to_snowflake, get_snowflake_columns
        conn = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
            schema=os.environ.get("SNOWFLAKE_SCHEMA", "HUBSPOT_RAW"),
        )
        schema = os.environ.get("SNOWFLAKE_SCHEMA", "HUBSPOT_RAW")

        def upsert(df, table="contacts"):
            return upsert_to_snowflake(df, conn, schema, table)

        def get_cols(table="contacts"):
            return get_snowflake_columns(conn, schema, table)

        def alter(stmts):
            cur = conn.cursor()
            for stmt in stmts:
                cur.execute(stmt)
            conn.commit()
            cur.close()

        return upsert, get_cols, alter

    elif target == "postgres":
        import psycopg2
        from hubspot_sync.load_postgres import upsert_to_postgres, get_postgres_columns
        conn = psycopg2.connect(os.environ["PG_DSN"])
        schema = os.environ.get("PG_SCHEMA", "hubspot")

        def upsert(df, table="contacts"):
            return upsert_to_postgres(df, conn, schema, table)

        def get_cols(table="contacts"):
            return get_postgres_columns(conn, schema, table)

        def alter(stmts):
            with conn.cursor() as cur:
                for stmt in stmts:
                    cur.execute(stmt)
            conn.commit()

        return upsert, get_cols, alter

    else:
        raise ValueError(f"Unknown target: {target}")


def run(args):
    token   = os.environ["HUBSPOT_ACCESS_TOKEN"]
    limiter = TokenBucket(daily_budget=400_000)
    state   = load_state()

    upsert, get_cols, apply_alter = get_warehouse_connector(args.target)

    # --- Schema sync (always runs before data load) ---
    logger.info("Running schema sync...")
    hs_schema       = fetch_hubspot_property_schema(token)
    warehouse_cols  = get_cols("contacts")
    added, removed  = detect_schema_drift(hs_schema, warehouse_cols)

    if added:
        stmts = generate_alter_statements(
            f"{'hubspot.' if args.target == 'postgres' else ''}contacts",
            added,
            dialect=args.target,
        )
        apply_alter(stmts)
        logger.info("Applied %d ALTER TABLE statements", len(stmts))

    if removed:
        logger.warning("Removed properties (manual review required): %s", removed)

    # Store schema hash so we can detect drift on next run without a full API call
    state["last_schema_hash"] = schema_hash(hs_schema)

    if args.schema_sync_only:
        save_state(state)
        logger.info("Schema sync only — exiting")
        return

    # --- Data load ---
    try:
        if args.mode == "backfill":
            logger.info("Starting backfill...")
            import datetime
            portal_created = datetime.datetime(2020, 1, 1)  # adjust to your portal creation date
            for page in backfill_contacts_large(token, PROPERTIES, limiter, portal_created):
                df = build_contacts_dataframe(page, PROPERTIES, hs_schema)
                upsert(df, "contacts")

                # Association CDC on each page of contacts
                contact_ids = [r["id"] for r in page]
                assoc_map   = poll_contact_deal_associations(token, contact_ids, limiter)
                assoc_df    = build_associations_dataframe(assoc_map)
                if not assoc_df.empty:
                    upsert(assoc_df, "contact_deal_associations")

        elif args.mode == "cdc":
            since_ms = state.get("last_run_ms", 0)
            logger.info("CDC since %d ms", since_ms)
            run_start_ms = current_ms()

            for page in incremental_contacts_since(token, since_ms, PROPERTIES, limiter):
                df = build_contacts_dataframe(page, PROPERTIES, hs_schema)
                upsert(df, "contacts")

                contact_ids = [r["id"] for r in page]
                assoc_map   = poll_contact_deal_associations(token, contact_ids, limiter)
                assoc_df    = build_associations_dataframe(assoc_map)
                if not assoc_df.empty:
                    upsert(assoc_df, "contact_deal_associations")

            state["last_run_ms"] = run_start_ms   # advance watermark only on full success

    except DailyBudgetExhausted as e:
        logger.error(str(e))
        save_state(state)
        sys.exit(2)   # exit code 2 signals quota exhaustion to the orchestrator

    save_state(state)
    logger.info("Pipeline complete")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["bigquery", "snowflake", "postgres"], required=True)
    p.add_argument("--mode", choices=["backfill", "cdc"], default="cdc")
    p.add_argument("--schema-sync-only", action="store_true")
    run(p.parse_args())
```

---

## Monitoring Recommendations

Log these events to detect extraction failures before they become silent data gaps:

| Event | Log level | Action |
|---|---|---|
| Daily budget > 80% consumed | WARN | Alert on-call; consider pausing backfill |
| Daily budget exhausted | CRITICAL | Stop pipeline; alert; resume next UTC midnight |
| Schema drift detected (added columns) | WARN | Auto-apply ALTER; confirm in warehouse |
| Schema drift detected (removed columns) | WARN | Manual review required; no auto-drop |
| CDC watermark advancing < 1M records/day | INFO | Normal for small portals |
| Association batch returning fewer IDs than input | INFO | Expected for contacts with no deals |
| Stale checkpoint (backfill cursor > 7 days old) | ERROR | Cursor expired; discard checkpoint and restart |
| Backfill window producing 0 records | DEBUG | Empty time window; normal for sparse portal history |
