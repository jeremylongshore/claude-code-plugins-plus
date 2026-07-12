# The Five HMS-to-UC Migration Blocker Classes

Not every Hive Metastore (HMS) table can be lifted into Unity Catalog (UC) in
place. UC governs storage through **external locations** — a securable that binds
one cloud path (`s3://`, `abfss://`, `gs://`) to a storage credential — and it
enforces an **allow-only** permission model on clusters running a UC-compatible
access mode. Any HMS table whose storage, permission model, or dependency graph
falls outside those two facts is a blocker: it needs *physical relocation* or
*rewrite*, not a metadata registration.

Two primitives do the in-place work when a table *is* eligible:

- **`SYNC`** registers an HMS **external** table (or a whole schema) into UC
  without moving a byte — it just creates the UC table object over the same files
  and stamps `upgraded_to` on the source. It requires (a) the table be EXTERNAL,
  and (b) an existing UC external location covering the path. Run it `DRY RUN`
  first; it returns a row per table with `status_code` + `description`.
- **`DEEP CLONE`** makes a full physical copy of a Delta (or Parquet/Iceberg)
  table's data + metadata into a new UC table — the tool of choice whenever the
  data must physically move (DBFS root, unsupported scheme).

Each blocker below carries the assessment message UCX or the Databricks Migration
Assistant emits, the relocation/remediation procedure, and the per-cloud path
variant. Error strings marked *(representative)* are accurate paraphrases —
exact wording drifts across DBR and UCX versions; do not quote them as literals.

---

## Blocker 1 — `wasbs://` and `adl://` scheme tables (Azure legacy storage)

**Why it blocks.** UC external locations accept only the secure ADLS Gen2 driver
`abfss://` on Azure. The legacy Blob-storage WASB driver (`wasb://` / `wasbs://`,
endpoint `*.blob.core.windows.net`) and the ADLS Gen1 driver (`adl://`, endpoint
`*.azuredatalakestore.net`) cannot back a UC external location at all — you
cannot even create the securable over them. ADLS Gen1 is doubly dead: Microsoft
retired it on 2024-02-29, so an `adl://` table is un-migratable *and* on
end-of-life storage.

**Assessment message** *(representative)*:

```
[UCX assessment] table hive_metastore.sales.orders : storage scheme 'wasbs'
is not supported by Unity Catalog external locations (requires 'abfss').
SYNC status_code: UNSUPPORTED_LOCATION_SCHEME
```

**Remediation — physical relocation onto `abfss://`.** The endpoint changes from
the Blob endpoint (`.blob.`) to the DFS endpoint (`.dfs.`) on the same (Gen2-
enabled) storage account. Deep-clone the table onto an `abfss://` path that a UC
external location + storage credential already cover:

```sql
-- Move a wasbs-backed external Delta table onto a UC-governed abfss:// path
CREATE TABLE main.sales.orders
DEEP CLONE hive_metastore.sales.orders
LOCATION 'abfss://data@acct.dfs.core.windows.net/uc/sales/orders';
```

For `adl://` (Gen1) tables there is no in-account driver swap — Gen1 is gone —
so the data must be copied to a *new* Gen2 account first (AzCopy / ADF), then
deep-cloned or `SYNC`'d once it sits on `abfss://`.

**Per-cloud variants** (the same table on each cloud lands on):

- **AWS:** `s3://bucket/uc/sales/orders`
- **Azure:** `abfss://data@acct.dfs.core.windows.net/uc/sales/orders`
- **GCP:** `gs://bucket/uc/sales/orders`

Once the data already sits on `abfss://` (only the catalog registration is
missing), skip the copy and `SYNC` it in place:

```sql
SYNC TABLE main.sales.orders FROM hive_metastore.sales.orders DRY RUN;
SYNC TABLE main.sales.orders FROM hive_metastore.sales.orders;
```

---

## Blocker 2 — `dbfs:/user/hive/warehouse/...` managed tables (DBFS root)

