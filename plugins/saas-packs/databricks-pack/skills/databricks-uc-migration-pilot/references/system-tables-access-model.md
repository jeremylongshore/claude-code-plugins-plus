# The Unity Catalog System-Tables Access Model

The migration pilot reads Unity Catalog **system tables** to do its job:
`system.billing.usage` to price the egress that a multi-region isolation pattern
adds, `system.access.audit` to prove who granted what during cutover,
`system.access.table_lineage` to order the view-migration graph, and
`system.query.history` / `system.compute.*` to spot the jobs still writing to
`hive_metastore`. Every one of those queries fails — often for the very operator
running the migration — with a denial that looks like a bug and is not:

```
[SELECT system.billing.usage] TABLE_OR_VIEW_NOT_FOUND: `system`.`billing`.`usage`
```

*(representative — the surface can also be `PERMISSION_DENIED` or an empty schema list.)*

The table is not missing and you are not under-privileged in the way you think.
System tables sit behind **two independent gates that admin-ness does not open**:
the schema must be **enabled** (an org-level Account Admin action), and the reader
must hold the **UC data-grant chain** on it (a Metastore Admin / owner action).
Being an Account Admin — the role that *enables* the schema — grants you **zero**
`SELECT` on its tables. This is the same two-layer model the
`uc-permission-tracer` subagent walks per access ticket; this reference is the
manual version so a human can follow the whole chain.

## The two-layer access model

UC deliberately separates **who administers the platform** from **who can read the
data** — including the platform's own telemetry.

- **Account Admin** — an org-level identity role. It manages metastores, creates
  and assigns them to workspaces, manages account-level users/groups/SCIM, and
  **enables system schemas**. It operates through account-level auth (the account
  console / account API), not a plain workspace token. What it does **not** confer:
  any `USE CATALOG`, `USE SCHEMA`, or `SELECT` on the data inside a metastore. An
  Account Admin who runs `SELECT * FROM system.billing.usage` is denied exactly
  like any unprivileged user until someone grants them the chain below.
- **Metastore Admin** (or an object **owner**) — the UC *data-governance* role. It
  holds `MANAGE`/grant authority over securables in the metastore and is the role
  that hands out `USE CATALOG system`, `USE SCHEMA system.<schema>`, and `SELECT`
  on specific system tables. This is a different job done by a (frequently
  different) person.

