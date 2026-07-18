# PRD: databricks-uc-migration-pilot

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-12
**Status:** Active

> Authored to the `templates/skill-docs/` submission standard at the Pack / flagship tier
> (this is a `databricks-pack` skill) as the design record for `databricks-uc-migration-pilot`,
> per `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills"). Companion docs beside it: `ADR.md`, `ONE-PAGER.md`.

## Problem

Every Databricks customer still on the legacy Hive Metastore (HMS) has to move to Unity
Catalog (UC), and almost none of them can eyeball their way there. A `hive_metastore`
table list looks migratable until you check the two things that actually decide it: the
table's real storage URI and its compute. Migration silently stalls on non-obvious
conditions — managed tables sitting on the DBFS root (`dbfs:/user/hive/warehouse`) that UC
will not govern; external tables backed by retired or deprecated storage schemes
(`adl://` ADLS Gen1, `wasbs://` legacy Blob) that must be re-pointed before UC will touch
them; tables whose only reader is a cluster still in **LEGACY_TABLE_ACL** access mode,
which UC does not support; and the **CLONE-drops-Delta-history gotcha** — a `DEEP CLONE`
copies today's data but the new table's time-travel history starts fresh, so a team that
relies on `VERSION AS OF` loses it and finds out after cutover, not before.

Then, once tables land in UC, access breaks in a way HMS never did. UC has a two-level
identity-plus-privilege model, and "user X can no longer see the table" almost never has
one cause — it resolves to a missing **group membership** (identity plane) OR a missing
link in the `USE CATALOG` → `USE SCHEMA` → `SELECT` grant chain (privilege plane, run by
the right admin), and untangling which eats roughly **90 minutes per support ticket**.
The existing v1 skills for this (`databricks-upgrade-migration`,
`databricks-migration-deep-dive`) are documentation cosplay — prose that describes
migration without ever reading a single table's storage URI, ordering a plan, or tracing
a live grant.

## The forcing function

**HMS reaches end-of-support and becomes read-only on September 30, 2026.** After that
date there is no "we'll migrate later" — schema changes, new tables, and the tooling that
depended on a writable HMS stop working. That deadline is what turns this from a
nice-to-have hygiene task into a dated, non-optional project for every HMS workspace, and
it is why a skill that produces a *reviewed, dependency-ordered plan* — not more prose —
is worth shipping now while there is still runway to execute it in maintenance windows.

## Target users

| User                          | Context                                                                                              | Primary need                                                                                                     |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Data-platform / lakehouse eng | Owns the HMS→UC project against the Sept-30-2026 clock; hundreds–thousands of `hive_metastore` tables | A real per-table readiness verdict (ready / blocked / orphan) and a dependency-ordered plan, not a prose checklist |
| Databricks workspace + metastore admin | Runs the grants, `SYNC`s, and external locations; owns cutover                              | A verb per table (SYNC / deep-clone / rewrite / skip) with the CLONE-history-loss tables flagged before execution |
| Platform / support engineer   | Fields "user X can't see `cat.sch.tbl` anymore" after tables move to UC                              | A one-shot trace of the two-level access model — the missing group AND/OR the missing grant, and who must run it |
| Data-platform architect       | Decides dev/staging/prod isolation under one UC metastore per region                                 | A decision tree that resolves the one-metastore-per-region constraint into a concrete catalog/binding/region pattern |

## Success criteria

Criteria below are the skill's eval contract — each is written to become a judge criterion
in the skill's `eval-spec.yaml`.

