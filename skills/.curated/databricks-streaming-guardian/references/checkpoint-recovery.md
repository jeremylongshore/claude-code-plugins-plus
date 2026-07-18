# Structured Streaming Checkpoint Failure Recovery

A Structured Streaming checkpoint is the query's durable memory: it records how far
the stream has read, what it has committed, and the identity of the source it read
from. When something the checkpoint points at disappears or changes underneath it,
the query does not degrade gracefully — it dies with a terse error, and the operator
is left deciding between three recovery paths that trade data loss against
duplication in different ways. This guide covers the three checkpoint failures that
account for most streaming incidents, then unifies them into one decision tree.

The three failures look unrelated but share one root: the checkpoint pins to
**concrete file paths** and to the **source table's identity (UUID)**, not to a
logical "where I am in this table" position. Anything that rewrites files, deletes
files, or mints a new table UUID breaks that pin. Error strings quoted below are
verbatim from the Databricks KB / community reports cited in Sources — match on the
bracketed error class (`DELTA_FILE_NOT_FOUND_DETAILED`,
`DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`), which is stable, not the
surrounding prose, which drifts across DBR versions.

## How a Structured Streaming checkpoint works

Every streaming query with a `checkpointLocation` maintains four subdirectories
under that path. Reading them is the whole of checkpoint forensics:

- `offsets/` — a write-ahead log. Before a micro-batch runs, the engine writes the
  range of offsets it plans to process to `offsets/<batchId>`. This is written
  **first**, ahead of any output.
- `commits/` — a completion marker written to `commits/<batchId>` **after** the
  batch's output is durably written. A batch with an `offsets/` entry but no
  matching `commits/` entry is the one that was in flight when the query stopped;
  it re-runs on restart.
- `sources/` — per-source metadata. For a Delta source, `sources/0/0` holds the
  initial snapshot / starting-offset record for source index 0. This file's
  disappearance is the D04 signature.
- `state/` — the state store (RocksDB or HDFS-backed) for stateful operators
  (aggregations, stream-stream joins, `dropDuplicatesWithinWatermark`). Empty for
  stateless append pipelines.

Batch IDs are **monotonic integers**. The highest-numbered file in `offsets/` and
`commits/` is the query's position. Two invariants let you diagnose almost any
checkpoint fault by listing these directories:

- The batch ID never goes backward. A restart that reports a lower `batchId` than
  you have seen before means the checkpoint lost its place — corruption or reset.
- `commits/<n>` implies `offsets/<n>` exists. A gap in the monotonic sequence, or an
  `offsets/` entry far ahead of the last `commits/` entry, is a discontinuity worth
  investigating.

For a **Delta source specifically**, the offset log stores the source table's
`reservoirId` — the table UUID minted when its `_delta_log` was created — plus the
Delta version and file index the stream has reached. Two consequences drive all three
pains below: the recorded position references files **by path**, so an OPTIMIZE
rewrite plus a VACUUM delete leaves it dangling (**D03**); and it is bound to that
**UUID**, so a `CREATE OR REPLACE` under the same name no longer matches (**D12**).

## D03 — `DELTA_FILE_NOT_FOUND_DETAILED` after VACUUM

**Symptom (verbatim):**

```
[DELTA_FILE_NOT_FOUND_DETAILED] File abfss://<storage>.dfs.core.windows.net/
<path>/part-xxxx-c000.snappy.parquet referenced in the transaction log
cannot be found.
```

The older form is a raw `FileNotFoundException: ... doesn't exist`, which can fire
even with `ignoreMissingFiles=true` set — that option is documented as not reliably
covering this case.

**The chain that gets you here.** Three background operations that are individually
healthy combine into a failure:

1. The streaming checkpoint records a position that references specific Parquet file
   paths in the source table.
2. `OPTIMIZE` (bin-packing or Z-ORDER) rewrites those small files into new, larger
   files at **new paths**, creating a new Delta version. The old files are now
   tombstoned but still on disk.
