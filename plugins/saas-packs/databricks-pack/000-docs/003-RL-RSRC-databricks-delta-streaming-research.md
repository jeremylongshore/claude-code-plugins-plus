# Databricks Pain Catalog — Domain 2: Delta Lake, Liquid Clustering, Structured Streaming, DLT

**Compiled:** 2026-05-27
**Scope:** Recurring, painful, real-world issues that bite engineers in production on Databricks DBR 13.x–16.x with Delta Lake 2.x–4.x.
**Purpose:** Grounding research for a Claude Code skill plugin pack rebuild — each entry classifies the pain type (platform bug / config mistake / design decision) and proposes the response architecture (which Claude Code primitives fit).

---

## D01 — `ConcurrentDeleteDeleteException` when manual OPTIMIZE collides with AUTO OPTIMIZE

**Domain:** delta-lake
**Trigger:** Engineer runs `OPTIMIZE <table>` manually (often from a notebook or scheduled job) while AUTO OPTIMIZE / auto-compaction is also enabled on the same table — common after MERGE/UPDATE/DELETE jobs which always have auto-compact on.
**Symptom:** Job fails with verbatim:

```
[DELTA_CONCURRENT_DELETE_DELETE] ConcurrentDeleteDeleteException:
This transaction attempted to delete one or more files that were deleted by a concurrent update.
```

`DESCRIBE HISTORY` shows two back-to-back OPTIMIZE rows where one is `"auto": true` and the other `"auto": false` around the failure timestamp.
**Root cause:** Both the auto-compactor and the manual OPTIMIZE are issuing optimistic-concurrency-controlled commits that mark the same source small files for deletion. Whichever commits second loses. This is a **design decision** in Delta's OCC model, not a bug — but it surprises engineers who don't realize MERGE/UPDATE/DELETE silently enable autoCompact.
**Blast radius:** single-table — but the failing job often holds up downstream Airflow/Workflow DAGs.
**Current workaround (manual):** Either (a) disable AUTO OPTIMIZE globally via `spark.databricks.delta.optimizeWrite.enabled false` + `spark.databricks.delta.autoCompact.enabled false` (Databricks officially discourages this — costs perf), or (b) gate manual OPTIMIZE behind a lock the team enforces by convention, or (c) wrap OPTIMIZE in retry-with-backoff.
**Citations:**

- https://kb.databricks.com/delta/running-optimize-on-delta-tables-causing-concurrentdeletedeleteexception-error
-
- https://docs.databricks.com/aws/en/optimizations/isolation/row-level-concurrency
**Response architecture recommendation:** **SKILL.md + scripts/ + Hooks (PreToolUse).** A `pre-optimize-check` script inspects table properties (`SHOW TBLPROPERTIES`) and recent `DESCRIBE HISTORY` to detect auto-compact activity in the last N minutes before allowing a manual OPTIMIZE; the hook blocks the user from firing `OPTIMIZE` without that check. SKILL.md teaches the recovery decision tree. No MCP needed — pure-SQL diagnostic via existing JDBC.

---

## D02 — `ConcurrentAppendException` on Liquid-Clustered tables despite "different rows"

**Domain:** liquid-clustering
**Trigger:** Engineer migrates a partitioned table to Liquid Clustering expecting better concurrency, then runs the same multi-writer MERGE jobs they ran before (e.g., per-tenant CDC merges fan-out across 50 workflow runs).
**Symptom:** Verbatim:

```
[DELTA_CONCURRENT_APPEND] ConcurrentAppendException: Files were added to the root of the table by a concurrent update.
```

