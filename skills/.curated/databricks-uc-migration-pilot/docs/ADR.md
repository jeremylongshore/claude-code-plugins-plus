# ADR: databricks-uc-migration-pilot — deterministic readiness audit, two planner/tracer subagents, classify-not-migrate, two data planes

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

An HMS→UC migration plan is only worth shipping if a metastore admin can trust every
per-table verdict in it and execute the plan in order without surprises. Three forces
shaped the design. (1) The **September 30, 2026** HMS end-of-support deadline makes this
non-optional for every HMS customer, and the migration is blocked by conditions that a
prose checklist or an eyeballed table list never catches — managed tables on the DBFS
root, external tables on retired schemes (`adl://`, `wasbs://`), LEGACY_TABLE_ACL-only
compute, and the CLONE-drops-Delta-history loss. (2) The decision of what to do with each
of hundreds-to-thousands of tables is a precise, rule-based classification over the
table's storage URI and type — the kind of thing that must be **reproducible and
auditable**, not an LLM guess that varies run to run. (3) Whether a table is actually
migratable is split across **two systems**: the Databricks metadata (table type + storage
URI) says whether the shape is right, but the **cloud IAM layer** says whether the storage
credential's role will authorize UC to read that path — and a table that looks "ready" on
the metadata plane still fails `SYNC` when the IAM trust policy is wrong.

## Decision

We ship a **deterministic bundled readiness audit** (`scripts/audit-hms-readiness.py`)
that classifies every `hive_metastore` table by storage-URI scheme and table type into
**ready / blocked / orphan** with a named blocker, and emits a readiness CSV — the LLM
never eyeballs migratability. Two focused **subagents** consume it: a `migration-planner`
that turns the CSV into a **dependency-ordered per-table plan** assigning one verb (`SYNC`
/ `DEEP CLONE` / rewrite / skip) and flagging every CLONE target as time-travel-lossy; and
a `uc-permission-tracer` that diagnoses UC's **two-level access model** ("user X needs
group Y membership AND grant Z run by metastore admin W"). A `/uc-env-pattern-picker`
decision tree resolves the **one-metastore-per-region** constraint into a concrete
catalog/binding/region pattern. Evidence comes from **two data planes**: the Databricks
CLI **Statement Execution API** for HMS inventory, UC grants, and system tables; and
**read-only AWS IAM introspection** for the storage-credential (D2) diagnosis. The skill
**classifies and plans; it never executes the migration** — `SYNC`, `CLONE`, `DROP`, and
`GRANT` are emitted as reviewed steps for a human in a maintenance window. Deep knowledge
(storage-scheme table, migration-verb playbook, UC access model, isolation patterns) loads
from `references/*.md` on demand.

## Alternatives considered

| Alternative                                                       | Why rejected                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Let the LLM read the table list and judge migratability inline    | Storage-scheme classification is a precise, rule-based decision over thousands of tables; a bundled script produces the same CSV from the same inventory and is reviewable line-by-line, while an LLM verdict is neither reproducible nor auditable — the same "the model does NOT do the load-bearing arithmetic" invariant the pack's cost skill holds. |
| One monolithic prompt doing audit + plan + trace + isolate        | Planning (over a static readiness CSV) and permission-tracing (over a live grant + identity graph) are different problems with different inputs. Two subagents keep each context small and independently testable, and let the tracer run standalone for "why can't user X see this table" without re-auditing.                                          |
| Auto-migrate — run `SYNC`/`CLONE`/rewrite once tables are classified | Migration is irreversible-in-effect (data copies, dropped history, cutover) and must pass human review plus a maintenance window. Auto-running it unattended across hundreds of tables is the exact failure this skill exists to prevent.                                                                                                             |
| Just run Databricks Labs UCX and read its assessment report       | UCX is a heavyweight batch assessment; this skill is the agent-native pilot — a focused readiness audit + dependency-ordered plan + live permission trace delivered conversationally in Claude Code, and it adds the cloud-IAM storage-credential plane and the environment-isolation decision tree a UCX assessment does not hand you. Complementary, not a replacement.  |
| Inline all UC-migration knowledge in the skill body               | The storage-scheme table, verb playbook, two-level access model, and isolation patterns are deep; loading them on every invocation bloats every run. They live in `references/*.md`, read only when a table hits that case.                                                                                                                            |