3. `VACUUM` — default retention 7 days — later deletes the tombstoned originals. The
   moment it runs, any checkpoint still pointing at those paths is dangling.

The trigger is the stream falling behind the OPTIMIZE-plus-VACUUM cycle: a cluster
restart, a late start, a paused pipeline, or a traffic spike that pushes the last
successful commit older than `deletedFileRetentionDuration`. A stream that stays
caught up never references a file old enough to be VACUUMed.

**Decision tree.** Establish two numbers first: the source's oldest available version
(`DESCRIBE HISTORY <table>` — the lowest version still readable) and the version your
checkpoint last committed. Then:

- **Checkpoint version is at or newer than the oldest available version** — the data
  you need still exists; this is a stale-metadata / dangling-pointer case, not true
  data loss. Try `FSCK REPAIR TABLE <table>` to prune references to files that no
  longer exist, then restart. This is Tier 1 (safe restart) if it clears.
- **Checkpoint version is older than the oldest available version** — the files you
  had not yet read are gone. You cannot avoid a gap. Restart from a **fresh
  checkpoint** with `startingVersion` pinned to the oldest available version, and
  accept that rows between your last commit and that version are lost unless you can
  backfill them from an upstream system. This is Tier 2 / Tier 3 territory — dedup
  downstream because reprocessing overlaps already-emitted rows.
- **You need exact continuity and have a Delta time-travel window** — if the source
  still has the version you were at (retention was long enough), you may restart
  from a fresh checkpoint with `startingVersion` set to your last-committed version,
  reprocessing forward with an idempotent sink.

`startingVersion` / `startingTimestamp` are honored **only when the checkpoint has no
prior offset log** — set them on a fresh checkpoint location; they are ignored once a
checkpoint exists.

**Prevention (do this instead of recovering).** Align VACUUM retention with streaming
lag, not with a default:

```sql
ALTER TABLE bronze.events SET TBLPROPERTIES (
  'delta.deletedFileRetentionDuration' = 'interval 30 days',
  'delta.logRetentionDuration'         = 'interval 30 days'
);
```

Do not VACUUM streamed-from tables aggressively, and do not tune retention below your
worst-case streaming outage. `OPTIMIZE` less frequently on hot streaming sources —
every OPTIMIZE creates the tombstones VACUUM later reaps.

## D04 — silent checkpoint corruption / reset to batch 0

**Symptom (verbatim, community report):**

```
StreamingQueryException: [STREAM_FAILED] Query [id = ..., runId = ...] terminated with exception:
dbfs:/mnt/path/my_table/sources/0/0 doesn't exist
```

A job healthy for months suddenly fails, or restarts and reports `batchId` resetting
from (for example) 711 back to 0. The `sources/`, `offsets/`, and `commits/`
directories stop advancing. There is often **no documented root cause** — this is the
one pain in this file that is a genuine platform-bug class, not a design surprise.
Contributing factors seen in the wild: a DBFS/S3 lifecycle policy silently deleting
checkpoint files, or metadata corruption after a cluster restart or rare DBR upgrade.

**Detect it — do not wait for the crash.** A batch-ID regression is the tell. Two
surfaces expose it:

- **Programmatic (ground truth):** the query's `StreamingQueryProgress`. Read
  `query.lastProgress.batchId` (or subscribe a `StreamingQueryListener` and watch
  `onQueryProgress`). A `batchId` lower than one you have already recorded, or a
  query stuck at `numInputRows = 0` for longer than its trigger interval, is the
  signature.
- **Workspace-wide:** the streaming query-progress system view
  (`system.streaming.query_progress` where available in your workspace — verify, as
  availability varies by DBR/enablement). Trend `batch_id` per `run_id`; a
  non-monotonic series is a corruption candidate.

Corroborate by listing `offsets/` and `commits/` under the checkpoint: the highest
integer filename is the true last position. If it is far below the batch ID the job
was last known to be at — or the directory is empty — the checkpoint is gone.

