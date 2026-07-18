# Databricks Streaming Guardian

**Guards live Delta Lake / Structured Streaming / Auto Loader / DLT pipelines against the data-ops foot-gun catalog — and is the pack's only skill whose PreToolUse hook blocks a genuinely-irreversible op (VACUUM, DROP TABLE, CREATE OR REPLACE) when active streaming consumers still read the table, then recovers the failure by its actual error code.**

## Problem

The data-ops layer loses data silently, triggered by routine commands. A
`CREATE OR REPLACE TABLE` re-mints a Delta UUID and kills every streaming consumer with
`DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE` (D12); a default-retention `VACUUM` cleans
a file a lagging checkpoint still pins, and the stream is dead until a human reconciles it
(D03) — the same boundary that severs time travel mid-investigation (D07). A manual
`OPTIMIZE` collides with auto-compaction (D01); a MERGE on a Liquid-Clustered table throws
`ConcurrentAppendException` despite "touching different rows" (D02); a checkpoint resets to
batch 0 (D04); RocksDB state OOM-kills the driver (D05); a DLT full refresh silently drops
weeks of history (D09); an Auto Loader stream stops on a new column (D10). None announces
itself as destructive — the destructive part is a one-line command run a hundred times.

## Solution

A guard-at-trigger, then recover-by-error-code pipeline. A `PreToolUse` hook stands at
`VACUUM` / `DROP TABLE` / `CREATE OR REPLACE TABLE`, reads `system.streaming.query_progress`,
and blocks the op only on positive confirmation of a live-and-affected consumer — naming it —
while degrading to an advisory warning when consumer state is unreadable, so it never
false-positive-blocks a table nothing streams from. Two deterministic scripts
(`pre-optimize-check.sh` auto-compact probe, `recover-streaming-source.py` 4-way recovery
tree) own the arithmetic; a `merge-rewriter` subagent rewrites a conflicting MERGE to scope
on the table's clustering keys; five references carry the concurrency, recovery, RocksDB, and
DLT / Auto Loader knowledge. Evidence spans two MCP planes — the `databricks-workspace-mcp`
control plane and the Databricks managed SQL MCP over `system.*` — with an advisory-mode
fallback on pasted state. It guards and recommends; it never runs the destructive op.

## W5

|           |                                                                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | Streaming / data-platform engineers, pipeline owners debugging Delta write conflicts, and DLT / Auto Loader authors                     |
| **What**  | Blocks a genuinely-irreversible op when live consumers read the table, and recovers the eleven data-ops foot-guns by their actual error code + specific fix |
| **When**  | About to `CREATE OR REPLACE` / `DROP` / `VACUUM` a streamed source; a stream just died on file-not-found / UUID-change / checkpoint reset; a MERGE keeps aborting |
| **Where** | Claude Code (also Codex-compatible), against a Databricks workspace with the workspace MCP registered and `system.streaming` readable   |
| **Why**   | The block stands at the trigger with no undo behind it, and it's precise — positive-confirmation-only, so it never cries wolf on a table nothing streams from |

## Stack

| Layer | Choice |
| ----- | ------ |
| Skill runtime | Claude Code `SKILL.md` (compatibility: Codex) |
| Guard | `PreToolUse` blocking hook on `VACUUM` / `DROP TABLE` / `CREATE OR REPLACE TABLE`, gated on `system.streaming.query_progress` |
| Control-plane evidence | `databricks-workspace-mcp` — `clusters_get` / `clusters_events` / `clusters_list` / `pipelines_get` |
| SQL / system evidence | Databricks managed SQL MCP over `system.*` (CLI Statement Execution API fallback) — `query_progress`, `DESCRIBE HISTORY` / `DESCRIBE DETAIL`, `SHOW TBLPROPERTIES` |
| Deterministic analysis | Bundled `pre-optimize-check.sh` (auto-compact collision probe), `recover-streaming-source.py` (4-way recovery tree) |
| Fan-out | `merge-rewriter` subagent — rewrites a MERGE predicate to the target's clustering keys |
| Knowledge | `references/*.md` loaded on demand (concurrency model, streaming recovery, RocksDB tuning, VACUUM/time-travel, DLT + Auto Loader guardrails) |

## Differentiators

1. **The pack's only hook that blocks — and blocks precisely** — it refuses `VACUUM` /
   `DROP` / `CREATE OR REPLACE` only when `system.streaming.query_progress` positively
   confirms a live-and-affected consumer, and degrades to advisory when state is unknown, so
   it guards the irreversible ops without ever false-positive-blocking a table nothing streams
   from.
2. **Names the error code, doesn't reset-and-hope** — every diagnosis lands on the actual
   code (`DELTA_FILE_NOT_FOUND`, `ConcurrentAppendException`,
   `DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`, `UnknownFieldException`) and its specific
   recovery, where the v1 skills only narrate the symptom.
3. **The LLM never does the load-bearing arithmetic** — deterministic scripts own the
   auto-compact collision probe and the offset-vs-version recovery tree, and the `merge-rewriter`
   subagent grounds the D02 rewrite in the table's real clustering keys, not a regex; the LLM
   reasons on top.