1. Triggers on HMS→UC migration questions ("migrate off Hive metastore", "Unity Catalog
   migration", "is this table ready for UC", "why can't user X see the table in UC") and
   does not trigger on unrelated Databricks prompts — eval criterion
   `triggers-on-uc-migration-question` (blocker) plus should-not-trigger control cases.
2. The readiness audit classifies every HMS table deterministically by storage-URI scheme
   and table type into **ready / blocked / orphan**, and names the specific blocker
   (`dbfs:/` root, `wasbs://`/`adl://`, LEGACY_TABLE_ACL compute, orphaned location) rather
   than a generic "not ready" — eval criterion `classifies-every-table-with-reason`
   (regression-critical).
3. The plan assigns exactly one migration verb per table (SYNC / deep-clone / rewrite /
   skip), orders tables so dependencies (e.g. views after base tables) come out safe, and
   **flags every table that will lose Delta time-travel on CLONE before cutover** — eval
   criterion `plan-is-ordered-and-flags-history-loss` (blocker).
4. A UC access failure is diagnosed as a concrete two-part answer — the missing group
   membership AND/OR the missing grant in the `USE CATALOG`/`USE SCHEMA`/`SELECT` chain,
   plus who (metastore admin / catalog owner) must run it — eval criterion
   `traces-two-level-access-model`.
5. The skill classifies and plans; it never executes `SYNC`, `CLONE`, `DROP`, or a grant —
   every migration action is emitted as a reviewed step for a human to run in a maintenance
   window — eval criterion `never-mutates-the-workspace` (regression-critical).

## Functional requirements

The pipeline is **detect → plan → trace → isolate**.

- **FR-1 (detect):** Run the bundled `scripts/audit-hms-readiness.py` over the full
  `hive_metastore` inventory (`SHOW SCHEMAS`/`SHOW TABLES` + `DESCRIBE EXTENDED` for
  storage location and table type via the CLI Statement Execution API); classify each
  table's storage-URI scheme as **ready** (`s3://`/`s3a://`, `abfss://`, `gs://`),
  **blocked** (`wasbs://`, `adl://`, `dbfs:/user/hive`/DBFS root, LEGACY_TABLE_ACL-only
  compute), or **orphan** (missing/dangling location); emit a readiness CSV.
- **FR-2 (plan):** The `migration-planner` subagent turns the readiness CSV into a
  dependency-ordered per-table plan, assigning each table a verb — `SYNC` (external tables
  already on a UC-supported scheme), `DEEP CLONE` (managed tables to move off DBFS root),
  rewrite/CTAS (format or conversion cases), or skip (orphan/blocked/unused) — and marks
  every CLONE target as time-travel-lossy.
- **FR-3 (trace):** The `uc-permission-tracer` subagent diagnoses UC's two-level access
  model, resolving a "user X cannot read `cat.sch.tbl`" report into the missing group
  membership (identity plane) and/or the missing grant in the three-tier chain (privilege
  plane), naming the admin who must run the fix.
- **FR-4 (isolate):** `/uc-env-pattern-picker` walks the one-metastore-per-region
  constraint into a concrete isolation pattern — catalog-per-environment with
  workspace-catalog binding, separate regions, or separate accounts — by isolation
  strictness and topology.
- **FR-5 (storage-credential diagnosis, D2):** For a table the metadata plane calls
  "ready" that still fails to `SYNC`, corroborate on the cloud IAM plane — read-only AWS
  IAM introspection of the storage credential's role (does it trust Databricks, is it
  self-assuming, can it read the external-location path) — so the plan flags the real
  blocker instead of mislabeling the table ready.
- **FR-6 (fail-fast prerequisites):** Verify the prerequisite chain upfront — a UC
  metastore exists in the region, system schemas are enabled (account-admin), and the
  running principal is a metastore admin for grant reads — and report the exact missing
  prerequisite verbatim rather than dying mid-audit.

## Out of scope

- **Executing the migration.** The skill emits a reviewed plan; a human runs `SYNC` /
  `CLONE` / rewrite / grants in a maintenance window. No `SYNC`, `CLONE`, `DROP`, `CREATE
  EXTERNAL LOCATION`, or `GRANT` is ever run by the skill.
- **Provisioning the UC metastore, storage credentials, or external locations.** Those are
  one-time account-admin setup; this skill assumes a metastore already exists in the region
  and diagnoses (never creates) storage credentials.
- **Authoring governance policy** (row/column masks, tags, lineage strategy) — that is
  downstream of a completed migration, not part of getting off HMS.
- **Non-AWS storage-credential diagnosis at parity.** The metadata plane classifies every
  table on any cloud; the live IAM (D2) corroboration is AWS-first — Azure managed-identity
  and GCP service-account credentials degrade to a manual external-location verification
  step.
- **Standard-tier / non-Unity-Catalog accounts** — there is no UC metastore to migrate
  into, so the readiness audit has no target.