The load-bearing rule, and the #1 false assumption in UC access tickets:
**administrative roles do not inherit `SELECT`.** Account-admin-ness enables the
schema; it never reads it. Metastore-admin-ness can *grant* the read; the grant
still has to be issued (a metastore admin holds broad privilege but the clean,
always-correct mental model is "the chain must be satisfied for the principal
doing the reading"). Enablement and grant are two switches, thrown by two roles,
and **both** must be on before a byte of `system.*` is visible.

## Per-schema enablement — each system schema is individually gated

The `system` catalog is not all-or-nothing. Every system **schema** carries its own
enable flag, and enabling one does nothing for the others — you enable
`billing`, then separately `access`, then separately `compute`, and so on. A
freshly created metastore typically exposes only a subset; the rest read as
"not found" until individually enabled.

| Schema | Representative contents | Typical default |
| --- | --- | --- |
| `access` | `audit`, `table_lineage`, `column_lineage` | requires enablement |
| `billing` | `usage`, `list_prices` | on by default in newer workspaces |
| `compute` | `clusters`, `warehouses`, `node_types`, `node_timeline` | requires enablement |
| `query` | `history` | requires enablement (preview) |
| `storage` | `predictive_optimization_operations_history` | requires enablement |
| `serving` | `endpoint_usage`, `served_entities` | requires enablement |
| `lakeflow` | `jobs`, `job_run_timeline`, `pipelines` | requires enablement |
| `information_schema` | per-catalog metadata views | **on by default, per catalog** |

*(Schema availability and default-enabled state drift across releases and clouds —
treat this table as representative and confirm the live state in the account
console → **Metastore → System schemas**. `billing` and `access` in particular have
shifted between "requires enablement" and "auto-enabled"; do not hardcode either.)*

Two precision points the pilot depends on:

- **There is no standalone `system.lineage` schema.** Lineage lives **under
  `access`**: `system.access.table_lineage` and `system.access.column_lineage`.
  Enabling `access` is therefore what lights up both audit *and* lineage — the
  view-ordering logic and the audit trail share one enable flag.
- **`information_schema` is always on and needs no enable call** — it exists in
  *every* catalog (`system.information_schema`, `main.information_schema`, …) the
  moment the catalog exists. It is the one "free" metadata surface; the gated,
  enable-then-grant schemas above are the ones this reference is about.

## The end-user grant chain

Once a schema is enabled, a reader still needs the **full three-link chain** —
the identical chain UC enforces on any catalog. A missing link **anywhere** denies,
and the denial does not tell you which link is missing:

```sql
-- All three are required to read ONE table. Grant the traversal (catalog+schema)
-- once per group, then SELECT on each intended table.
GRANT USE CATALOG ON CATALOG system                TO `finops-readers`;
GRANT USE SCHEMA  ON SCHEMA  system.billing         TO `finops-readers`;
GRANT SELECT      ON TABLE   system.billing.usage   TO `finops-readers`;
GRANT SELECT      ON TABLE   system.billing.list_prices TO `finops-readers`;
```

The chain is **per-schema for the traversal grants and per-table for `SELECT`**:
`USE CATALOG system` is granted once, but each schema you want read needs its own
`USE SCHEMA system.<schema>`, and `SELECT` is scoped to individual tables (or the
whole schema via `GRANT SELECT ON SCHEMA system.access TO …` when you intend all of
it). Granting `SELECT` on `system.access.audit` without `USE SCHEMA system.access`
denies. Granting `USE SCHEMA` without `USE CATALOG system` denies. The #1 wrong
fix is "grant SELECT" when the actually-missing link is `USE SCHEMA`.

## Step-by-step enablement procedure

The end-to-end path crosses three roles. Skipping any one leaves the table invisible.

**1. Account Admin enables the system schema.** This needs **account-level auth** —
a plain workspace-user PAT is rejected because enablement is an account-admin
operation, not a metastore-data operation. Use the CLI (version-robust) or the raw
REST call; both require the caller to hold the account-admin role.

```bash
# Resolve the metastore id first (needs an authenticated CLI).
databricks metastores summary --output json | jq -r '.metastore_id'

# Enable the `access` schema (audit + lineage) and `billing` on that metastore.
# Caller MUST be an account admin; a non-admin workspace token errors out.
databricks system-schemas enable <metastore_id> access
databricks system-schemas enable <metastore_id> billing
# (older CLI builds spell this `databricks unity-catalog system-schemas enable …`)

# Equivalent raw REST — served at the workspace UC host, but the token must be
# account-admin-capable. Endpoint version is representative; confirm against the
# current System Schemas REST reference before scripting it.
curl -sS -X PUT \
  "https://<workspace-host>/api/2.1/unity-catalog/metastores/<metastore_id>/systemschemas/access" \
  -H "Authorization: Bearer $DATABRICKS_TOKEN"
```

A successful enable returns the schema in `state: ENABLE_COMPLETED` *(representative)*;
re-list with `databricks system-schemas list <metastore_id>` to confirm.

**2. Metastore Admin grants the chain to a group.** Never grant to individual users —
grant to a group and manage membership in the IdP (step 3). This is a *different
person/role* from step 1:

```sql
GRANT USE CATALOG ON CATALOG system              TO `finops-readers`;
GRANT USE SCHEMA  ON SCHEMA  system.access        TO `platform-auditors`;
GRANT SELECT      ON SCHEMA  system.access        TO `platform-auditors`;  -- all audit+lineage tables
GRANT USE SCHEMA  ON SCHEMA  system.billing       TO `finops-readers`;
GRANT SELECT      ON TABLE   system.billing.usage TO `finops-readers`;
```

**3. The IdP adds users to the granted group.** Membership flows from your identity
provider through SCIM into UC's account-level group. Nested groups are where this
silently breaks: **UC evaluates account-level group membership**, so a user in
group A, where A is a member of grant-holding group B, is covered **only if the
nesting is materialized at the account level** — a workspace-local group, or a
nested-group expansion the SCIM bridge did not flatten, does not carry the
account-level grant. See the nested-group and SCIM-flattening caveats in
`scim-bridge-patterns.md` before assuming a nested membership is effective.

## Audit-trail considerations

Every grant issued in step 2 is a governance event and should be logged — and UC
logs it for you, **in a system table that is itself one of these gated schemas**:
`system.access.audit`. Grant/revoke operations on securables surface there under
the `unityCatalog` service (action names like `updatePermissions` / `createGrant`
are *representative* — confirm against your rows), with the actor, target
securable, and change recorded.

The chicken-and-egg to plan around: **`system.access.audit` only captures events
from the moment the `access` schema is enabled.** Enable `access` *first*, before
you begin issuing the migration's grants, or the early grants (including the grant
that opens the audit table itself) land before auditing is on and never appear.
For a clean cutover record, enablement of `access` is step zero, and the group
that reads the audit table (`platform-auditors` above) is granted before the bulk
grant work starts — so the audit trail of the migration is complete from the first
grant forward.

