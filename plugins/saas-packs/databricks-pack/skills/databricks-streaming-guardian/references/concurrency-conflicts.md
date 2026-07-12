# Delta Lake Write-Conflict Resolution — OCC, Compaction Collisions, and Liquid Clustering

A Delta write conflict is not a lock timeout and not a deadlock — Delta takes no
locks. It is an **optimistic concurrency control (OCC)** failure: two writers each
read the same table version, each plan a change, and both try to commit the next
version. One wins; the other must prove its change does not collide with the winner's
before it can rebase and retry. When that proof fails, the loser throws a
`Concurrent*Exception` and the whole operation aborts — the application, not Delta,
must retry it. This reference explains what "collide" actually means at the file
level, then catalogs the two conflict classes that bite hardest in production:
`ConcurrentDeleteDeleteException` from a manual `OPTIMIZE` racing auto compaction
(D01), and `ConcurrentAppendException` that appears the day you migrate a table to
Liquid Clustering (D02). Each carries how it manifests, how to detect it before it
pages you, and the exact mitigation.

## The OCC commit protocol — what a "conflict" actually is

A Delta table is an ordered log of commits under `_delta_log/`: each commit is a
zero-padded JSON file (`00000000000000000042.json`) holding a set of **actions** —
`AddFile` (a data file now part of the table), `RemoveFile` (a data file tombstoned
out), plus metadata/protocol changes. The current table state is the log replayed to
the highest version.

A writer does three things:

- Reads the snapshot at version `N` and records its **read set** (the data files it
  scanned to evaluate its predicate) and its **write set** (the files it will add and
  the files it will remove).
- Stages its new data files.
- Attempts to commit as version `N+1` by atomically creating `...N+1.json`. That
  atomic put-if-absent of the next log file is the single serialization point — only
  one writer can create version `N+1`.

If a writer loses that race because another commit landed `N+1` first, it does **not**
blindly fail. Delta runs **conflict detection**: it reads the winning commit's actions
and checks them against this transaction's read/write set. If the file sets are
disjoint and no metadata/protocol change intervened, the loser transparently rebases
onto `N+1` and retries its commit as `N+2` — the caller never sees it. It throws only
when the overlap violates the isolation guarantee.

So a conflict is precise: **two commits that raced for adjacent versions whose file
sets overlap in a way the isolation level forbids.** It is a **file-level** decision,
not a row-level one — two writers editing different rows that happen to live in the
same Parquet file conflict, unless row-level concurrency (below) is in play.

Two isolation levels govern which overlaps are legal, set per table:

```sql
-- Default is WriteSerializable; Serializable is stricter (and conflicts more):
ALTER TABLE fact_sales SET TBLPROPERTIES ('delta.isolationLevel' = 'Serializable');
```

Under **WriteSerializable** (the default), a blind append (`INSERT`) is allowed to not
conflict with a concurrent `UPDATE`/`DELETE`/`MERGE` that read the region it appended
to. Under **Serializable**, that same pair can conflict, because Serializable demands
the outcome match some strict serial order of all writes. Read-modify-write operations
(`UPDATE`/`DELETE`/`MERGE`) and compaction (`OPTIMIZE`) can conflict under **both**
levels — those are the classes below.

**Row-level concurrency** (GA on Databricks Runtime 14.2+, automatic on tables with
deletion vectors enabled) narrows conflict detection from the file to the row: two
operations that touch **different rows** of the same file no longer collide, which
erases many `ConcurrentAppendException` / `ConcurrentDeleteReadException` cases. It
does **not** help the `OPTIMIZE`-vs-`OPTIMIZE` case in D01 — compaction rewrites whole
files by definition, so there is no row-level disjointness to exploit.

## D01 — ConcurrentDeleteDeleteException: manual OPTIMIZE colliding with auto compaction

**What it is.** `OPTIMIZE` is bin-packing compaction: it reads many small files and
rewrites them into fewer large ones, which means it issues `RemoveFile` for every
small file it consumed. **Auto compaction** does the identical thing automatically as
a post-commit hook after a write. When both compact the **same** files, each plans to
remove files the other is also removing. The loser of the commit race finds its
tombstone targets already tombstoned and throws:

```text
ConcurrentDeleteDeleteException: This transaction attempted to delete one or more
files that were deleted (for example <file>) by a concurrent update.
```

**The trap.** Auto compaction is easy to have on without knowing it. It is enabled by
the table property `delta.autoOptimize.autoCompact`, **or** cluster/session-wide by
`spark.databricks.delta.autoCompact.enabled` (`true`/`auto`) — and it fires as a
post-commit hook after `MERGE`/`UPDATE`/`DELETE`/streaming writes that leave many
small files. A team then adds a nightly scheduled `OPTIMIZE` for clustering
maintenance, the two overlap on a hot partition, and the job dies intermittently.
Note the two run to different targets — auto compaction packs to ~128 MB
(`spark.databricks.delta.autoCompact.maxFileSize`), manual `OPTIMIZE` to ~1 GB
(`spark.databricks.delta.optimize.maxFileSize`) — so they are not even redundant work,
they are two compactors fighting.