**Recover.** There is no in-place repair for a corrupt checkpoint. You restart with a
new checkpoint location and re-establish position deterministically:

- Pin the restart to a known-good starting position — `startingVersion` (or
  `startingTimestamp`) set to a Delta version you can prove you had already processed
  cleanly. This is the Delta-source analog of Kafka's `startingOffsets`: a concrete,
  operator-chosen point, never `startingOffsets = latest` on a table you have not
  reconciled (that silently drops the gap).
- **Validate the sink is idempotent before you restart**, because a checkpoint reset
  converts an exactly-once guarantee into at-least-once — the overlap between your
  pinned version and the old position **will** be reprocessed. An idempotent sink
  absorbs the duplicates:

```python
def upsert(microBatchDF, batchId):
    (deltaTable.alias("t")
       .merge(microBatchDF.alias("s"), "t.id = s.id")
       .whenNotMatchedInsertAll()
       .execute())

stream.writeStream.foreachBatch(upsert).option("checkpointLocation", NEW_PATH).start()
```

For a plain Delta append sink, the built-in idempotent-write options
(`.option("txnAppId", appId).option("txnVersion", batchId)`) let Delta skip a
`(appId, batchId)` pair it has already committed — reprocessing the same batch is a
no-op rather than a duplicate.

## D12 — `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`

**Symptom (verbatim):**

```
[STREAM_FAILED] Query [id = <query-id>, runId = <run-id>] terminated with exception:
[DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE] The streaming query was reading from
an unexpected Delta table (id = '<id>'). It used to read from another Delta table
(id = '<other-id>') according to checkpoint.
```

**Why it happens.** The checkpoint pins to the source table's UUID (`reservoirId`,
set when `_delta_log` is created), not to its name. `CREATE OR REPLACE TABLE`, and
`DROP TABLE` followed by `CREATE TABLE`, both mint a **new** UUID even when the name
is byte-identical. The instant a producer runs that migration, **every** active
streaming consumer of the table dies on its next batch, because the UUID in its
checkpoint no longer matches the UUID on disk. This is intentional safety — it stops
a stream from silently consuming unrelated data that happened to reappear under the
same name — but it makes `CREATE OR REPLACE` a cross-team footgun: the producer team
believes they changed nothing, while the consumer team scrambles.

**Prevention is the only clean answer — this is what the skill's PreToolUse hook
blocks.** Never `CREATE OR REPLACE` (or drop-and-recreate) a table that any stream
reads from. Migrate the table **in place**, preserving its UUID:

- Schema changes — `ALTER TABLE ... ADD COLUMN` / `DROP COLUMN` / `RENAME COLUMN`, or
  enable column mapping; never replace the table to change its schema.
- Full data rebuild — `TRUNCATE TABLE` then `INSERT`, or a `MERGE`, both of which
  keep the `_delta_log` (and UUID) intact.
- If you genuinely must stand up a new table, do the clone-and-swap **knowing the new
  table has a new UUID**, and plan the consumer restart as part of the migration —
  the swap is not transparent to streams.

The PreToolUse hook enforces this by querying the workspace for streaming queries
currently consuming the target table and blocking the DDL if any active consumer
exists, naming them by owner so the migration becomes a coordinated change rather
than a surprise outage.

**Recover (when the migration already ran).** There is no automatic recovery and no
way to re-point an existing checkpoint at a new UUID. Restart each consumer against a
**fresh checkpoint location**, choosing a starting position on the new table
(`startingVersion` / `startingTimestamp`), and dedup downstream — the new table has
no shared history with the consumer's old position, so treat this as a full reset
(Tier 3) with idempotent-sink dedup mandatory.

## Three-tier recovery decision tree

Every checkpoint incident resolves to one of three tiers. Choose the **lowest** tier
whose precondition holds — the cost and duplication risk climb with the tier.

