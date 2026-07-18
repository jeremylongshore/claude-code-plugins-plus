# ADR: databricks-streaming-guardian — blocking hooks for irreversible ops only, a precise consumer-state gate, deterministic recovery probes, a MERGE-rewriter subagent, and dual-MCP evidence

> Filed at `docs/ADR.md` beside the rest of the submission set, per
> `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills") — keeping the four docs atomic and inside the
> markdownlint-gated `plugins/**` tree. The ADR template's `000-docs/`-filing note
> (`NNN-AT-DECR-<slug>.md`) is the known alternative reading; the divergence is intentional
> and called out here.

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-12
**Status:** Accepted

## Context

This is the pack's only skill that sits at the moment a genuinely-destructive command runs.
Four forces shaped it. (1) The data-ops foot-guns are triggered by routine one-line
commands — `CREATE OR REPLACE TABLE`, `DROP TABLE`, `VACUUM`, a manual `OPTIMIZE`, a MERGE —
that the operator has run a hundred times, and the destructive part (a re-minted table UUID
that kills every consumer, a cleaned file a checkpoint still pins) is invisible until after
the command commits. A skill that narrates the failure afterward is too late; the value is a
guard *at the trigger*. (2) The block decision depends on live consumer state that exists in
exactly one place — `system.streaming.query_progress` — and getting the decision wrong in the
false-positive direction is worse than having no hook: a guard that refuses ops on tables
nothing streams from trains operators to disable it, and then it protects nothing. (3) The
eleven pains split cleanly into deterministic arithmetic (auto-compact collision detection,
checkpoint-offset-vs-source-version drift, retention-vs-lag) that must be **reproducible and
auditable**, and one genuinely LLM-shaped task — rewriting a MERGE predicate across an SCD2 /
dedup / CDC surface too varied for a regex. (4) The evidence is split across **two API
surfaces**: consumer state and table history live only in `system.*`, while pipeline
manifests and cluster Spark config live only in the control plane.

## Decision

We **merge the delta-conflict-resolver into this skill** rather than ship it standalone: the
Delta write conflicts (D01 `ConcurrentDeleteDeleteException`, D02 `ConcurrentAppendException`)
and the streaming-source failures (D03 / D04 / D12) are the same optimistic-concurrency and
checkpoint substrate a streaming operator debugs in one sitting — a MERGE conflict and a
file-not-found are the same engineer's afternoon. We ship a **`PreToolUse` hook that blocks**
`VACUUM` / `DROP TABLE` / `CREATE OR REPLACE TABLE` — the pack's only blocking hook, reserved
for ops with no undo — gated on a **precise, positive-confirmation-only** read of
`system.streaming.query_progress`, degrading to advisory warn when that state is unreadable.
Reversible ops (D01 OPTIMIZE, D09 full refresh) get advisory warnings, never blocks. The
deterministic work runs in **two bundled scripts** — `scripts/pre-optimize-check.sh`
(auto-compact collision probe for D01) and `scripts/recover-streaming-source.py` (the 4-way
checkpoint-recovery decision tree for D03) — so the LLM never eyeballs a timeline or an
offset. The one LLM-shaped task, the D02 MERGE predicate rewrite, runs in a **`merge-rewriter`
subagent** that reads the target's clustering keys and rewrites the `ON` predicate. Evidence
comes from **two MCP planes**: the `databricks-workspace-mcp` control plane
(`clusters_get` / `clusters_events` / `clusters_list` / `pipelines_get`) and the **Databricks
managed SQL MCP** (CLI Statement Execution API as the concrete fallback) for the `system.*`
reads. The skill **guards and recommends; it never runs the destructive op or mutates a
table** — and when a plane is absent it degrades to **advisory mode**, accepting pasted
`query_progress` / offsets / config. Deep knowledge (concurrency model, streaming recovery,
RocksDB tuning, VACUUM/time-travel, DLT + Auto Loader guardrails) loads from `references/*.md`
on demand.

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| Ship `delta-conflict-resolver` as a separate skill | The concurrency conflicts (D01/D02) and the streaming-source failures (D03/D04/D12) are the same OCC + checkpoint substrate — a MERGE that aborts and a stream that can't find its file are one operator's afternoon on the same table. A separate skill would split the guard from the recovery and force the operator to know which failure class they had before picking a skill. Merging keeps conflict-resolution and streaming-recovery in one flow. |
| Make the hooks advisory-only (warn, never block), like the rest of the pack | `DROP TABLE` / `CREATE OR REPLACE` / `VACUUM` on a live-consumer table is irreversible — the UUID is re-minted, the file is gone, and there is no undo. A warning the operator can scroll past is not enough when the op kills every downstream consumer. For genuinely-irreversible ops we block; for reversible ones (OPTIMIZE, full refresh) we warn. Blocking is scoped to the ops that earn it. |
| Block on any `DROP` / `CREATE OR REPLACE` / `VACUUM` regardless of consumer state (fail-closed) | This manufactures false positives on every table nothing streams from, and a hook that cries wolf gets disabled — which destroys the protection for the tables that need it. The block fires only on positive confirmation of a live-and-affected consumer; unknown state degrades to a loud advisory. Precision is the whole point of the hook. |
| Let the LLM read the checkpoint offset vs source version, or the auto-compact history, and estimate | The drift computation (committed offset vs latest version, VACUUM retention vs consumer lag) and the auto-compact collision probe are deterministic; a bundled script produces the same recovery recommendation and the same collision verdict every run and is reviewable line-by-line, while an LLM estimate is neither reproducible nor auditable. The LLM reasons on top — the same "the model does NOT do the load-bearing arithmetic" invariant the pack's cost and forensics skills hold. |
| Regex-rewrite the MERGE predicate in a script | The MERGE SQL surface (SCD2, dedup, CDC, multi-key) is far too varied for a regex; a wrong rewrite silently corrupts data. The `merge-rewriter` subagent reads the target's actual clustering keys via `DESCRIBE DETAIL` and rewrites the predicate to scope on them, keeping context small and the rewrite grounded in the table's real layout. |
| A single data plane — control-plane MCP only, or SQL only | Consumer state (`system.streaming.query_progress`) and table history (`DESCRIBE HISTORY` / `DESCRIBE DETAIL`) live only in `system.*`; pipeline manifests and cluster Spark config live only in the control plane. Either plane alone guards half the pains — the SQL plane can't read the DLT manifest, the control plane can't see who's streaming from a table. |
| Hard-require both MCP planes registered | On-call rarely has the full toolchain wired when a stream dies. Advisory mode accepts pasted `query_progress` / offsets / config and still diagnoses and recovers — weaker evidence, clearly labeled, still actionable — and the hook degrades to advisory warn rather than refusing to run. |

A further rejection is baked into the output contract: a generic "your stream failed — reset
the checkpoint and restart." Every diagnosis must name the *actual* error code
(`DELTA_FILE_NOT_FOUND`, `ConcurrentAppendException`,
`DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE`, `UnknownFieldException`) and its specific
recovery, enforced by the blocker eval criterion `names-error-code-and-recovery`.

## Consequences

**Positive:**

- The destructive op is guarded *at the trigger*, not narrated after the loss — the pack's
  only blocking hook stands exactly where `CREATE OR REPLACE` / `DROP` / `VACUUM` would kill a
  live consumer.
- The block is precise: positive-confirmation-only against `system.streaming.query_progress`,
  so a table nothing streams from is never refused — the `never-false-positive-blocks`
  criterion holds it there.
- Recovery is deterministic and reviewable: `recover-streaming-source.py` produces the same
  4-way recommendation from the same offset/version inputs, and `pre-optimize-check.sh` the
  same collision verdict.
- The D02 rewrite is grounded in the table's real clustering keys, not a regex guess, so the
  narrowed MERGE actually scans a non-overlapping file set.
- Merging conflict-resolution and streaming-recovery keeps the whole OCC + checkpoint surface
  in one skill the operator reaches for once.

**Negative / accepted tradeoffs:**

- The blocking hook is the highest-consequence primitive in the pack; a bug in target-table
  resolution or the consumer probe is felt immediately. Accepted, and mitigated by the
  positive-confirmation-only rule + the two regression-critical eval criteria guarding both
  false-positive and unknown-state behavior.
- The consumer probe requires the managed SQL MCP (or CLI Statement Execution access) and the
  `system.streaming` read grant; without it the hook can only advise, not block. Accepted —
  advisory-with-confirmation still surfaces the risk, and fail-closed would be worse.
- Two evidence planes mean more setup than a single-surface skill. Accepted as the price of
  guarding both table-integrity symptoms and pipeline/config symptoms in one pass.
- The RocksDB (D05) read overlaps the forensics skill's compute territory; it is scoped here
  to the streaming-state OOM only, not general cluster diagnosis. Accepted — the split keeps
  each skill's contract clean.
- Merging the conflict-resolver makes this a larger skill. Accepted — progressive disclosure
  keeps the concurrency, recovery, RocksDB, and DLT/Auto Loader knowledge in `references/*.md`,
  loaded only when a run hits that class.

## Tool-permission scope

No bare `Bash`: shell is scoped to a few binaries, and every MCP tool and CLI call is a
read-only `get` / `events` / `list` or `system.*` / `DESCRIBE` statement read. The bundled
scripts are local analyzers, the `merge-rewriter` subagent is a read-only rewriter that emits
SQL for a human to run, and the `PreToolUse` hook only *denies or allows* a user's op — it
never issues one. Nothing in the tool set can run `VACUUM` / `DROP` / `CREATE OR REPLACE`, or
otherwise mutate a table.

| Tool | Why it's needed |
| ---- | --------------- |
| `Read` | Load the on-demand `references/*.md` knowledge (concurrency model, streaming recovery, RocksDB tuning, VACUUM/time-travel, DLT + Auto Loader guardrails) and the per-check result artifacts. |
| `Write` | Write the rendered recovery report, the rewritten MERGE, and per-check detail artifacts to the runtime working dir (`$OUT`) — never into the skill package. |
| `Edit` | Rescope the report when the user narrows to one table or one pain class. |
| `Bash(databricks:*)` | CLI Statement Execution API for the `system.streaming.query_progress` consumer probe (the hook's block decision) and the `DESCRIBE HISTORY` / `DESCRIBE DETAIL` / `SHOW TBLPROPERTIES` reads — the managed SQL MCP is the preferred surface; this is the concrete fallback. |
| `Bash(jq:*)` | Parse statement-execution JSON and checkpoint-offset JSON and assemble the offset-vs-version input fed to the recovery tree. |
| `Bash(python3:*)` | Run `recover-streaming-source.py` (the 4-way checkpoint-recovery decision tree) — the script owns the offset/version drift arithmetic; the LLM never eyeballs an offset. |
| `Bash(bash:*)` | Run `pre-optimize-check.sh` (the auto-compact collision probe against `SHOW TBLPROPERTIES` + recent `DESCRIBE HISTORY`). |
| `Glob` | Collect the per-check `*.json` result artifacts and the source files the DLT-threading grep (D08) scans. |
| `mcp__databricks-workspace-mcp__clusters_list` | Enumerate clusters and resolve the target when the user names a symptom, not a cluster ID. |
| `mcp__databricks-workspace-mcp__clusters_get` | Read a stateful stream's cluster spec — Spark configs for the RocksDB bounded-memory grade (D05), `spark_version`, `runtime_engine`. |
| `mcp__databricks-workspace-mcp__clusters_events` | Pull cluster restart / stream-stop events that flag a stuck stream (D04) or the `UnknownFieldException` failure event (D10). |
| `mcp__databricks-workspace-mcp__pipelines_get` | Read the DLT pipeline manifest — source types and `pipelines.reset.allowed` for the full-refresh guard (D09), pipeline definition for the threading scan (D08). |