A further rejection is baked into the output contract: a single "ready / not-ready" verdict
with no reason. Every blocked or orphan table must carry the *specific* blocker
(`dbfs:/` root, `wasbs://`/`adl://`, LEGACY_TABLE_ACL compute, dangling location), enforced
by the regression-critical eval criterion `classifies-every-table-with-reason`.

## Consequences

**Positive:**

- Every table gets a deterministic, reproducible classification tied to its real storage
  URI — same inventory, same CSV, reviewable in `scripts/audit-hms-readiness.py`.
- The plan is dependency-ordered and one-verb-per-table, so the team executes in a safe
  order and knows exactly which tables lose Delta time-travel on CLONE **before** cutover.
- The permission tracer converts "user X can't see the table" from a ~90-minute support
  ticket into a one-shot diagnosis naming the missing group membership and/or grant, and
  who must run it.
- `/uc-env-pattern-picker` turns the one-metastore-per-region constraint into a concrete
  catalog/binding/region decision instead of a surprise discovered mid-migration.
- Classify-not-migrate keeps every irreversible action behind human review and a
  maintenance window.

**Negative / accepted tradeoffs:**

- Hard prerequisites: a UC metastore already created in the region, account-admin
  (system-schema enablement), metastore-admin (grant reads / external locations / `SYNC`),
  and AWS-side IAM read access for the storage-credential diagnosis. Missing any one
  narrows what the skill can confirm — accepted, because a plan that cannot verify the
  storage credential is a plan that fails at execution.
- The skill stops at a reviewed plan; a human still runs `SYNC`/`CLONE`/rewrite/grants in a
  maintenance window. Accepted — auto-migration is the failure mode, not the feature.
- The live IAM (D2) plane is AWS-first; Azure managed-identity and GCP service-account
  storage-credential diagnosis degrade to a manual external-location verification step.
  Accepted — the metadata plane is cloud-neutral and still classifies every table.
- A script + two subagents + on-demand references is more moving parts than a single
  prompt. Accepted as the price of a reproducible audit and independently-runnable
  permission tracing.

## Tool-permission scope

No bare `Bash`: shell is scoped to three binaries (`databricks`, `jq`, `python3`), and the
AWS surface is used only for **read-only** STS/IAM introspection (`aws sts
get-caller-identity`, `aws iam get-role`) — never a write/create/update verb. Nothing in
the tool set can mutate a workspace, a grant, a table, or an IAM role. The two subagents
(`migration-planner`, `uc-permission-tracer`) are read-only analyzers the skill dispatches;
the migration itself is never executed — it is emitted as a reviewed plan.

| Tool                 | Why it's needed                                                                                                                                                                                                              |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Read`               | Load the on-demand `references/*.md` knowledge (migration blockers / storage-scheme classification, migration-verb playbook, UC two-level access model, env-isolation patterns) and the readiness CSV + per-table plan artifacts. |
| `Write`              | Write the readiness CSV, the migration plan, and the permission-trace report to the runtime working dir (`$OUT`) — never into the skill package.                                                                             |
| `Edit`               | Rescope the generated plan when the user defers a schema or changes a table's assigned verb.                                                                                                                                |
| `Bash(databricks:*)` | CLI Statement Execution API: the `hive_metastore` inventory scan (`SHOW SCHEMAS`/`SHOW TABLES`, `DESCRIBE EXTENDED` for storage location + table type), UC grant reads (`SHOW GRANTS`), the `SYNC` dry-run probe, and `system.*` reads. |
| `Bash(jq:*)`         | Parse Statement Execution JSON, inject `warehouse_id` into the SQL template, and assemble the readiness CSV rows.                                                                                                            |
| `Bash(python3:*)`    | Run the bundled `scripts/audit-hms-readiness.py` storage-URI-scheme classifier over the inventory (the script owns the READY/BLOCKED/ORPHAN verdict — the LLM never eyeballs a URI).                                          |
| `Bash(aws:*)`        | Read-only STS/IAM introspection for the D2 storage-credential diagnosis — confirm the running principal (`aws sts get-caller-identity`) and inspect the storage-credential role's trust policy + read permissions on the external-location path (`aws iam get-role`). No IAM write verb is used. |
| `Glob`               | Collect the readiness CSV and per-table plan artifacts for the planner and tracer steps.                                                                                                                                    |