**Tier 1 — safe restart (no data impact).** The checkpoint is intact and monotonic,
and every file / version it references still exists on the source. Just restart the
query; it resumes from the last `commits/` entry, re-running only the in-flight
batch. The re-run of one uncommitted batch is idempotent by design.

- Applies to: transient failures (node loss, spot reclaim, a passing cloud blip);
  D03 cases where `FSCK REPAIR TABLE` clears a stale pointer and the data survives.
- Tradeoff: none. No loss, no duplication.

**Tier 2 — offset / reprocess (bounded reprocessing).** The source table still exists
with the same UUID and a readable history window, but the exact files or the exact
position are gone. Restart from a **fresh checkpoint** with `startingVersion` pinned
to a known-good version, reprocessing forward.

- Applies to: D03 where the checkpoint fell behind VACUUM but recent versions are
  still available.
- Tradeoff: pin **at or before** your last-committed version and you lose nothing but
  emit duplicates for the overlap — safe **only** with an idempotent sink (MERGE, or
  `txnAppId`/`txnVersion`). Pin **after** the last commit and you skip — and
  permanently lose — the gap. When in doubt, pin earlier and dedup.

**Tier 3 — full checkpoint reset + backfill (maximum reprocessing).** No salvageable
position: the checkpoint is corrupt (D04) or the source UUID changed (D12). Start a
fresh checkpoint from the earliest available version, or run a separate batch
backfill of the historical gap, then let the stream take over the tail.

- Applies to: D04 corruption / batch-0 reset; D12 after a `CREATE OR REPLACE`.
- Tradeoff: highest cost and the largest duplicate volume — dedup downstream is
  **not optional**. Loss risk if you shortcut by pinning to `latest` to skip the
  backfill; that trades the reprocessing cost for a silent data hole. The exactly-once
  guarantee is gone the moment the checkpoint resets — correctness now depends
  entirely on the sink being idempotent.

The through-line across all three tiers: **the sink's idempotency is what makes any
non-trivial recovery safe.** Tier 1 preserves exactly-once for you; Tiers 2 and 3
downgrade the pipeline to at-least-once, so a `MERGE`-based or `txnAppId`/`txnVersion`
sink is the difference between clean recovery and a polluted downstream table. Verify
it before you reset a checkpoint, not after.

## Sources

- Databricks — *Structured Streaming checkpoints* (checkpoint directory layout,
  `offsets` / `commits` / `sources` / `state`, restart semantics),
  docs.databricks.com structured-streaming reference.
- Databricks — *Recover a pipeline from a streaming checkpoint failure* (the
  documented three-tier recovery framing), docs.databricks.com.
- Databricks KB — *Delta table as a streaming source returns
  `DELTA_FILE_NOT_FOUND_DETAILED` even though no user or lifecycle rule deleted files*
  (D03 root cause: OPTIMIZE + VACUUM vs checkpoint file-path pin).
- Databricks KB — *`FileNotFoundException` while streaming even with
  `ignoreMissingFiles` set* (D03 older-form error, mitigation gap).
- community.databricks.com — *Spark streaming checkpoint corrupted* (D04 batch-ID
  reset with no clean root cause; `sources/0/0 doesn't exist`).
- Databricks KB — *Streaming job failing with
  `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`* (D12 UUID pin vs
  `CREATE OR REPLACE`).
- Databricks — *VACUUM* and *Delta retention* (`deletedFileRetentionDuration`,
  `logRetentionDuration`, `delta.retentionDurationCheck.enabled`), docs.databricks.com.
- Databricks — *Idempotent writes to Delta tables* (`txnAppId` / `txnVersion`) and
  *`foreachBatch`* upsert / MERGE patterns, docs.databricks.com structured-streaming.
- Databricks — *Delta table streaming reads* (`startingVersion` / `startingTimestamp`
  honored only on a fresh checkpoint; `skipChangeCommits`), docs.databricks.com.