**Detect it — before you schedule OPTIMIZE.** The property is not always visible where
you look. Check all three scopes:

```sql
-- Table-scoped auto compaction (the common silent case):
SHOW TBLPROPERTIES fact_sales;
-- Flag if present and true:
--   delta.autoOptimize.autoCompact   = true
--   delta.autoOptimize.optimizeWrite = true
```

```sql
-- Same properties plus numFiles, the fragmentation OPTIMIZE would target:
DESCRIBE DETAIL fact_sales;
-- properties column carries delta.autoOptimize.*; numFiles shows small-file count
```

```sql
-- Cluster / session-scoped auto compaction — NOT shown by SHOW TBLPROPERTIES,
-- so a table can auto-compact even with no table property set:
SET spark.databricks.delta.autoCompact.enabled;
```

**Mitigation — pick one compactor, never two.**

- If auto compaction is on and adequate, **do not** also run scheduled `OPTIMIZE` on
  that table. Auto compaction handles small-file cleanup and retries its own hook.
- If you need scheduled `OPTIMIZE` (for example to re-cluster), **disable** table auto
  compaction so only your job compacts, and run it in a window with no writers:

```sql
ALTER TABLE fact_sales SET TBLPROPERTIES ('delta.autoOptimize.autoCompact' = 'false');
-- then run OPTIMIZE when ingestion is paused / off-peak:
OPTIMIZE fact_sales;
```

- If you cannot pause writers, **serialize** maintenance: run `OPTIMIZE` from a single
  scheduled job (never two overlapping ones), and wrap it in retry-with-backoff so a
  rare collision with a straggler write self-heals rather than failing the run.

## D02 — ConcurrentAppendException after migrating to Liquid Clustering

**What it is.** `ConcurrentAppendException` is thrown when a concurrent operation
**adds files** to a region of the table that the current read-modify-write operation
(`MERGE`/`UPDATE`/`DELETE`) **read** to evaluate its condition:

```text
ConcurrentAppendException: Files were added to the root of the table by a concurrent
update. Please try the operation again.
```

The classic advice is "make the separation explicit in the operation's condition." On
a **partitioned** table that is nearly automatic: a `MERGE` whose `ON` clause pins a
partition column (`t.region = 'EMEA'`) reads only that partition's directory, so
fan-out MERGEs into different partitions read disjoint file sets and never conflict.

**The surprise with Liquid Clustering (LC).** LC removes hive-style partition folders.
It clusters rows by the clustering keys into a single logical file space and prunes via
**file-level data skipping** on those keys (ordering built from clustering keys, not
partition directories). Skipping speeds reads — but it does **not** give conflict
detection folder-level disjointness for free. A fan-out MERGE pipeline that worked on a
partitioned table starts throwing `ConcurrentAppendException` after the migration,
because each writer's `ON` predicate no longer tells Delta which file set it is scoped
to. The writers read overlapping file sets, and the losers abort.

**The fix — scope the MERGE predicate to the clustering keys.** Narrow each writer's
condition with a literal on the clustering key so Delta can prove the writers touch
disjoint files.

Failing broad predicate — every fan-out writer reads the whole table:

```sql
-- fact_sales is CLUSTER BY (region). N parallel writers, one region each.
-- This ON clause gives Delta no way to prove disjointness -> ConcurrentAppendException.
MERGE INTO fact_sales AS t
USING staged_updates AS s
  ON t.sale_id = s.sale_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

Fixed clustering-key-scoped predicate — the EMEA writer reads only EMEA-clustered
files, the AMER writer only AMER files, so their file sets are disjoint:

```sql
-- The writer that owns the EMEA shard pins the clustering key as a literal AND
-- matches on it, so file-skipping restricts its read set to EMEA files only:
MERGE INTO fact_sales AS t
USING (SELECT * FROM staged_updates WHERE region = 'EMEA') AS s
  ON  t.sale_id = s.sale_id
  AND t.region  = s.region
  AND t.region  = 'EMEA'
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

The load-bearing lines are `t.region = 'EMEA'` (a constant predicate Delta uses to skip
to the EMEA file set) and `t.region = s.region` (so inserts land in the right cluster).
Do this for every clustering key you fan out on. On DBR 14.2+, enabling deletion
vectors / row-level concurrency further reduces the residual collisions, but scoping
the predicate to the clustering keys is the primary fix — it is what makes the writers'
file sets provably disjoint.

## The conflict matrix — which operation pairs collide

Read this as "operation A racing operation B for the next version." "Never" means the
file sets are structurally disjoint and Delta always rebases silently; the isolation
column names when an overlap is treated as a conflict.

