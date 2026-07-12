# ADR: databricks-cluster-forensics — deterministic event bucketing, a fan-out investigator subagent, dual-MCP evidence, and a merged upgrade advisor

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

A compute-layer diagnosis is only worth shipping if a 2 AM operator can trust the named
cause and act on the exact mitigation. Three forces shaped the design. (1) The platform
reports failures in umbrella codes and elapsed-minute counters that hide the cause — a
useful diagnosis has to correlate a cluster's raw lifecycle events into a per-stage /
per-cause attribution the operator cannot read off the cluster page. (2) That attribution
is arithmetic over event timestamps and exact facts about class files and source ASTs —
the kind of thing that must be **reproducible and auditable**, not an LLM guess that
varies run to run — while the root-cause reasoning *on top of* it is genuinely LLM-shaped.
(3) The evidence is split across **two API surfaces**: cluster lifecycle events live only
in the control plane (`clusters.events`), but the Photon-premium audit and node-timeline
reads live only in the `system.*` tables behind a SQL warehouse — and a cluster that looks
fine on one plane is bleeding on the other.

## Decision

We ship a **bundled deterministic bucketer** (`scripts/cluster-coldstart-forensics.py`)
that reads a cluster's `clusters.events` stream and splits PENDING time into named stages
(cloud VM allocation / network + DNS / library + init), plus two **pre-upgrade detectors** —
`scripts/find-cwd-writes.py` (AST scan for the DBR 14.x 500 MB CWD-write cap) and
`scripts/scan-jar-jdk.sh` (`javap` class-file-version scan for the 15.1 DBFS-root-lib
removal + JDK-11 drop) — so the LLM never eyeballs a timeline or a class file. A
**`cluster-event-investigator` subagent** fans out one root-cause thread per cause class
(cold-start / Photon-fallback / DBR-landmine / termination-umbrella / spot-shuffle),
keeping each context small and letting the classes run in parallel. Evidence comes from
**two MCP planes**: the `databricks-workspace-mcp` control plane for
`clusters_list`/`clusters_get`/`clusters_events`, and the **Databricks managed SQL MCP**
(with the CLI Statement Execution API as the concrete fallback) for the `system.*`
Photon-coverage and node-timeline reads. We **merge the DBR upgrade advisor into this
skill** rather than ship it standalone, because the upgrade landmines surface as the same
PENDING / termination symptoms the operator is already debugging. The skill **diagnoses
and recommends; it never restarts, resizes, edits, or terminates a cluster** — and when an
MCP plane is absent it degrades to **advisory mode**, accepting pasted events / config and
still naming the cause. Deep knowledge (termination-codes decode, DBR version-landmine
table, Photon fallback rules, event-stage reference) loads from `references/*.md` on
demand.

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| Ship `dbr-upgrade-advisor` as a separate skill | The 14.x / 15.1 / 15.4 landmines never announce themselves as "upgrade problems" — they surface as post-bump cluster failures (CWD write errors, JAR load failures, silently shifted dates), i.e. the exact PENDING / termination symptoms this skill already investigates. A 2 AM operator would have to know in advance the failure was upgrade-caused to pick the right skill. Merging keeps the upgrade landmines inside the same event-correlation flow. |
| Let the LLM read the event stream and estimate where PENDING time went | Event-stage bucketing is deterministic arithmetic over timestamps, and the class-file / AST detectors are exact scans; a bundled script produces the same buckets and the same landmine list every run and is reviewable line-by-line, while an LLM estimate is neither reproducible nor auditable. The LLM does the root-cause reasoning on top — the same "the model does NOT do the load-bearing arithmetic" invariant the pack's cost and migration skills hold. |
| One monolithic prompt walking all cause classes sequentially | The six pains are independent investigations with different inputs (lifecycle events vs `system.*` reads vs source AST vs JAR class files). A `cluster-event-investigator` subagent fans out one thread per cause class so each context stays small and the classes run in parallel, and the investigator can run standalone for a single symptom without loading the whole playbook. |
| A single data plane — control-plane MCP only, or SQL only | Cluster lifecycle events live only in the control plane; the Photon-premium-while-fallen-back audit and node-timeline reads live only in `system.*`. Either plane alone diagnoses half the pains and misses the other half. |
| Hard-require both MCP planes registered | On-call rarely has the full toolchain wired at 2 AM. Advisory mode accepts pasted `clusters.events` JSON / cluster config and still buckets, decodes, and names the cause — weaker evidence, clearly labeled, still actionable — rather than refusing to run. |