**Why it blocks.** HMS **managed** tables written to the DBFS root
(`dbfs:/user/hive/warehouse/<db>.db/<table>`) have no cloud-native URI a UC
external location can reference — the DBFS root is an opaque, workspace-owned
storage layer, and UC refuses to govern it. `SYNC` also rejects them because they
are managed, not external. This is the single most common blocker in a mature
workspace: every table created with `CREATE TABLE …` and no `LOCATION` landed
here.

**Assessment message** *(representative)*:

```
[UCX] hive_metastore.sales.orders classified DBFS_ROOT_DELTA — managed table on
DBFS root cannot be SYNC'd; migrate via deep clone / CTAS.
SYNC status_code: DBFS_ROOT_LOCATION
description: Table located in DBFS root and cannot be synced to Unity Catalog.
```

(UCX's table-migration `What` enum tags these `DBFS_ROOT_DELTA` /
`DBFS_ROOT_NON_DELTA`; its `migrate-tables` workflow uses deep clone / CTAS for
them rather than SYNC.)

**Remediation — physically relocate into UC-managed storage.** Because the data
must actually move off the DBFS root, deep-clone (Delta) or CTAS (any format)
into a UC **managed** table, letting the target metastore's managed-storage
location own the new files:

```sql
-- Delta managed table on DBFS root → UC managed table (data physically copied)
CREATE TABLE main.sales.orders
DEEP CLONE hive_metastore.sales.orders;

-- Non-Delta managed table → UC managed table via CTAS
CREATE TABLE main.sales.orders AS
SELECT * FROM hive_metastore.sales.orders;
```

No `LOCATION` clause on a UC managed table — the metastore or catalog managed
location decides the path. The per-cloud managed-storage root is whatever
`abfss://` / `s3://` / `gs://` location the metastore (or catalog/schema) was
created with; you do not name it in the DDL.

**Cutover discipline.** Keep the source HMS table read-only for the retention
window, then drop it *after* validating row counts — the deep clone is an
independent copy, so dropping the source frees the DBFS-root files safely.

---

## Blocker 3 — `LEGACY_TABLE_ACL` clusters (DENY-based permission model)

**Why it blocks.** Two things are legacy here. First, the **cluster**: workloads
running on a legacy access mode (`LEGACY_TABLE_ACL`, `LEGACY_SINGLE_USER`,
`LEGACY_PASSTHROUGH`, or No-Isolation `NONE`) cannot talk to UC — UC requires a
UC-compatible access mode (Standard/Shared = `USER_ISOLATION`, or
Dedicated/Single-user = `SINGLE_USER`). Second, the **grants**: HMS Table ACLs
are a permissive model supporting both `GRANT` *and* `DENY`. UC is **allow-only**
— there is no `DENY`. A permission set that relied on a DENY to carve an
exception out of a broad GRANT has no mechanical UC equivalent, so the migration
tooling cannot auto-map it.

**Assessment message** *(representative)*:

```
[UCX migrate-acls] hive_metastore.sales.orders : DENY grant on principal
`contractors` has no Unity Catalog equivalent (UC is grant-only). Manual review
required. Cluster 0921-xxxx uses data_security_mode=LEGACY_TABLE_ACL — not UC
compatible.
```

**Remediation — re-express DENY as absence-of-grant, then move the cluster.** UC
is default-deny, so a HMS DENY becomes "simply never grant it," which usually
means restructuring group membership so the excepted principal does not inherit
the broad grant:

```sql
-- HMS (legacy, DENY-capable) — what you are replacing:
--   GRANT SELECT ON TABLE sales.orders TO `analysts`;
--   DENY  SELECT ON TABLE sales.orders TO `contractors`;   -- no UC equivalent

-- UC (grant-only): grant the allowed group, and keep the denied principal
-- out of any group that inherits the grant.
GRANT SELECT ON TABLE main.sales.orders TO `analysts`;
-- `contractors` receives no grant → effectively denied. If `contractors` was a
-- member of `analysts`, split the group so the exception holds.
```

Then repoint the workload's cluster off the legacy mode:

```
# Cluster spec (all clouds — access mode is cloud-independent)
data_security_mode: USER_ISOLATION   # Standard/Shared, multi-user + UC
# or
data_security_mode: SINGLE_USER      # Dedicated, single principal + UC
```

