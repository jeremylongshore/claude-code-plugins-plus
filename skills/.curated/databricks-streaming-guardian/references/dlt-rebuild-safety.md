# DLT Rebuild & Refresh Safety — Full-Refresh Is a Loaded Gun

Delta Live Tables (rebranded **Lakeflow Declarative Pipelines**) is declarative: you
describe datasets with `@dlt.table` / `@dlt.view` (Python) or `CREATE OR REFRESH
STREAMING TABLE` / `CREATE MATERIALIZED VIEW` (SQL), and DLT resolves the dependency
graph and runs it for you. That convenience hides two runtime realities that bite
hard — how the graph gets **built** (a side-effect collection pass that is not
thread-safe) and how it gets **rebuilt** (a full refresh that re-reads sources from
scratch and will silently ship an incomplete table if a source has aged out).

Read the failure-mode framing first, same as the upgrade reference. A build-time race
is intermittent but loud once you know the signature — it fails the run. A full
refresh against a non-replayable source is the dangerous class: the pipeline goes
**green**, the table is smaller, and no exception announces the loss. This reference
covers the DLT thread race (D08), the silent full-refresh data drop (D09), the
rebuild cost multiplier (D11), and a pre-flight checklist you run before ever clicking
"Full refresh all."

The sibling cost reference —
`../../databricks-cost-leak-hunter/references/dlt-tier-cost-tradeoffs.md` — owns the
steady-state edition/serverless leak math; this file owns the **rebuild** economics,
which are a different shape.

---

## D08 — The DLT thread race: registering `@dlt.table` from a ThreadPoolExecutor

**The pattern.** A pipeline that generates many tables programmatically — one per
source table, per tenant, per region — from a config list. Someone "speeds up" the
generation by dispatching the registration calls across a `ThreadPoolExecutor`,
reasoning that hundreds of tables should be built in parallel.

**Why it races.** `@dlt.table` does not build anything when it runs. It is a
**registration side effect**: applying the decorator appends a node to the collector
DLT walks during its graph-construction (analysis) phase. DLT executes your module
**once, top to bottom, on the driver**, harvests every registration in that single
pass, then resolves dependencies and executes. That collector is not designed for
concurrent mutation. Dispatch the registrations across threads and they append in
non-deterministic order — nodes land late, a `dlt.read`/`dlt.read_stream` reference
resolves before its target node is registered, and you get dependency-resolution
failures. Because thread-completion order varies run to run, the same code throws
`dataset not found` / `table X is not defined` on some runs and passes on others.

```python
# Anti-pattern: registration dispatched across threads. @dlt.table mutates DLT's
# graph collector as a side effect; ThreadPoolExecutor makes those writes race.
from concurrent.futures import ThreadPoolExecutor
import dlt

def register(name):
    @dlt.table(name=name)                        # side effect: adds a graph node
    def _():
        return dlt.read_stream("bronze_events")

with ThreadPoolExecutor(max_workers=8) as pool:  # <-- the bug
    list(pool.map(register, table_names))        # non-deterministic append order
```

**The fix.** Register **serially**. There is nothing to parallelize at registration
time — the actual data work is Spark's job during graph execution, not during the
metadata pass, so the thread pool buys zero throughput and only introduces the race.
Loop single-threaded, or use metaprogramming DLT sees in one deterministic sequence.
Watch the co-occurring **late-binding closure trap**: a decorated function that closes
over the loop variable will capture its final value unless you bind it as a default
argument (`name=name`).

```python
# Fix: one deterministic registration pass, loop variable bound per iteration.
import dlt

for _name in table_names:                        # single-threaded, stable order
    def _factory(name=_name):                    # bind now, not at call time
        @dlt.table(name=name)
        def _():
            return dlt.read_stream("bronze_events")
    _factory()
```

**Detect.** Grep the pipeline source for `ThreadPoolExecutor`, `ProcessPoolExecutor`,
`asyncio`, `multiprocessing`, or a `.map(`/`concurrent` import in any module that also
defines `@dlt.table`/`@dlt.view`. Any thread that reaches a decorator is a latent
intermittent failure — the absence of a crash on the last run proves nothing.

---

## D09 — Full refresh silently dropping data on a non-replayable source