Engineer's gut reaction: "but my MERGEs touch different user_ids — Liquid Clustering should handle this." DBR 15.3 reproducer in citation.
**Root cause:** Liquid Clustering replaces *folder-based partition pruning* with file-skipping via ZCubes. The conflict detection still works on the file set the MERGE *scanned*, not on the final touched rows. If the merge predicate is just `s.user_id = t.user_id`, Delta reads candidate files across the whole logical clustering — overlapping reads → overlapping write sets → conflict. **Design decision (Liquid Clustering does NOT magically eliminate writer conflicts)**, but it is widely misunderstood as such in marketing material.
**Blast radius:** prod-pipelines — typically blows up fan-out jobs in workflow orchestrators.
**Current workaround (manual):** Add narrowing predicates to MERGE on the clustering key(s) so each merge scans a non-overlapping file set: `... AND t.country = '<lit>' AND t.date = '<lit>'`. Or enable row tracking: `ALTER TABLE t SET TBLPROPERTIES ('delta.enableRowTracking' = true)` (DBR 14+). Or serialize the writers.
**Citations:**

- https://community.databricks.com/t5/data-engineering/concurrentappendexception-liquid-clustered-table-different-row/td-p/76916
- https://kb.databricks.com/delta/insert-operation-fails-while-trying-to-execute-multiple-concurrent-insert-or-merge-operations-to-append-data
-

**Response architecture recommendation:** **SKILL.md + references/ + Subagent.** A subagent inspects the user's MERGE SQL, identifies the clustering keys of the target table (via MCP-fetched `DESCRIBE DETAIL` or stored ref), and rewrites the predicate to include the clustering-key filters. The references/ dir holds the full "MERGE rewrite cookbook" — examples for SCD2, dedup, CDC. A pure scripts/ approach is too brittle here because the SQL surface is too varied — needs an agent rewriting the predicate, not a regex.

---

## D03 — Streaming source fails `DELTA_FILE_NOT_FOUND_DETAILED` after VACUUM cleans files the checkpoint still references

**Domain:** streaming
**Trigger:** Long-running streaming job consumes a Delta source that has OPTIMIZE running periodically + a daily VACUUM with the default 7-day retention. The streaming job falls behind (cluster restart, late start, traffic spike) by more than retention, OR the checkpoint's tracked offset references a file that OPTIMIZE rewrote and VACUUM later cleaned.
**Symptom:** Verbatim:

```
[DELTA_FILE_NOT_FOUND_DETAILED] File abfss://<storage>.dfs.core.windows.net/
<path>/part-xxxx-c000.snappy.parquet referenced in the transaction log
cannot be found.
```

Or the older form: `FileNotFoundException: ... doesn't exist` even with `ignoreMissingFiles=true` set.
**Root cause:** **Platform-bug-adjacent design decision.** The streaming Delta source pins offsets to *file paths*, not logical version positions. OPTIMIZE creates a new logical version where files are rewritten; VACUUM (7 days later by default) deletes the originals. If the streaming job's last successful commit is older than the OPTIMIZE+VACUUM cycle, the next batch tries to read a file that no longer exists. `ignoreMissingFiles` was supposed to mitigate but is documented as not always working for this case.
**Blast radius:** prod-pipelines — entire streaming consumer dead until manual recovery.
**Current workaround (manual):** Pick one of: (a) restart with a fresh checkpoint location + manual reconciliation/dedup downstream, (b) restart with `startingVersion` set to the oldest available version per `DESCRIBE HISTORY`, (c) `FSCK REPAIR TABLE <name>` to prune stale metadata, (d) run `OPTIMIZE` on source less often or move VACUUM retention to >> streaming SLA.
**Citations:**

- https://kb.databricks.com/delta/delta-table-as-a-streaming-source-returns-error-delta_file_not_found_detailed-even-though-no-user-or-lifecycle-rule-has-deleted-files
- https://kb.databricks.com/delta/error-filenotfoundexception-while-streaming-job-or-reading-delta-table-even-with-ignoremissingfiles-set-
- https://community.databricks.com/t5/data-engineering/deltafilenotfoundexception-no-file-found-in-the-directory-sudden/td-p/53066
**Response architecture recommendation:** **MCP server + Slash command + Hooks (SessionStart).** This is a multi-system diagnostic — needs typed Databricks Workspace API access (job state, checkpoint location, source-table version history) to triangulate. A `/recover-streaming-source` slash command runs a decision tree: get latest source version → get latest committed checkpoint offset → compute drift → recommend one of the 4 recovery strategies. SessionStart hook warns "you have N streaming jobs with checkpoints older than the source's `deletedFileRetentionDuration`."