There is no per-cloud storage variant here — this blocker is about the
permission model and cluster access mode, not storage paths. UCX's group- and
ACL-migration steps port the GRANTs automatically and produce a manual-review
list of exactly the DENYs and legacy-mode clusters above.

---

## Blocker 4 — View-on-view depth and dependency ordering

**Why it blocks.** An HMS view stores its SQL text with two-level names
(`schema.object`) or explicit `hive_metastore.` references. In UC a view must
reference its inputs by **three-level** name (`catalog.schema.object`), and every
object it reads must already exist in UC. A view built on another view therefore
cannot be migrated until its dependency is migrated *and* its stored SQL is
rewritten — so the whole view graph has to be migrated in **topological
(dependency) order**, leaves first. Deeply nested view chains compound the
problem: each level must be resolvable at creation time, and very deep chains can
exceed the query analyzer's nested-view resolution limit *(depth ceiling is
environment-dependent — treat any hard number as representative, not a constant)*,
forcing you to flatten the chain.

**Assessment message** *(representative)*:

```
[UCX migrate-views] hive_metastore.sales.orders_by_region depends on
hive_metastore.sales.orders_enriched which is not yet migrated — deferring.
CREATE VIEW ... failed: table or view not found: hive_metastore.sales.orders_enriched
(rewrite references to three-level Unity Catalog names).
```

**Remediation — migrate leaves first, rewrite to three-level names.** Recreate
the base object(s) in UC, then each dependent view, rewriting every reference
from `hive_metastore.<schema>.<obj>` (or bare `<schema>.<obj>`) to
`<catalog>.<schema>.<obj>`:

```sql
-- 1. Base view first (references UC tables, not hive_metastore.*)
CREATE VIEW main.sales.orders_enriched AS
SELECT o.*, c.region
FROM main.sales.orders o
JOIN main.sales.customers c ON o.cust_id = c.id;

-- 2. Then the dependent view, now that orders_enriched exists in UC
CREATE VIEW main.sales.orders_by_region AS
SELECT region, COUNT(*) AS n
FROM main.sales.orders_enriched
GROUP BY region;
```

Views hold no data, so there is no storage relocation and no per-cloud variant —
the only work is ordering + reference rewriting. UCX's `migrate-views` workflow
builds the dependency graph, walks it leaf-to-root, and rewrites the SQL; it
flags views whose HMS SQL uses a Hive dialect construct that is invalid in UC
Spark SQL for manual porting. Watch for cycles introduced by legacy Hive views —
UC will not create a self- or mutually-referential view.

---

## Blocker 5 — Non-Delta external tables (Parquet / ORC / CSV / JSON)

**Why it blocks.** It usually *doesn't* block outright — it migrates by a
different path. A **Delta** external table on a supported cloud scheme is the
ideal `SYNC` case: UC registers the existing Delta log in place, no copy. A
**non-Delta** external table (Parquet, ORC, CSV, JSON, Avro) has no transaction
log, so the migration strategy forks by format:

- **Parquet / ORC** can be cloned straight to Delta (`DEEP CLONE` reads the files
  and builds a Delta log), or `SYNC`'d as-is to stay in native format.
- **CSV / JSON / Avro** cannot be deep-cloned to Delta (no CLONE source support);
  they migrate via `SYNC` (kept in native format) or CTAS/INSERT into a new table.

**Assessment message** *(representative)*:

```
[UCX] hive_metastore.raw.events : EXTERNAL, format=CSV — eligible for SYNC as a
non-Delta external table (no Delta history to preserve). DEEP CLONE unsupported
for CSV source; use SYNC or CREATE EXTERNAL TABLE + INSERT.
```

**Remediation A — keep native format, register in place (`SYNC`).** Works for any
format on a governed cloud path; no data moves:

```sql
SYNC TABLE main.raw.events FROM hive_metastore.raw.events DRY RUN;
SYNC TABLE main.raw.events FROM hive_metastore.raw.events;
```