A further rejection is baked into the output contract: a generic "your cluster failed to
start — check your config and retry." Every diagnosis must name the *actual* error or
termination code (CLOUD_PROVIDER_LAUNCH_FAILURE, NPIP_TUNNEL_SETUP_FAILURE, the specific
stage-abort) and its version-specific mitigation, enforced by the regression-critical eval
criterion `names-error-code-and-version-mitigation`.

## Consequences

**Positive:**

- Cold-start diagnoses attribute PENDING time to a named stage, deterministic and
  reviewable in `scripts/cluster-coldstart-forensics.py` — same events, same buckets.
- The umbrella termination codes decode to one of five specific causes each, with the check
  to confirm that cause, instead of a retry.
- DBR upgrade landmines are caught *before* the bump by exact scanners (AST + `javap`),
  not discovered after cutover.
- The Photon audit names jobs paying the ~2× premium while operators fall back to Spark — a
  real leak the cluster page never shows.
- The fan-out investigator keeps each cause class independently testable and lets a single
  symptom be diagnosed without loading the full playbook.

**Negative / accepted tradeoffs:**

- Hard prerequisites: `databricks-workspace-mcp` registered (cluster events), the
  Databricks CLI authenticated, and a running SQL warehouse for the Photon / `system.*`
  reads. Missing any one narrows what the skill can confirm — accepted, because advisory
  mode still runs on pasted input.
- Two evidence planes plus a SQL warehouse mean more setup than a single-surface skill.
  Accepted as the price of diagnosing both lifecycle symptoms and billing / coverage
  symptoms in one pass.
- The Photon-coverage read overlaps the sibling cost skill's territory; it is scoped here to
  the fallback-while-billed forensic symptom only, not a spend report. Accepted — the split
  keeps each skill's contract clean.
- Merging the upgrade advisor makes this a larger skill. Accepted — progressive disclosure
  keeps the upgrade knowledge in `references/*.md`, loaded only when a run hits an upgrade
  case.
- Without an MCP plane, advisory mode leans on pasted events / config: weaker evidence,
  clearly labeled, still names the cause.

## Tool-permission scope

No bare `Bash`: shell is scoped to a few binaries, and every MCP tool and CLI call is a
read-only `list`/`get`/`events` or `system.*` statement read. The bundled scripts are
local analyzers, and the `cluster-event-investigator` subagent is a read-only analyzer the
skill dispatches. Nothing in the tool set can restart, resize, edit, or terminate a
cluster.

| Tool | Why it's needed |
| ---- | --------------- |
| `Read` | Load the on-demand `references/*.md` knowledge (termination-codes decode, DBR version-landmine table, Photon fallback rules, event-stage reference) and the per-cause result artifacts. |
| `Write` | Write the rendered forensic report and per-cause detail artifacts to the runtime working dir (`$OUT`) — never into the skill package. |
| `Edit` | Rescope the report when the user narrows to one cluster or one cause class. |
| `Bash(databricks:*)` | CLI Statement Execution API for the `system.*` Photon-coverage + node-timeline reads (the managed SQL MCP is the preferred surface; this is the concrete fallback), and the `clusters.events` fetch fallback when the workspace MCP is not registered. |
| `Bash(jq:*)` | Parse cluster-events JSON and statement-execution JSON and assemble the per-stage input fed to the bucketer. |
| `Bash(python3:*)` | Run the bundled `cluster-coldstart-forensics.py` (PENDING-time bucketer) and `find-cwd-writes.py` (AST scan for the 14.x CWD-cap writes) — the scripts own the bucketing and the flag list; the LLM never eyeballs a timeline. |
| `Bash(javap:*)` | Read each JAR's class-file major version in `scan-jar-jdk.sh` to flag JARs built against the removed JDK 11 before a 15.1+ bump. |
| `Glob` | Collect the per-cause `*.json` result artifacts for the investigator's fan-out and the final report. |
| `mcp__databricks-workspace-mcp__clusters_list` | Enumerate clusters and resolve the target when the user names a symptom, not a cluster ID. |
| `mcp__databricks-workspace-mcp__clusters_get` | Read a flagged cluster's live spec — `runtime_engine`, `spark_version`, spot config (`aws_attributes` / `azure_attributes`), `autotermination_minutes`. |
| `mcp__databricks-workspace-mcp__clusters_events` | Pull the raw lifecycle event stream (CREATING → STARTING → RUNNING, INIT_SCRIPTS events, TERMINATING + termination code) that the bucketer and the termination-decoder consume. |