## Worked traversal — "why does THIS user not see THIS table"

This is the exact graph `uc-permission-tracer` automates, walked by hand for
`alice@corp.com` hitting a denial on `system.billing.usage`. Walk the nodes in
order; the **first** broken link is the answer, but check them all — a lower link
can also be missing.

```
Trace: alice@corp.com → system.billing.usage  (denied)

0. Schema enabled?
   system-schemas list <metastore_id> → billing: ENABLE_COMPLETED ✓
   (if DISABLED/absent → NOT a grant problem; Account Admin must enable it — step 1)

1. Admin short-circuit (does NOT grant access — just note it):
   account-admin: yes   ← the false lead. Admin role does NOT inherit SELECT.
   metastore-admin: no
   → being account admin is why alice could ENABLE billing, and is irrelevant to
     READING it. Keep walking.

2. USE CATALOG system:
   granted to `finops-readers` ✓   alice ∈ finops-readers?  yes ✓

3. USE SCHEMA system.billing:
   granted to `finops-readers` ✓   ✓

4. SELECT system.billing.usage:
   granted to `finops-readers` ✗   ← the table-level SELECT was never granted
                                      (only list_prices was). BROKEN LINK.

Resolution: the missing link is table-level SELECT, not membership and not
enablement. A metastore admin runs:
   GRANT SELECT ON TABLE system.billing.usage TO `finops-readers`;
```

A second common shape: links 2–4 all show "granted to `finops-readers` ✓" yet alice
is still denied. Then the break is **membership**, not a grant: alice is in a
workspace-local group that *nests* `finops-readers`, but UC only honors
account-level nesting — the fix is an IdP/SCIM membership change (step 3), and no
additional `GRANT` will help. Prescribing another grant here is the classic wrong
answer.

## Sources

- Databricks — *Monitor usage with system tables* (system catalog overview,
  per-table reference), docs.databricks.com `/admin/system-tables`.
- Databricks — *Enable system table schemas* (per-schema enablement, System Schemas
  API / `databricks system-schemas` CLI, account-admin requirement),
  docs.databricks.com `/admin/system-tables/#enable`.
- Databricks — *System tables: `access` (audit logs + table/column lineage)* and
  *`billing` (usage, list_prices)* schema references, docs.databricks.com.
- Databricks — *Unity Catalog privileges and securable objects* (the
  `USE CATALOG` → `USE SCHEMA` → `SELECT` grant chain; grant-only model),
  docs.databricks.com `/data-governance/unity-catalog/manage-privileges`.
- Databricks — *Account admin vs. metastore admin roles* (who enables vs. who
  grants), docs.databricks.com `/admin/` + `/data-governance/unity-catalog/`.