**Remediation B — upgrade to Delta.** Parquet/ORC via deep clone; CSV/JSON via an
external write-then-register or CTAS:

```sql
-- Parquet/ORC external → Delta (data copied, Delta log built)
CREATE TABLE main.raw.events
DEEP CLONE parquet.`s3://bucket/legacy/raw/events`;

-- CSV/JSON external → UC external in the same format on a governed path
CREATE EXTERNAL TABLE main.raw.events (event_id STRING, ts TIMESTAMP, payload STRING)
USING CSV OPTIONS (header 'true')
LOCATION 's3://bucket/uc/raw/events';
INSERT INTO main.raw.events SELECT * FROM hive_metastore.raw.events;
```

**Per-cloud variants** (the `LOCATION` / clone-source path):

- **AWS:** `s3://bucket/uc/raw/events`
- **Azure:** `abfss://data@acct.dfs.core.windows.net/uc/raw/events`
- **GCP:** `gs://bucket/uc/raw/events`

Non-Delta tables carry no time-travel history, so nothing is lost by `SYNC` —
the only decision is whether to modernize to Delta now or defer it.

---

## Gotchas

**`CREATE TABLE ... SHALLOW CLONE` does NOT migrate data or Delta history — time
travel breaks post-migration.** A shallow clone copies only the metadata and a
pointer to the source's data files *at the clone instant* — no Parquet is copied,
and the full transaction log is not reproduced. Two ways this bites during a
migration:

1. **Time travel silently loses versions.** The shallow clone knows only the
   version it was cut from. `SELECT ... VERSION AS OF <older>` against the clone
   fails or returns nothing, because those older files were never referenced.
2. **Dropping the source destroys the clone.** The clone still points at the HMS
   source's underlying files. Retire the HMS table (or let `VACUUM` reclaim old
   files) and the shallow clone's data disappears — a data-loss trap precisely
   when you think migration is "done."

Use **`DEEP CLONE`** for any migration where the source will be retired: it
physically copies the current data files and can be re-run incrementally to catch
up new writes before final cutover.

```sql
-- WRONG for migration: no data copied, breaks when hive_metastore.sales.orders is dropped
CREATE TABLE main.sales.orders SHALLOW CLONE hive_metastore.sales.orders;

-- RIGHT: full physical copy, independent of the source
CREATE TABLE main.sales.orders DEEP CLONE hive_metastore.sales.orders;
```

**Even DEEP CLONE resets the version lineage.** The clone starts its own Delta
history at version 0; it does not inherit the source's version numbers. If you
need auditable pre-migration history, keep the source HMS table **read-only** for
your retention window rather than expecting the clone to time-travel into the
source's past.

**`SYNC` is a shared-file registration — do not dual-write.** After `SYNC` the
HMS table and the UC table point at the *same* files, and the source is stamped
`upgraded_to`. Route all writes through UC afterward; writing from both catalogs
(or running `VACUUM` from the HMS side) corrupts the shared location.

**`SYNC` only upgrades EXTERNAL tables.** A managed HMS table returns a
non-success `status_code` (see Blocker 2). Always run `SYNC ... DRY RUN` and read
the `status_code` / `description` per row before the real run — it is the
cheapest way to bucket a whole schema into "SYNC-able" vs "must deep clone."

## Sources

- Databricks — *Upgrade Hive tables and views to Unity Catalog* (migrate guide),
  docs.databricks.com `/data-governance/unity-catalog/migrate`.
- Databricks — *`SYNC` command* reference and *Manage external locations and
  storage credentials* (supported URI schemes), docs.databricks.com.
- Databricks — *Clone a table on Databricks* (deep vs shallow clone semantics,
  time-travel behavior), docs.databricks.com.
- UCX (Databricks Labs UC migration toolkit) — assessment workflow, table
  migration `What` classification, and `migrate-tables` / `migrate-views` /
  `migrate-acls` playbook, github.com/databrickslabs/ucx +
  databrickslabs.github.io/ucx.
- community.databricks.com — HMS-to-UC migration threads on DBFS-root managed
  tables, `wasbs`/`adl` unsupported schemes, and Table-ACL DENY mapping.