| Operation A | Operation B | Conflicts? | Typical exception |
| --- | --- | --- | --- |
| INSERT (blind append) | INSERT (blind append) | Never | — |
| INSERT (blind append) | OPTIMIZE / auto compaction | Never | — |
| INSERT (blind append) | UPDATE / DELETE / MERGE | Serializable only (not WriteSerializable) | `ConcurrentAppendException` |
| UPDATE / DELETE / MERGE | UPDATE / DELETE / MERGE | Both isolation levels | `ConcurrentAppendException`, `ConcurrentDeleteReadException` |
| UPDATE / DELETE / MERGE | OPTIMIZE / auto compaction | Both isolation levels | `ConcurrentDeleteReadException`, `ConcurrentAppendException` |
| OPTIMIZE / auto compaction | OPTIMIZE / auto compaction | Both isolation levels | `ConcurrentDeleteDeleteException` (D01) |
| Any write | Streaming write, same `txnAppId`/`txnVersion` | Always (idempotency guard) | `ConcurrentTransactionException` |
| Any write | Concurrent schema / property change | Always | `MetadataChangedException` / `ProtocolChangedException` |

Reading the exception names as symptoms:

- `ConcurrentAppendException` — someone appended files into the region you read (D02;
  fan-out MERGE without scoped predicates).
- `ConcurrentDeleteReadException` — you read files a concurrent op deleted (compaction
  removed files mid-flight under your MERGE).
- `ConcurrentDeleteDeleteException` — you and another op deleted the same file (D01;
  two compactors).
- `ConcurrentTransactionException` — two streams share a checkpoint / idempotent
  transaction id; give each stream its own checkpoint location.
- `MetadataChangedException` / `ProtocolChangedException` — a schema, table-property,
  or protocol change raced your write; re-read and retry.

## General mitigations — narrow, isolate, serialize

Three levers resolve nearly every case above, in priority order:

- **Narrow the predicate.** Every `MERGE`/`UPDATE`/`DELETE` condition should carry a
  constant on the partition or clustering key that scopes the writer to a disjoint file
  set (D02). This is the highest-leverage fix and the one the conflict message is
  begging for when it says "make the separation explicit."
- **Isolate by partition / clustering key.** Shard fan-out writers so each owns a
  distinct key value, and make that value a literal in the condition. Disjoint keys →
  disjoint files → no conflict, at either isolation level.
- **Serialize maintenance.** Run `OPTIMIZE`/`VACUUM` from one scheduled job in a
  low-traffic window, and do not stack manual `OPTIMIZE` on top of auto compaction
  (D01). Where genuinely concurrent writers are unavoidable, wrap the operation in
  bounded retry-with-exponential-backoff — a `Concurrent*Exception` is a retryable
  signal, not a bug, and a clean re-read usually rebases cleanly on the second attempt.

Two supporting levers: enable **deletion vectors / row-level concurrency** (DBR 14.2+)
to demote file-level conflicts to row-level, and drop to **WriteSerializable** (the
default) rather than **Serializable** unless a downstream consumer truly needs the
stricter guarantee — Serializable manufactures conflicts WriteSerializable would let
pass. Do **not** lower isolation below WriteSerializable; there is no safe level below
it for concurrent writers.

## Sources

- Databricks — _Isolation levels and write conflicts on Databricks_ (OCC model, the
  WriteSerializable-vs-Serializable conflict matrix, and the `ConcurrentAppendException`
  / `ConcurrentDeleteReadException` / `ConcurrentDeleteDeleteException` /
  `ConcurrentTransactionException` / `MetadataChangedException` / `ProtocolChangedException`
  catalog with per-exception avoidance guidance), docs.databricks.com
  `/optimizations/isolation-level`.
- Databricks — _Compact data files with optimize on Delta Lake_ and _Auto compaction
  for Delta Lake on Databricks_ (`OPTIMIZE` bin-packing, the `delta.autoOptimize.autoCompact`
  table property, the `spark.databricks.delta.autoCompact.enabled` session config, and
  the ~128 MB auto-compaction target vs the ~1 GB `OPTIMIZE` target),
  docs.databricks.com `/delta/optimize` and `/delta/tune-file-size`.
- Databricks — _Use liquid clustering for Delta tables_ (LC replaces partitioning /
  ZORDER with clustering-key file-skipping, and the guidance to add clustering columns
  to the operation condition to avoid write conflicts), docs.databricks.com
  `/delta/clustering`.
- Databricks — _Isolation levels and write conflicts_ § row-level concurrency
  (GA on DBR 14.2+, automatic on deletion-vector tables; demotes file-level conflicts
  to row-level and which exceptions it does and does not resolve), docs.databricks.com
  `/optimizations/isolation-level`.
- Delta Lake — _Concurrency control_ (protocol-level OCC: the `_delta_log` ordered
  commit files, `AddFile`/`RemoveFile` actions, atomic next-version commit as the
  serialization point, and optimistic conflict detection / rebase), docs.delta.io
  `/latest/concurrency-control`.
