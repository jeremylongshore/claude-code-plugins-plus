# System Tables Setup — the Metastore-Admin Grant Chain

Billing system tables are Unity-Catalog-governed. Access requires a grant chain that
only a **metastore admin** can issue. The skill probes access in Step 1 and, if the
probe fails, reports the exact missing grant here — it never fails mid-analysis.

## Why this is the most common failure

`system.billing.usage` lives in the read-only `system` catalog. A principal with full
workspace-admin rights can still be blocked because system-schema access is granted
separately at the metastore level. The error surfaces as `PERMISSION_DENIED` on the
first `SELECT`. Detecting it upfront — and naming the precise grant a metastore admin
must run — is the difference between a clean "ask your admin for X" and a confusing
mid-flow crash.

## The grant chain (run by a metastore admin)

Replace `<principal>` with the running user, service principal, or group. Each link
is required; granting `SELECT` on the table without `USE CATALOG` / `USE SCHEMA`
still denies access.

```sql
-- 1. Catalog-level access to the system catalog
GRANT USE CATALOG ON CATALOG system TO `<principal>`;

-- 2. Schema-level access to the billing schema
GRANT USE SCHEMA ON SCHEMA system.billing TO `<principal>`;

-- 3. Read on the two billing tables the dollar math needs
GRANT SELECT ON TABLE system.billing.usage       TO `<principal>`;
GRANT SELECT ON TABLE system.billing.list_prices TO `<principal>`;

-- 4. Compute schema (config + utilization corroboration)
GRANT USE SCHEMA ON SCHEMA system.compute              TO `<principal>`;
GRANT SELECT    ON TABLE  system.compute.clusters      TO `<principal>`;
GRANT SELECT    ON TABLE  system.compute.node_timeline TO `<principal>`;
```

## Enabling the system schemas (if not yet enabled)

System schemas may not be enabled on the metastore at all. A metastore admin enables
them via the Account API. List status first:

```bash
databricks api get "/api/2.0/unity-catalog/metastores/<metastore_id>/systemschemas"
```

Then enable the billing and compute schemas:

```bash
databricks api put \
  "/api/2.0/unity-catalog/metastores/<metastore_id>/systemschemas/billing"
databricks api put \
  "/api/2.0/unity-catalog/metastores/<metastore_id>/systemschemas/compute"
```

## Verifying access (what Step 1 runs)

A single-row probe per table, executed through the CLI Statement Execution API
(requires `DATABRICKS_WAREHOUSE_ID`). If every probe returns a row, the grant chain
is complete.

```sql
SELECT 1 FROM system.billing.usage           LIMIT 1;
SELECT 1 FROM system.billing.list_prices     LIMIT 1;
SELECT 1 FROM system.compute.clusters        LIMIT 1;
SELECT 1 FROM system.compute.node_timeline   LIMIT 1;
```

Equivalent grant audit (who can already read the table):

```sql
SHOW GRANTS ON TABLE system.billing.usage;
```

## What to report when the probe fails

When Step 1's probe does not return `SUCCEEDED`, surface this to the user verbatim and
STOP — do not run the leak scans:

- Which probe failed (catalog, schema, or table level).
- The exact grant statement a metastore admin must run (from the chain above).
- That the grant is a **metastore-admin** action — workspace admin alone is not
  enough.

## Two data planes, two independent auth surfaces

- **Databricks CLI Statement Execution API** (`/api/2.0/sql/statements`) — reads
  `system.*` for every dollar figure. Auth is the CLI's `DATABRICKS_HOST` +
  `DATABRICKS_TOKEN` (or `databricks auth login`); Unity Catalog enforces the grant
  chain above on each read. Requires `DATABRICKS_WAREHOUSE_ID`.
- **`databricks-workspace-mcp`** — reads control-plane config/events (clusters,
  pools, pipelines). Its own auth tree (PAT / U2M / M2M); PAT is unsupported in
  Databricks-App deployment mode. It needs no system-table grants — it reads the live
  REST API, not `system.*`.

If the workspace MCP is not registered, the skill degrades: it still reports dollar
figures from the CLI but cannot corroborate live config; it then accepts pasted
config/spend numbers for the corroboration step.
