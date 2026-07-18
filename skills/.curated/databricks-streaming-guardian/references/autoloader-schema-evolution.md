# Auto Loader Schema Evolution — Modes, the Restart Loop, and Silent Drift

Auto Loader (`cloudFiles`) ingests files as they land, and the single decision that
governs how it reacts to a new column in the source is
`cloudFiles.schemaEvolutionMode`. Get it wrong in either direction and you pick your
poison: the **default fails the stream on every new column** and needs a restart to
evolve, or the permissive alternative **never fails but silently reshapes your table**
and buries the drift in a rescue column nobody reads.

This reference covers the four evolution modes, the exact failure they throw, the
restart-to-evolve loop that makes the default safe in production, the `schemaHints`
pattern that keeps inference from churning, the `_rescued_data` column and how to
monitor it, and why the `schemaLocation` must be stable and unique per stream.

One nuance up front, because it changes which mode is "default": the default of
`cloudFiles.schemaEvolutionMode` **depends on whether you provide a schema**. With
schema inference (no `.schema(...)` given — the common Auto Loader case) the default
is **`addNewColumns`**. When you *do* pass an explicit schema, the default is
**`none`**. So the "stream stops on every new column" pain is specifically the
schema-inference path, and it is the one most teams hit first.

## Modes at a glance

Read the "stream stops?" column first — it is the availability-vs-drift axis of the
whole feature. A mode that stops is loud and safe-by-default (you *know* the schema
changed); a mode that never stops trades that signal for uptime and pushes the
detection burden onto you.

| Mode | On a new column | Stream stops? | Core tradeoff |
| --- | --- | --- | --- |
| `addNewColumns` *(default, no schema)* | Adds the column to the tracked schema, then **fails** | **Yes** — one failure per new column; restart evolves | Availability blip in exchange for a durable, auto-applied schema update. Safe *only* with an auto-restart. |
| `rescue` | Routes the column's data into `_rescued_data`; schema never changes | **No** | Maximum uptime, but the table shape never grows — new fields are silently sidelined and hidden from every downstream reader. |
| `failOnNewColumns` | **Fails** and does **not** update the schema | **Yes** — stays down until you act | Hard human gate. No silent drift, no auto-evolve — you must edit the schema (or hints) or remove the file before it restarts. |
| `none` | Ignores the column; nothing rescued unless `rescuedDataColumn` is set | **No** | Freezes the schema with zero visibility. New data is dropped on the floor. Rarely what you want unless the schema is contractually fixed. |

## The `cloudFiles.schemaEvolutionMode` modes in detail

**`addNewColumns` — fail once, evolve on restart (the default).** When Auto Loader
reads a record with a field not in the tracked schema, it writes the widened schema
(new columns appended, existing column *types* unchanged) into the schema location and
then **fails the batch** with `UnknownFieldException`. The stream stops. On the next
run it reads the now-updated schema location and processes the new column normally.
The operational tradeoff is a brief per-new-column outage for a schema that evolves
automatically and durably — which is only acceptable if something restarts the stream
for you (next section). Without an auto-restart this mode is a pager at 3 a.m.

```python
df = (spark.readStream
      .format("cloudFiles")
      .option("cloudFiles.format", "json")
      .option("cloudFiles.schemaLocation", "/Volumes/main/ingest/_schemas/orders")
      .option("cloudFiles.schemaEvolutionMode", "addNewColumns")   # default when no schema
      .load("/Volumes/main/ingest/landing/orders"))
```

**`rescue` — never fail, never evolve.** The tracked schema is frozen. Any column that
is new, type-mismatched, or case-mismatched has its data captured in `_rescued_data`
instead of failing the stream. The stream stays green through arbitrary upstream
change. The cost is exactly that silence: the table's columns never grow, so a genuinely
new business field (`shipping_zone`, `tax_id`) lands as an opaque JSON blob in the
rescue column and never becomes a first-class, queryable column until a human notices
and acts. Use it only where you actively monitor `_rescued_data` (below) — otherwise
you have built a drift-hiding machine.

**`failOnNewColumns` — hard stop, no auto-evolve.** The stream fails on a new column
and, unlike `addNewColumns`, does **not** write an updated schema. It will not restart
successfully until you either update the provided schema / `schemaHints` yourself or
remove the offending file from the source. This is the mode for a governed pipeline
where a schema change must be a reviewed human event, not an automatic one. The
tradeoff is availability: the stream is down for as long as the change sits unhandled,
by design.