---

## D04 — Streaming checkpoint silently resets to batch 0 after months of healthy operation

**Domain:** streaming
**Trigger:** Production Spark Streaming job that has been running for many months suddenly fails or restarts from batch 0. No code change recent to the failure. Often after a cluster restart or rare DBR upgrade.
**Symptom:** Verbatim (community report):

```
StreamingQueryException: [STREAM_FAILED] Query [id = ..., runId = ...] terminated with exception:
dbfs:/mnt/path/my_table/sources/0/0 doesn't exist
```

`sources/`, `offsets/`, and `commits/` directories under the checkpoint path stop receiving writes; batch ID resets from 711 → 0 on next restart.
**Root cause:** **Platform bug class** — checkpoint metadata corruption (or in some cases, deletion by a lifecycle policy on DBFS/S3 the user didn't know existed). Databricks has a documented "Recover a pipeline from streaming checkpoint failure" page but no clean root-cause story for spontaneous corruption.
**Blast radius:** single-pipeline → workspace-wide if the checkpoint location is shared.
**Current workaround (manual):** Documented three-tier recovery: (1) full table refresh + recompute, (2) checkpoint reset + downstream dedup, (3) restart from a known-good `startingVersion`. None is cheap.
**Citations:**

- https://community.databricks.com/t5/administration-architecture/spark-streaming-checkpoint-corrupted/td-p/3681
- https://docs.databricks.com/aws/en/structured-streaming/checkpoints
- https://docs.databricks.com/aws/en/ldp/recover-streaming
**Response architecture recommendation:** **MCP server + Hooks (SessionStart + PostToolUse) + scripts/.** Hook-based monitoring is the right shape: a `SessionStart` hook lists streaming queries with `numInputRows=0` for N minutes and surfaces "your stream is stuck — likely checkpoint corruption." A `scripts/diagnose-checkpoint` tool inspects `sources/`, `offsets/`, `commits/` for monotonic IDs and flags discontinuities. Recovery is a guided playbook in SKILL.md because the three recovery paths have different downstream cleanup implications — the agent has to ask the user which they prefer.

---

## D05 — RocksDB state store pins multi-GB off-heap memory; driver OOM despite normal heap

**Domain:** streaming
**Trigger:** Stateful streaming workload (`dropDuplicatesWithinWatermark`, stream-stream join, `mapGroupsWithState`, or `applyInPandasWithState`). Cluster resized, shuffle partition count changed without clearing checkpoint, OR data volume grew while state schema is wide.
**Symptom:** Driver pod OOMKilled. `executor.rocksDBOperationsTimeMillis` and metrics show `rocksdbPinnedBlocksMemoryUsage` in the 10s of GB. One documented case: 22 GB pinned. Another: 32 GB used to store 611,788 records.
**Root cause:** **Design decision** — default RocksDB has no memory cap; pinned blocks aren't subject to JVM GC; `memoryUsedBytes` reflects full row width (all columns), not just the watermark/key columns. Compounded if shuffle partitions changed without checkpoint reset — RocksDB keeps multiple state-store instances per partition simultaneously.
**Blast radius:** prod-pipelines — entire job dies, often takes the cluster with it.
**Current workaround (manual):** Set `spark.databricks.streaming.statefulOperator.stateRebalancing.enabled true`, cap RocksDB with `spark.sql.streaming.stateStore.rocksdb.boundedMemoryUsage true` + `spark.sql.streaming.stateStore.rocksdb.maxMemoryUsageMB 4096`, enable `changelogCheckpointing.enabled true` (DBR 13.3+), trim state schema to only what's needed for the operator, and clear checkpoint after any partition-count change.
**Citations:**

- https://community.databricks.com/t5/administration-architecture/extreme-rocksdb-memory-usage/td-p/42972
- https://medium.com/@rahulgosavi.94/why-your-databricks-streaming-job-is-leaking-driver-memory-and-how-to-fix-it-41554b75c73a
- https://docs.databricks.com/aws/en/structured-streaming/rocksdb-state-store
**Response architecture recommendation:** **SKILL.md + references/ + scripts/.** Encyclopedic — the configuration surface is large enough that a deep references/ section is needed (one page per RocksDB knob with what it actually does). `scripts/scan-stream-config` reads job/cluster Spark configs and grades them against the recommended bounded-memory profile. No MCP strictly needed because Databricks Jobs API + REST give enough info; could upgrade to MCP if used heavily.

---

## D06 — Liquid Clustering migration from partition + Z-ORDER: hidden full rewrite cost + downstream breakage

**Domain:** liquid-clustering
**Trigger:** Engineer follows a Databricks blog or DAIS talk recommending Liquid Clustering, runs `ALTER TABLE t CLUSTER BY (col1, col2)` on a multi-TB partitioned table that also has historical Z-ORDER. Then runs `OPTIMIZE FULL` because the docs imply it's needed for a clean transition.
**Symptom:** (1) `OPTIMIZE FULL` either OOMs the cluster or runs for 12–48 hours on a multi-TB table; (2) downstream Spark jobs that hard-coded partition predicates (`WHERE _hive_partition = ...`) break because the table no longer has partition folders; (3) "table size ballooning after optimization jobs" reported by multiple community users — Delta keeps both the old and new file sets until VACUUM; (4) `CLUSTER BY` is mutually exclusive with partitioning and with Z-ORDER, so any code path doing `OPTIMIZE ZORDER BY (...)` now errors.
**Root cause:** **Design decision wrapped in documentation gap.** Liquid Clustering trades partition-pruning predictability for incremental ZCubes; the migration path is real-but-expensive and the "before/after" performance comparison rarely accounts for the rewrite cost, the dual-storage period, or downstream code coupling to partitioning.
**Blast radius:** workspace-wide downstream — every consumer of the table needs review.
**Current workaround (manual):** Before flipping `CLUSTER BY`, audit downstream queries for explicit partition predicates; rewrite to use clustering keys instead. Stage the migration on a cloned table first (`CREATE TABLE staging CLONE source`), verify size + perf, swap. Budget the cluster + storage cost in advance. Run timely VACUUM after the OPTIMIZE FULL.
**Citations:**

- https://community.databricks.com/t5/data-engineering/when-to-use-and-when-not-to-use-liquid-clustering/td-p/136190
- https://docs.databricks.com/aws/en/delta/clustering
- https://dataengineerwiki.substack.com/p/how-liquid-clustering-actually-beats
- https://www.canadiandataguy.com/p/optimizing-delta-lake-tables-liquid
**Response architecture recommendation:** **Slash command + Subagent + MCP server.** This is a multi-stage migration; agent-driven. `/migrate-to-liquid-clustering <table>` orchestrates: (1) MCP-fetched `DESCRIBE HISTORY` + size estimate, (2) Subagent grep across the workspace for downstream readers referencing partition predicates, (3) generate migration plan with cost estimate + rollback path, (4) execute as a clone-first/swap-at-end pattern. MCP is justified because the migration touches multiple workspace-API surfaces (jobs, tables, lineage). Hooks not needed.

---

## D07 — Delta time travel breaks silently when VACUUM crosses retention boundary

**Domain:** delta-lake
**Trigger:** Engineer relies on Delta time travel for "rollback in case anything goes wrong" (auditor demand, GDPR right-to-be-forgotten misunderstanding, dev-prod debugging). VACUUM runs nightly at default 7-day retention OR has been tuned down to 1–2 days for cost.
**Symptom:** `SELECT * FROM t VERSION AS OF 47` works fine for recent versions and fails for older ones with the standard `DELTA_FILE_NOT_FOUND_DETAILED` error. Or `DESCRIBE HISTORY` truncates and the engineer is confused why "version 0 doesn't exist anymore."
**Root cause:** **Design decision + recurring misconception.** Time travel is per-transaction versioning on top of Parquet — VACUUM removes files associated with versions older than retention. Common misconceptions documented: time travel = backups (no), time travel = SCD2 (no), time travel = GDPR erasure (no — opposite, it *retains* deleted data), time travel = CDC alternative (CDF is the right tool). Each misconception leads to a different failure mode.
**Blast radius:** dev-workspace + audit/compliance — usually only bites during a high-pressure investigation.
**Current workaround (manual):** Lengthen retention via `ALTER TABLE t SET TBLPROPERTIES ('delta.deletedFileRetentionDuration' = 'interval 30 days', 'delta.logRetentionDuration' = 'interval 30 days')`, plus disable VACUUM safety check if going below 7 days (`SET spark.databricks.delta.retentionDurationCheck.enabled = false`) — but this trades storage cost for safety. For real archival, take an external snapshot or CLONE.
**Citations:**

- https://medium.com/towards-data-engineering/top-misconceptions-about-delta-lake-time-travel-a9fff62bdf5a
- https://docs.databricks.com/aws/en/delta/vacuum
- https://kb.databricks.com/en_US/delta/vacuum-best-practices-on-delta-lake
- https://medium.com/@vinodkumar.mani/databricks-delta-lake-time-travel-understanding-retention-before-you-lose-your-data-f4ea26ccb934
**Response architecture recommendation:** **SKILL.md + references/ + Hooks (PreToolUse on VACUUM).** SKILL.md teaches the 4-misconception framework so the agent can name the user's *actual* need (backup vs SCD2 vs CDF vs rollback). A PreToolUse hook on `VACUUM` queries the table's retention settings + the workspace's longest-running streaming consumer's lag and warns if VACUUM will sever time travel for an active reader. references/ holds the decision tree per use case.

---

## D08 — DLT pipeline intermittently fails "table missing" due to concurrent Python threads inside `@dlt.table` functions

**Domain:** DLT
**Trigger:** Engineer parallelizes ingestion of N source tables (a common pattern: 58 bronze tables in one pipeline) using Python `ThreadPoolExecutor` or similar inside the DLT notebook to "speed up" pipeline graph construction.
**Symptom:** Pipeline fails ~25–30% of runs with "table missing" / table-not-found during DAG materialization. Re-running with no code change succeeds. Both UI runs and full-refresh runs affected. From the community thread: *"the pipeline fails once every 3/4 runs saying that a table is missing - but when i rerun without any code change - it completes successfully."*
**Root cause:** **Platform-bug-adjacent design constraint.** DLT's `@dlt.table` / `@dlt.view` decorators register tables into a pipeline graph during the planning phase. Threading those registrations creates a race in the registration order, so the planner sometimes sees a dependent table before its dependency exists. Databricks support privately identified threading as the cause; not documented publicly.
**Blast radius:** single-pipeline, but the intermittency burns engineering time hunting non-bugs.
**Current workaround (manual):** Remove the threading; let DLT's own DAG executor parallelize. Use a for-loop with parameterized table definitions instead of threads.
**Citations:**

- https://community.databricks.com/t5/data-engineering/delta-live-table-pipeline-failure-table-missing/td-p/40475
- https://docs.databricks.com/aws/en/dlt/recover-streaming
- https://b-eye.com/blog/databricks-delta-live-tables-guide/
**Response architecture recommendation:** **Hooks (PreToolUse) + SKILL.md.** This pain is detectable statically — a PreToolUse hook on DLT notebook deploys greps for `ThreadPoolExecutor`, `concurrent.futures`, `threading.Thread` inside files that import `dlt` and blocks with a clear error citing this exact pattern. SKILL.md provides the rewrite pattern (for-loop with closure binding). No MCP / subagent needed — pattern is small and fixed.

---

## D09 — DLT full refresh on streaming tables silently drops data when source is non-replayable

**Domain:** DLT
**Trigger:** Engineer hits "Full Refresh" in DLT UI (or runs a `--full-refresh-all` workflow trigger) on a pipeline whose source is a Kafka topic with 7-day retention, an Event Hub with N-day retention, a truncate-and-load Delta source, or a cloud-object-storage path where files have already aged off.
**Symptom:** Pipeline completes "successfully" but the target table is missing weeks/months of history. No error. No alert. Discovered later by a downstream consumer or BI report showing zero rows for older partitions.
**Root cause:** **Design decision** — full refresh = truncate target + replay source from the beginning of *currently available* source data. If the source can't replay to the original start, you lose what's no longer there. Databricks docs do warn but the UI button gives no friction.
**Blast radius:** prod-pipelines + downstream — silent data loss is the worst kind.
**Current workaround (manual):** Pre-mark protected tables with `pipelines.reset.allowed=false` in the table property (DLT-specific) — this blocks accidental full refresh entirely. Otherwise: snapshot the target BEFORE full refresh, full-refresh, diff, backfill from snapshot. Or never enable full refresh on append-only event-source streams; use Change Data Feed-driven reprocessing instead.
**Citations:**

- https://community.databricks.com/t5/data-engineering/dlt-full-refresh/td-p/63245
- https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/full-refresh
- https://docs.databricks.com/aws/en/ldp/updates
- https://dmesh-io.medium.com/full-refresh-on-databricks-delta-live-streaming-tables-with-kafka-topics-f79a222c4c29
**Response architecture recommendation:** **Hooks (PreToolUse on pipeline-update API call) + Slash command + MCP server.** The most valuable response is friction at the moment of triggering full refresh. PreToolUse hook on any `gh-databricks pipelines update --full-refresh*` style invocation: agent inspects pipeline manifest for source types (Kafka/Kinesis/EventHub/Autoloader), checks for `pipelines.reset.allowed=false`, and refuses + offers `/protect-dlt-pipeline` slash command to add the property. MCP needed because the check requires authenticated Pipelines API access to read the manifest.

---

## D10 — Autoloader `UnknownFieldException` stops the stream on every new column; rescue mode silently widens schema

**Domain:** streaming (Autoloader)
**Trigger:** Bronze ingestion with Autoloader reading JSON/CSV/Parquet from S3/ADLS/GCS. Upstream system adds a new column. Engineer set up the stream with `cloudFiles.schemaEvolutionMode='addNewColumns'` (the default before a recent change) OR didn't think about schema-evolution mode at all.
**Symptom:** Two distinct failure modes depending on mode:

- **addNewColumns (default in many setups):** stream stops with `UnknownFieldException`. Engineer must restart manually after the schema-location auto-updates. Downstream is now stale until restart.
- **rescue mode:** stream keeps running but all unexpected fields land in `_rescued_data` (a JSON-blob string column) — silent schema drift, downstream queries break because the "new" column never materializes as a typed column.
- **failOnNewColumns:** explicit fail every time.
**Root cause:** **Design decision** — Autoloader trades automation for explicitness. None of the modes does what most engineers actually want: "evolve the schema, type the new column inferred from the data, restart the stream automatically, and notify me." The schemaHints feature partially fills the gap but requires the engineer to know the new column name in advance.
**Blast radius:** prod-pipelines — bronze layer broken → silver/gold cascade.
**Current workaround (manual):** Combination of `schemaHints` for known-evolving fields + `rescuedDataColumn` for safety net + downstream monitor that alerts if `_rescued_data IS NOT NULL` for >X% of rows + an autoloader restart job triggered by the UnknownFieldException event. Multi-piece.
**Citations:**
- https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema
- https://community.databricks.com/t5/technical-blog/schema-management-and-drift-scenarios-via-databricks-auto-loader/ba-p/63393
- https://learn.microsoft.com/en-us/azure/databricks/ingestion/cloud-object-storage/auto-loader/schema
- https://medium.com/@asindugayangana/databricks-auto-loader-best-practices-for-reliable-and-scalable-data-ingestion-30e65bf4c520
**Response architecture recommendation:** **MCP server + Hooks (PostToolUse on stream-stop) + scripts/ + Subagent.** The right response is a small system, not a single skill artifact:
- MCP exposes Databricks Jobs API + the schema-location storage path.
- PostToolUse hook detects an `UnknownFieldException` in a job's failure event and auto-invokes a Subagent.
- Subagent reads the latest schema in the schema location, diffs against last commit, proposes a `schemaHints` patch + PR.
- `scripts/rescued-data-monitor` cron-style script that surfaces the `_rescued_data IS NOT NULL` rate per table.

---

## D11 — DLT serverless cost spike: maintenance cluster runs predictive optimization 24×7 on idle pipelines

**Domain:** DLT
**Trigger:** Engineer migrates a triggered pipeline to DLT serverless for "auto-scaling cost savings." Pipeline itself runs 1×/day for 20 minutes, but the bill triples.
**Symptom:** Databricks billing shows continuous serverless SKU usage even when the pipeline isn't actively updating. Investigation reveals the maintenance cluster (separate from the update cluster) is running predictive optimization (VACUUM, OPTIMIZE, automatic Liquid Clustering key selection) on every table the pipeline owns, every day.
**Root cause:** **Design decision** — each declarative pipeline has TWO compute resources (update + maintenance) and predictive optimization is on by default for managed Unity Catalog tables. The maintenance cluster cost isn't visible in the same place as the update cost. Plus, DLT Advanced tier defaults bring in features (CDC, expectations enforcement, SCD2) the engineer may not be using.
**Blast radius:** workspace-wide cost — multiplied across N pipelines.
**Current workaround (manual):** (1) Audit each pipeline's tier — drop to DLT Core or Pro if Advanced features aren't used; (2) review `enzyme.mode` and predictive-optimization settings per table; (3) for triggered pipelines, ensure performance mode is set to standard not "Performance optimized" if latency doesn't justify the premium; (4) use system tables (`system.billing.usage`) to attribute costs per pipeline.
**Citations:**

- https://www.cloudzero.com/blog/reduce-databricks-costs/
- https://docs.databricks.com/aws/en/admin/system-tables/serverless-billing
- https://docs.databricks.com/aws/en/ldp/serverless
- https://medium.com/@kezhu2007/how-i-traced-a-3-5x-databricks-cost-spike-to-three-dashboards-part-1-11724476d1ff
- https://www.unraveldata.com/resources/maximizing-databricks-predictive-optimization-roi/
**Response architecture recommendation:** **MCP server + Slash command + scripts/.** Cost analysis = data join across `system.billing.usage`, pipeline manifest, and table properties. `/dlt-cost-audit` slash command: MCP-pulls the billing rows for the last 30 days grouped by pipeline_id + workload_type (update vs maintenance), correlates with pipeline tier + serverless mode + table predictive-optimization flags, and outputs "your top-3 cost levers." scripts/ holds reusable SQL queries against system tables. No subagent — this is deterministic data analysis.

---

## D12 — `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`: streaming job dies after upstream "CREATE OR REPLACE TABLE" silently changes table ID

**Domain:** streaming
**Trigger:** A streaming job reads from a Delta source table. A separate team (or the same engineer on a different day) runs `CREATE OR REPLACE TABLE <name> ...` or `DROP TABLE` + `CREATE TABLE` against that source — typical for "rebuild bronze from scratch" or schema migration scripts.
**Symptom:** Verbatim:

```
[STREAM_FAILED] Query [id = <query-id>, runId = <run-id>] terminated with exception:
[DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE] The streaming query was reading from
an unexpected Delta table (id = '<id>'). It used to read from another Delta table
(id = '<other-id>') according to checkpoint.
```

**Root cause:** **Design decision** — checkpoints pin to the source table's UUID (set at `_delta_log` creation), not to the table's qualified name. `CREATE OR REPLACE` creates a new UUID even if name is unchanged. This is intentional safety (preventing accidental consumption of unrelated data under the same name) but bites every time a team uses CREATE OR REPLACE on a streamed-from table.
**Blast radius:** prod-pipelines + cross-team — usually the consumer team has to scramble while the producer team thinks they did nothing wrong.
**Current workaround (manual):** (1) Don't CREATE OR REPLACE streamed-from tables; instead use truncate + insert, or DROP COLUMN + ADD COLUMN, or migrate via clone-and-swap. (2) If forced, restart the consumer with a fresh checkpoint and downstream dedup. No automatic recovery.
**Citations:**

- https://kb.databricks.com/streaming/streaming-job-failing-with-different_delta_table_read_by_streaming_source-error
- https://kb.databricks.com/streaming/structured-streaming-job-fails-with-a-streaming-query-exception-when-a-schema-changes-in-the-source-table
- https://kb.databricks.com/streaming/resumed-streaming-job-fails-after-pause-with-streamingqueryexception-error
**Response architecture recommendation:** **Hooks (PreToolUse on CREATE OR REPLACE / DROP TABLE) + MCP server.** Right-shaped response is producer-side prevention, not consumer-side recovery. PreToolUse hook on `CREATE OR REPLACE TABLE` or `DROP TABLE` queries the workspace via MCP for streaming queries currently consuming from that table (`SELECT * FROM system.streaming.query_progress WHERE source_table = ...`) and blocks the operation if any active consumers exist, surfacing them by name + owner. SKILL.md provides the safer migration patterns. Hook also fires on the consumer side as an early warning if the table UUID changed between sessions.

---

## Source gaps / unfilled areas

What this catalog does NOT yet cover well — flag these for follow-up research:

1. **Reddit r/databricks + r/dataengineering primary-source threads** — WebFetch on reddit.com blocked from this environment. Several pains here are likely under-represented as a result (e.g., "everyone's worst DLT story" anecdotes that show up in those subs). Recommend follow-up via Brave Search or a Reddit-API MCP.
2. **DAIS 2024/2025 talks** — talk pages indexed but not video-mined; deep streaming postmortems (e.g., Stripe's, Shopify's at DAIS) are richer than blog form but require transcript work.
3. **delta-rs (Rust client) issues** — included in original scope; not separately mined. delta-rs has its own pain surface around protocol-version skew with Databricks-managed tables that deserves its own entry.
4. **Delta UniForm / Iceberg compat pain** — emerging area in 2025; saw signals but didn't have a clear recurring-issue thread to anchor a pain entry. Worth its own pass.
5. **Materialized View incremental-refresh fallbacks** — DLT MVs sometimes silently fall back to full recompute; community thread exists but pain is still being characterized. Worth re-mining in 6 months.
6. **Photon-vs-classic engine subtle behavior differences in Delta writes** — multiple anecdotal mentions, no canonical thread yet.
7. **`MERGE WITH SCHEMA EVOLUTION` interaction with downstream readers expecting old schema** — covered in D-implicit but deserves a dedicated entry once a concrete repro thread surfaces.

---

## Pain-type tally (for response-architecture planning)

| Type | Entries | Notes |
|---|---|---|
| Design decision (platform-by-design, surprises engineers) | D01, D02, D05, D06, D07, D09, D10, D11, D12 | 9/12 — the dominant class; response is education + friction-at-trigger-time, not bug-fixes |
| Platform-bug-adjacent (works as designed but design is flawed) | D03, D08 | 2/12 — needs workaround playbooks, can't fix the platform |
| Platform bug class (no documented root cause) | D04 | 1/12 — needs monitoring + guided recovery |

**Strategic takeaway for the plugin pack:** the dominant response primitives are **Hooks (PreToolUse for friction-at-trigger)** + **MCP server (Databricks Workspace API access for diagnostics)** + **SKILL.md (decision trees for the design-decision cluster)**. Subagents are needed in only ~3 of the 12 entries (SQL rewriting, multi-file workspace scans). Scripts/ shows up as supporting tooling, not as the primary entry point.
