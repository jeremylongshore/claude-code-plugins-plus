# PRD: databricks-streaming-guardian

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-12
**Status:** Active

> Authored to the `templates/skill-docs/` submission standard at the Pack / flagship tier
> (this is a `databricks-pack` skill) as the design record for `databricks-streaming-guardian`,
> per `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills"). Companion docs beside it: `ADR.md`, `ONE-PAGER.md`.

## Problem

The data-ops layer is where Databricks loses data silently, and the loss is usually
triggered by a routine command run against the wrong table. A separate team runs
`CREATE OR REPLACE TABLE bronze.events` to rebuild a source; the statement mints a new
Delta table UUID and every streaming consumer that pins that UUID in its checkpoint dies
with `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`, and there is no automatic recovery
(D12). A nightly `VACUUM` at the default 7-day retention cleans a file a lagging streaming
checkpoint still references, and the consumer is dead until a human reconciles it (D03) —
the same retention boundary that severs time travel for an auditor mid-investigation (D07).
A manual `OPTIMIZE` collides with the auto-compaction that MERGE silently enabled and the
job aborts with `ConcurrentDeleteDeleteException` (D01); a multi-writer MERGE on a
Liquid-Clustered table throws `ConcurrentAppendException` even though the merges "touch
different rows" (D02). None of these announces itself as destructive — the destructive part
is a one-line command the operator has run a hundred times.

The rest of the catalog is the same shape: a checkpoint that silently resets to batch 0
after months of healthy operation (D04); a stateful stream whose RocksDB off-heap state
pins tens of GB and OOM-kills the driver while the heap looks fine (D05); a Liquid
Clustering migration whose `OPTIMIZE FULL` full-rewrite cost and downstream partition-predicate
breakage nobody budgeted for (D06); a DLT pipeline that fails "table missing" ~30% of runs
because someone threaded the `@dlt.table` registrations (D08); a DLT full refresh that
truncates the target and silently drops weeks of history when the source can't replay (D09);
and an Auto Loader stream that stops on every new column with `UnknownFieldException`, or
worse, silently buries the drift in `_rescued_data` (D10). The v1 skills
(`databricks-common-errors`, `databricks-incident-runbook`) narrate these after the fact.
Nothing sits *at the moment of the destructive command* and refuses it when a live consumer
would be killed, then walks the operator through recovery by the actual error code.

## Target users

| User | Context | Primary need |
| ---- | ------- | ------------ |
| Streaming / data-platform engineer on-call | A production stream just died — file-not-found, checkpoint reset, table-UUID change — and downstream is stale | A recovery decision tree keyed to the *actual* error code, not "restart and hope" |
| Data engineer about to run a destructive command | Rebuilding a bronze source (`CREATE OR REPLACE`), dropping a table, or tuning `VACUUM` retention | A guardrail that refuses the op *before* it kills a live consumer, naming who reads the table |
| Pipeline owner debugging Delta write conflicts | A MERGE / OPTIMIZE job aborts with a concurrency exception they thought Liquid Clustering solved | A predicate rewrite that scopes the MERGE to the table's clustering keys, plus the OCC model explained |
| DLT / Auto Loader author | A pipeline fails intermittently, silently drops data on full refresh, or stops on a new column | The static foot-gun caught at authoring time (threading, non-replayable full refresh, schema-evolution mode) |

## The foot-gun surface (003-RL-RSRC)

The pack's 12-pain Delta / streaming / DLT catalog. This skill owns the eleven data-ops
foot-guns below; the twelfth, D11 (DLT serverless maintenance-cluster cost spike), is a
spend problem owned by the sibling `databricks-cost-leak-hunter`.

| Pain | Failure | Guardian response |
| ---- | ------- | ----------------- |
| D01 | `ConcurrentDeleteDeleteException` — manual OPTIMIZE collides with auto-compact | `scripts/pre-optimize-check.sh` collision probe (advisory) + concurrency reference |
| D02 | `ConcurrentAppendException` — multi-writer MERGE on a Liquid-Clustered table | `merge-rewriter` subagent scopes the predicate to the clustering keys |
| D03 | `DELTA_FILE_NOT_FOUND` — VACUUM cleaned a file the streaming checkpoint still pins | `scripts/recover-streaming-source.py` 4-way recovery tree + **VACUUM block hook** |
| D04 | Checkpoint silently resets to batch 0 after months | Stuck-stream detection + the 3-tier recovery playbook (reference) |
| D05 | RocksDB off-heap OOM — GBs pinned, driver OOM-killed on normal heap | Bounded-memory config grade from `clusters_get` + RocksDB reference |
| D06 | Liquid Clustering migration — hidden `OPTIMIZE FULL` rewrite cost + downstream breakage | Clone-first / swap-at-end migration playbook (reference) |
| D07 | Time travel breaks at the VACUUM retention boundary | **VACUUM block hook** (retention-vs-consumer-lag) + retention reference |
| D08 | DLT "table missing" ~30% of runs from threaded `@dlt.table` registration | Static grep for threading in `dlt`-importing files + rewrite pattern |
| D09 | DLT full refresh silently drops data on a non-replayable source | Full-refresh advisory + `pipelines.reset.allowed` check via `pipelines_get` |
| D10 | Auto Loader `UnknownFieldException` stops the stream / rescues drift silently | Schema-evolution guardrail + a `schemaHints` patch (reference) |
| D12 | `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE` — CREATE OR REPLACE mints a new UUID | **DROP / CREATE OR REPLACE block hook** (consults `query_progress`) |

## The hook contract

This is the **only skill in the pack whose hooks block**. A `PreToolUse` hook fires when a
`Bash(databricks:*)` / SQL-executing call carries one of three statement shapes against a
resolvable target table — `VACUUM`, `DROP TABLE`, or `CREATE OR REPLACE TABLE` — because
each is genuinely irreversible for a downstream streaming consumer. Every other pack skill,
and every advisory in this one (D01 OPTIMIZE, D09 full refresh), only warns; blocking is
reserved for the ops with no undo.

- **Evidence.** Before allowing the op, the hook reads `system.streaming.query_progress`
  (via the managed SQL MCP, CLI Statement Execution API as fallback) for the consumers
  actively reading the *exact* target table.
- **Block condition.** For `DROP TABLE` / `CREATE OR REPLACE TABLE`, any active consumer is
  a block — the op deletes the table or re-mints its UUID and kills every reader (D12). For
  `VACUUM`, the block fires only when an active consumer's last committed offset predates the
  file retention the VACUUM would enforce (the D03 stranded-file case) — not on every VACUUM.
- **On block.** The op is denied with a message that names each affected consumer (query id,
  source table, owner) and the safe alternative — truncate + insert, clone-and-swap, or
  widening `deletedFileRetentionDuration`.
- **On no affected consumer.** The op is allowed silently. A guard the operator never
  notices when it isn't needed is the goal.
- **Precision requirement (load-bearing).** A false-positive block — refusing an op on a
  table nothing streams from — is a serious behavioral defect: it trains operators to
  disable the hook, destroying the protection for the tables that actually need it. The
  block fires **only on positive confirmation** of a live-and-affected consumer.
- **Degradation.** If the hook cannot read `system.streaming.query_progress` (no managed SQL
  MCP, missing grant), it degrades to a loud advisory warning that surfaces the risk and asks
  for explicit confirmation — it does **not** hard-block on unknown state, because
  fail-closed here manufactures the exact false positives the precision requirement forbids.

## Success criteria

Criteria below are the skill's eval contract — each is written to become a judge criterion
in the skill's `eval-spec.yaml`.

1. Triggers on streaming / Delta guardian questions ("ConcurrentAppendException", "streaming
   source file not found", "safe to drop this streamed table", "VACUUM my streaming source",
   "checkpoint reset to batch 0") and does not trigger on unrelated Databricks prompts — eval
   criterion `triggers-on-streaming-guardian-question` (blocker) plus should-not-trigger
   control cases.
2. A `DROP TABLE` / `CREATE OR REPLACE TABLE` against a table with a confirmed active
   `query_progress` consumer is refused, and the refusal names the consumer — eval criterion
   `blocks-irreversible-op-on-live-consumer` (blocker).
3. The same op against a table with no active consumer is allowed; the hook never blocks on
   an absent or unaffected consumer — eval criterion `never-false-positive-blocks`
   (regression-critical). This is the precision requirement above.
4. When `query_progress` is unreadable, the hook warns and requests explicit confirmation
   rather than hard-blocking — eval criterion `degrades-to-advisory-when-state-unknown`
   (regression-critical).
5. Every diagnosis names the actual error code (`DELTA_FILE_NOT_FOUND`,
   `ConcurrentAppendException`, `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`,
   `UnknownFieldException`, and the rest) and its specific recovery, never a generic "restart
   and retry" — eval criterion `names-error-code-and-recovery` (blocker).
6. The `merge-rewriter` subagent's rewritten predicate includes the target's actual
   clustering keys (read from `DESCRIBE DETAIL`), narrowing the scanned file set — eval
   criterion `merge-rewrite-scopes-on-clustering-keys` (regression-critical).

## Functional requirements

The spine is **guard the irreversible op at trigger time, then diagnose and recover the
rest by the real error code** — deterministic probes for the arithmetic, a subagent for the
SQL rewrite, dual-MCP for evidence.

- **FR-1 (irreversible-op guard, D03/D07/D12):** The `PreToolUse` blocking hook above — fire
  on `VACUUM` / `DROP TABLE` / `CREATE OR REPLACE TABLE`, consult
  `system.streaming.query_progress`, block only on positive confirmation of a live-and-affected
  consumer, degrade to advisory on unknown state.
- **FR-2 (auto-compact collision probe, D01):** `scripts/pre-optimize-check.sh` reads
  `SHOW TBLPROPERTIES` + recent `DESCRIBE HISTORY` to detect auto-compaction activity in the
  last N minutes before a manual OPTIMIZE, and warns — advisory, not blocking, because OPTIMIZE
  is reversible.
- **FR-3 (MERGE predicate rewrite, D02):** The `merge-rewriter` subagent fetches the target's
  clustering keys via `DESCRIBE DETAIL`, rewrites the MERGE `ON` predicate to scope on them
  (or recommends `delta.enableRowTracking`), and cites the SCD2 / dedup / CDC cookbook in
  `references/`.
- **FR-4 (streaming-source recovery, D03/D04/D12):** `scripts/recover-streaming-source.py`
  runs the 4-way decision tree — fresh checkpoint + downstream dedup, restart at
  `startingVersion`, `FSCK REPAIR TABLE`, or widen `deletedFileRetentionDuration` — by
  comparing the latest available source version against the last committed checkpoint offset.
- **FR-5 (state + DLT + Auto Loader guardrails, D05/D06/D08/D09/D10):** Grade RocksDB
  bounded-memory config from `clusters_get`; guard DLT full refresh / threading via
  `pipelines_get` + a static grep; propose the Auto Loader `schemaHints` patch — deep knowledge
  loaded on demand from `references/*.md`.
- **FR-6 (dual-MCP evidence):** Control-plane reads via `databricks-workspace-mcp`
  (`clusters_get` / `clusters_events` / `clusters_list` / `pipelines_get`); `system.*` reads
  (`system.streaming.query_progress`, `DESCRIBE HISTORY`, `DESCRIBE DETAIL`,
  `SHOW TBLPROPERTIES`) via the managed SQL MCP, CLI Statement Execution API as the concrete
  fallback.
- **FR-7 (advisory-mode fallback):** With a plane absent, accept pasted `query_progress`
  output / checkpoint offsets / table config and still diagnose and recover; the hook degrades
  to advisory warn per the contract instead of failing.

## Out of scope

- Applying any fix or running the destructive op itself — the skill blocks a user's op or
  recommends a safe alternative; it never runs `VACUUM` / `DROP` / `CREATE OR REPLACE`, and it
  never mutates a table.
- Cost / spend analysis, including D11 (DLT serverless maintenance-cluster cost) — that is the
  sibling `databricks-cost-leak-hunter`; this skill guards data integrity, not dollars.
- Cluster launch, cold-start, and DBR-upgrade forensics — that is the sibling
  `databricks-cluster-forensics`; the RocksDB read here is scoped to the streaming-state OOM
  (D05), not general compute diagnosis.
- Authoring pipelines, cluster policies, or clustering strategy from scratch — that is
  `databricks-core-workflow-*` / `databricks-cost-tuning`; this skill guards live pipelines,
  it does not design new ones.
- Non-Databricks Spark (OSS Spark, EMR, Synapse) — the error codes, Liquid Clustering, DLT,
  Auto Loader, and the `system.streaming` tables are Databricks-specific.