**`none` — ignore and freeze.** New columns are ignored and their data is dropped;
nothing is rescued unless you separately set the `rescuedDataColumn` option. The stream
does not fail. This is the least-visible mode of all — it combines `rescue`'s uptime
with none of its capture — so reserve it for sources whose schema is truly fixed by
contract. If you are not certain the schema is frozen, `none` will quietly lose data.

## The restart-to-evolve loop (why `addNewColumns` needs a restart, and how to make it safe)

`addNewColumns` cannot apply a new column *within* the running query — the moment it
sees an unknown field it records the widened schema and raises `UnknownFieldException`
to end the batch. Evolution therefore requires the query to **stop and start again** so
it re-reads the updated schema location on the next run. The exception is explicitly
flagged as retryable *(error text is representative — exact class/wording drifts across
DBR versions; do not quote as a literal)*:

```text
org.apache.spark.sql.catalyst.util.UnknownFieldException:
[UNKNOWN_FIELD_EXCEPTION.NEW_FIELDS_IN_RECORD_WITH_FILE_PATH] Encountered unknown
fields during parsing: [ shipping_zone ], which can be fixed by an automatic retry.
```

In production you do **not** babysit this by hand. Run the stream as a Databricks
Job / Lakeflow task with a retry policy, so the failure self-heals: the task restarts,
reads the widened schema, and processes the new column.

```text
# Databricks Job task — let the platform absorb the evolve-and-restart cycle
tasks:
  - task_key: ingest_orders
    max_retries: -1            # unlimited (or a bounded count with a backoff)
    min_retry_interval_millis: 30000
    retry_on_timeout: true
```

The one hard requirement for this to be safe is an **idempotent sink**. Structured
Streaming's checkpoint already gives exactly-once delivery to a Delta sink, so a restart
resumes from the last committed offset — no data loss, no double-write — even though the
batch that saw the new column failed. If you write through `foreachBatch`, you own that
guarantee: make the write idempotent (Delta `MERGE` on a key, or the `txnAppId` /
`txnVersion` idempotent-write options) so a re-run of the same micro-batch cannot
duplicate rows. Get the checkpoint and idempotency right and the restart loop is a
non-event; get it wrong and every schema evolution risks duplicate data.

## `cloudFiles.schemaHints` — pin types so inference doesn't churn or mis-type

Auto Loader infers types from a sample, and for JSON/CSV it infers **every column as a
string** unless `cloudFiles.inferColumnTypes` is `true`. That means an `amount` that
should be `DECIMAL` arrives as `STRING`, and a column that looks integer-ish in the
sample can flip type as new files widen the value range. `schemaHints` lets you assert
the types you already know, overriding inference for exactly those columns while leaving
the rest inferred:

```python
.option("cloudFiles.schemaHints",
        "order_id BIGINT, amount DECIMAL(12,2), created_at TIMESTAMP, "
        "address.zip STRING, tags ARRAY<STRING>")
```

Hints take standard SQL type syntax, address **nested** fields with dot paths
(`address.zip`), and cover complex types (`ARRAY<...>`, `MAP<...>`, `STRUCT<...>`). The
pattern for a stable-but-evolvable schema is: hint the columns you care about (so their
types never churn or mis-infer) and let `addNewColumns` handle genuinely new fields.
Note the interaction with rescue — if the hinted type conflicts with the actual data in
a record (a hint says `INT` but the value is `"N/A"`), that value cannot be parsed into
the hinted type and is routed to `_rescued_data` rather than crashing the parse. Hints
constrain *type*; they do not by themselves add or remove columns.

## `_rescued_data` — what lands there, and why you must watch it

The rescued data column (default name `_rescued_data`, renamable via
`cloudFiles.rescuedDataColumn`) is Auto Loader's catch-all for anything it could not
place in the schema: columns **missing from the tracked schema**, values whose **type
does not match**, and columns whose **case differs** from the schema. It is added by
default under schema inference. Each rescued record is a JSON blob containing the
unparsed columns *and* the source file path, so you can trace a rescued value back to
the file it came from.