**What a full refresh does.** A DLT **full refresh** truncates the target and
reprocesses **from scratch**. For a streaming table backed by Auto Loader or Kafka,
that means it **resets the checkpoint** and re-reads the source from its earliest
*currently available* offset — not from the offset it originally started at. That
distinction is the whole bug.

**Streaming table vs materialized view — know which you are rebuilding.** A
**materialized view** already recomputes its full defining query against the current
source snapshot on every refresh, so it is only as complete as its source is *now*. A
**streaming table** accumulates across incremental runs and only re-reads the whole
source on a full refresh. The dangerous combination is a **streaming table whose
streaming source is non-replayable** — full refresh discards the accumulated history
and re-reads a source that no longer holds it.

**How it manifests — a silent runtime regression.** The refresh completes green. The
rebuilt table simply has fewer rows, because the records that aged out of the source
between first ingest and the rebuild are gone forever and nothing errored:

| Source type | Replayable? | Full-refresh result |
| --- | --- | --- |
| Append-only bronze Delta, VACUUM retention ≥ history age | Yes | Faithful rebuild |
| Cloud files via Auto Loader, all source files retained | Yes | Faithful rebuild |
| Kafka topic, retention window < age of first ingest | **No** | Silently drops every record older than retention |
| Truncate-and-load / `overwrite` Delta source | **No** | Rebuilds only the current snapshot; prior history gone |
| Auto Loader dir with lifecycle-expired / deleted files | **No** | Missing the windows whose files were reaped |

**When full refresh is safe.** The source is fully replayable end to end: an
append-only landing/bronze layer you never truncate, with Delta `VACUUM` retention
longer than the history you need; or a cloud storage prefix where every source file is
retained. If you can re-read every byte the table was ever built from, a full refresh
is a faithful rebuild.

**The guard — protect non-replayable tables from reset.** DLT ships a purpose-built
table property. Set `pipelines.reset.allowed = false` on any streaming table whose
source cannot be replayed; a pipeline-wide full refresh then **skips** that table
instead of resetting its checkpoint. This is the primary defense for a Kafka/landing
ingest table.

```sql
-- Full refresh will SKIP this table rather than reset its checkpoint and
-- re-read a Kafka topic that has since aged past its retention window.
CREATE OR REFRESH STREAMING TABLE kafka_ingest
  TBLPROPERTIES ('pipelines.reset.allowed' = 'false')
AS SELECT * FROM STREAM read_kafka(/* ... */);
```

```python
# Same guard in Python.
@dlt.table(
    name="kafka_ingest",
    table_properties={"pipelines.reset.allowed": "false"},
)
def kafka_ingest():
    return spark.readStream.format("kafka").options(**kafka_opts).load()
```

**The other two guards.** Snapshot before you refresh, and refresh narrowly:

```sql
-- Cheap metadata-only snapshot before any refresh you are unsure about.
CREATE TABLE recovery.kafka_ingest_20260712 DEEP CLONE main.silver.kafka_ingest;
```

```text
# Full-refresh ONLY the tables whose sources you KNOW are replayable — a bare
# full_refresh:true resets EVERY streaming table in the pipeline at once.
POST /api/2.0/pipelines/{pipeline_id}/updates
{ "full_refresh_selection": ["dim_customer", "fct_orders"] }
```

---

## D11 — DLT tier / serverless cost, and why a rebuild multiplies it

**The steady-state tiers (cross-referenced, not duplicated).** DLT bills a DBU premium
over the underlying compute, scaled by **product edition** — `CORE` (streaming +
transforms) < `PRO` (adds `APPLY CHANGES` CDC) < `ADVANCED` (adds data-quality
expectations). Serverless DLT removes cluster management and reprices the DBU. Exact
per-DBU rates and the edition premium multipliers are the sibling cost reference's job
and drift with the price sheet — *(verify against the current Databricks pricing
page for your cloud and region)*. What matters here is the **cost shape of a
rebuild**, which the steady-state view does not capture.

**Why a rebuild multiplies compute.** An incremental run processes one increment; a
full refresh reprocesses **all history**. The rebuild bill is not "a bit more" — it is
the normal-run cost scaled by how much history you are re-reading:

```text
# Rebuild cost  ≈  normal-run cost  ×  (total history reprocessed / typical increment)
#
#   incremental run : processes ~1 day of data      ->  D DBUs
#   full refresh    : reprocesses ~2 years of data  ->  ~730 × D DBUs  (one-off spike)
#
# then multiplied again by:
#   - edition premium        (CORE  <  PRO  <  ADVANCED)
#   - serverless DLT DBU rate (if the pipeline runs serverless)
#   - Photon                 (rides on top where enabled)
```

**The compounding traps.** A whole-pipeline full refresh reprocesses every table's
full history at once, so the multiplier hits the entire DAG simultaneously — a large,
concentrated, one-off spend that a cost dashboard will read as a spike with no obvious
cause. A pipeline sitting on `ADVANCED` it does not need, or on serverless when a
scheduled classic-Jobs backfill would be cheaper, pays that premium **on every row of
history** during the rebuild, not just on the daily increment. Before a large rebuild,
right-size the edition to what the pipeline's features actually require and estimate
`history_volume × edition_rate` up front rather than discovering it on the invoice.

---

## Before you full-refresh — the rebuild-safety checklist

Run this before any full refresh or pipeline rebuild. If any answer is "no" or
"unsure," stop and fix it first — the refresh is one-way once the source has moved on.

- **Is every source replayable?** For each streaming source: is the Kafka retention
  window longer than the age of the oldest data the table holds? Is the Delta source
  append-only with `VACUUM` retention ≥ the history you need (not truncate-and-load,
  not `overwrite`)? Are all Auto Loader source files still present (no storage
  lifecycle expiry)? A single non-replayable source makes the whole refresh lossy.
- **Are the non-replayable tables protected?** Any streaming table you cannot replay
  must carry `pipelines.reset.allowed = false` so a pipeline-wide full refresh skips
  it instead of resetting its checkpoint.
- **Have you snapshotted?** `DEEP CLONE` (or verify Delta time-travel retention covers)
  every target you are about to reset, so a bad rebuild is recoverable.
- **Can you refresh narrowly?** Prefer `full_refresh_selection` over a blanket
  `full_refresh: true` — refresh only the replayable tables and leave accumulating
  streaming tables untouched.
- **Is the sink idempotent / rebuild-tolerant?** Will downstream consumers survive the
  target being truncated and repopulated? Do `APPLY CHANGES` (CDC) targets re-key
  correctly on replay? Is there any exactly-once or append-tracking consumer that will
  double-count or gap when the table is rebuilt?
- **What is the recompute cost?** Estimate `history_volume × edition/compute_rate`
  before you click. Right-size the edition (drop `ADVANCED`/`PRO` if unused) and pick
  classic vs serverless deliberately for a one-off backfill.
- **Is registration deterministic?** If the pipeline generates tables
  programmatically, confirm registration is single-threaded (D08) so the rebuilt graph
  is stable — a full refresh is the worst time to hit an intermittent build-order race.

---

## Sources

- Databricks — *Delta Live Tables / Lakeflow Declarative Pipelines: how updates work*
  (full refresh re-reads sources from scratch; streaming tables reset their checkpoint,
  materialized views recompute against the current source snapshot),
  docs.databricks.com `/dlt/updates`.
- Databricks — *Prevent tables from being reset during a full refresh* (the
  `pipelines.reset.allowed = false` table property), docs.databricks.com
  `/dlt/full-refresh`.
- Databricks — *Programmatically create multiple tables / load data with DLT* (the
  loop-plus-closure metaprogramming pattern for generating datasets; register in a
  single deterministic pass), docs.databricks.com `/dlt/python-ref`.
- Databricks — *Auto Loader* and *Structured Streaming from Delta tables*
  (`ignoreChanges` / `skipChangeCommits`; append-only source requirement, why
  truncate-and-load and expired-file sources are non-replayable), docs.databricks.com
  `/ingestion/auto-loader` + `/structured-streaming/delta-lake`.
- Databricks — *DLT product editions* (`CORE` / `PRO` / `ADVANCED` feature and DBU-
  premium tiers) and *Serverless DLT pricing*, docs.databricks.com `/dlt/configure`
  and databricks.com/product/pricing — *(verify exact per-DBU rates and premium
  multipliers against the live price sheet for your cloud/region)*.
- Databricks — *Pipelines REST API: start update* (`full_refresh`,
  `full_refresh_selection`, `refresh_selection` fields for scoping a refresh),
  docs.databricks.com `/api/workspace/pipelines/startupdate`.