The danger is specific to `rescue` mode (and to any hint-driven type mismatch): the
stream stays green while real data quietly accumulates in `_rescued_data`. A non-null
`_rescued_data` is your **only** signal that the upstream shape drifted — an added
field, a renamed key, a type change. Monitor it as a first-class data-quality metric,
not an afterthought:

```sql
-- Alert when rescued rows appear — the drift signal rescue mode otherwise hides
SELECT count(*)                                        AS total_rows,
       count(*) FILTER (WHERE _rescued_data IS NOT NULL) AS rescued_rows,
       round(100.0 * count(*) FILTER (WHERE _rescued_data IS NOT NULL)
             / count(*), 3)                            AS pct_rescued
FROM main.bronze.orders
WHERE _ingest_date = current_date();
```

To find *what* drifted, crack open the JSON — the keys are the columns that got
sidelined, and you can decide whether to promote them (add to `schemaHints` or let
`addNewColumns` evolve) or fix the upstream producer:

```sql
SELECT DISTINCT get_json_object(_rescued_data, '$.columnName'),
       get_json_object(_rescued_data, '$._file_path')
FROM main.bronze.orders
WHERE _rescued_data IS NOT NULL
LIMIT 100;
```

A pipeline running `rescue` mode with no alert on `pct_rescued` is the exact failure
this document warns about: it will run "successfully" for months while silently
dropping every new field into a blob, and the first anyone hears of it is a downstream
consumer asking where the new column went.

## `schemaLocation` — stable and unique per stream

`cloudFiles.schemaLocation` is the directory where Auto Loader persists the inferred
schema and every subsequent evolution. It is **required** whenever you use inference or
`schemaHints`, and it is what makes the restart-to-evolve loop work — the widened schema
that `addNewColumns` writes on failure lives here, and the restarted query reads it back
from here.

Two rules keep it from corrupting your stream:

- **Stable across restarts.** The schema location must survive the query's lifetime —
  it holds the evolution history. Do **not** point it at a scratch path that gets wiped,
  and do not co-locate it somewhere a cleanup job might clear. A common, safe layout is
  a dedicated subdirectory under (or beside) the checkpoint, on a governed UC volume.
- **Unique per stream.** Two different streams must never share one schema location —
  they would clobber each other's tracked schema and interleave unrelated evolutions.
  One stream, one schema location. (In DLT / Lakeflow declarative pipelines this is
  managed for you; when you wire Auto Loader by hand, you own the uniqueness.)

```python
# One dedicated, durable schema dir per stream — never shared, never on scratch
.option("cloudFiles.schemaLocation", "/Volumes/main/ingest/_schemas/orders")
.load("/Volumes/main/ingest/landing/orders")
```

If you move or lose the schema location, Auto Loader re-infers from scratch on the next
run — which can silently re-introduce the very type churn `schemaHints` existed to
prevent. Treat it as durable state, versioned alongside the pipeline.

## Sources

- Databricks — *Configure schema inference and evolution in Auto Loader* (the
  `cloudFiles.schemaEvolutionMode` mode table, default-depends-on-schema-provided
  behavior, `UnknownFieldException` on new columns), docs.databricks.com
  `/ingestion/cloud-object-storage/auto-loader/schema`.
- Databricks — *Auto Loader options* reference (`cloudFiles.schemaLocation`,
  `cloudFiles.schemaHints`, `cloudFiles.inferColumnTypes`, `cloudFiles.rescuedDataColumn`),
  docs.databricks.com `/ingestion/cloud-object-storage/auto-loader/options`.
- Databricks — *What is the rescued data column?* (contents of `_rescued_data`:
  missing / type-mismatched / case-mismatched columns plus source file path),
  docs.databricks.com `/ingestion/cloud-object-storage/auto-loader/schema`.
- Databricks — *Run an Auto Loader stream in production* / Jobs retry policy
  (self-healing restart after a schema-evolution failure; checkpoint exactly-once),
  docs.databricks.com `/ingestion/cloud-object-storage/auto-loader/production`.
- Databricks — *Idempotent writes with `foreachBatch`* (`txnAppId` / `txnVersion`,
  MERGE-on-key) for non-Delta / custom sinks across the restart loop,
  docs.databricks.com `/structured-streaming/delta-lake` and `/foreach-batch`.
