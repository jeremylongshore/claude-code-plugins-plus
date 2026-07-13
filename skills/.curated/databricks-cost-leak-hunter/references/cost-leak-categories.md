# The Four Cost-Leak Categories

Each category below carries a plain-English definition, the FinOps root cause (why
the money leaks, in dollar terms, not Spark jargon), the real `system.billing.usage`
detection SQL, and the single-config-change remediation. All four detection queries
reuse one price-window join — the `priced` CTE — defined once below.

Confidence tiers (carried into the CFO report's `Confidence` column):

- **Confirmed** (Categories 1, 2): money actually billed, or a deterministic
  re-pricing delta. Recoverable.
- **Estimated** (Category 3): a modeled figure (`spend × (1 − CPU%)`), not a billed
  amount.
- **At-risk** (Category 4): a premium pending review against actual runtime gain.

## The dollar primitive — the `priced` CTE (reused by every query)

The dollar of any usage row is `usage_quantity * list_prices.pricing.default`, joined
on `sku_name` AND `usage_unit` within the price-effective window, restricted to
`currency_code = 'USD'`. `pricing` is a STRUCT (`.default` is its USD-per-unit
field); `usage_metadata` is a STRUCT carrying `cluster_id` / `job_id` /
`warehouse_id` / `instance_pool_id`. Joining on `sku_name` alone over-counts — a
single SKU can be priced in different units, so `usage_unit` in the join is
load-bearing.

```sql
WITH priced AS (
  SELECT
    u.usage_date,
    u.sku_name,
    u.usage_quantity,
    u.usage_unit,
    u.billing_origin_product,
    u.usage_metadata,
    u.custom_tags,
    u.usage_quantity * lp.pricing.default AS usd
  FROM system.billing.usage u
  JOIN system.billing.list_prices lp
    ON  u.sku_name   = lp.sku_name
    AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND u.usage_end_time <  COALESCE(lp.price_end_time, TIMESTAMP '9999-12-31')
  WHERE u.usage_date >= current_date() - INTERVAL 30 DAYS
    AND lp.currency_code = 'USD'
)
```

---

## Category 1 — Clusters that never auto-terminate (idle compute) · Confirmed

**Definition.** Interactive clusters left running with `auto_termination_minutes = 0`
keep billing DBUs around the clock even when no one is attached.

**FinOps root cause.** Idle compute is one of the largest cloud-waste categories;
utilization on always-on interactive clusters is chronically low. Every idle hour
bills at the full All-Purpose DBU rate for zero work delivered.

**Detection SQL.** `system.compute.clusters` is change-history (SCD), so take the
*latest* config row per cluster (not `MAX()` over the window, which would mask a
cluster that was 0 then fixed).

```sql
WITH priced AS ( /* …the CTE above… */ ),
cluster_cfg AS (
  SELECT cluster_id, cluster_name, auto_termination_minutes,
         worker_count, min_autoscale_workers, max_autoscale_workers
  FROM (
    SELECT cluster_id, cluster_name, auto_termination_minutes,
           worker_count, min_autoscale_workers, max_autoscale_workers,
           ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS rn
    FROM system.compute.clusters
    WHERE change_time >= current_date() - INTERVAL 30 DAYS
  )
  WHERE rn = 1
)
SELECT
  p.usage_metadata.cluster_id         AS cluster_id,
  COALESCE(c.cluster_name, 'unknown') AS cluster_name,
  c.auto_termination_minutes,
  ROUND(SUM(p.usd), 2)                AS spend_30d_usd,
  ROUND(SUM(p.usage_quantity), 2)     AS dbus_30d
FROM priced p
JOIN cluster_cfg c ON p.usage_metadata.cluster_id = c.cluster_id
WHERE p.billing_origin_product = 'ALL_PURPOSE'
  AND c.auto_termination_minutes = 0
GROUP BY p.usage_metadata.cluster_id, c.cluster_name, c.auto_termination_minutes
HAVING SUM(p.usd) > 0
ORDER BY spend_30d_usd DESC;
```

**Corroborate.** `databricks-workspace-mcp` → `clusters_get` (live REST
`autotermination_minutes`), `clusters_events` (idle gap between RUNNING and
TERMINATING).

**Remediation (single config change).** Set auto-termination (e.g. 30 min) on the
flagged clusters.

---

## Category 2 — Scheduled jobs on All-Purpose Compute · Confirmed

**Definition.** Pipelines prototyped in interactive notebooks get shipped to prod by
scheduling them on the same all-purpose cluster instead of a Jobs cluster.

**FinOps root cause.** All-Purpose compute bills at ~$0.55/DBU vs ~$0.15/DBU for Jobs
Compute — 2–3× more for the same batch work. The premium pays for shared multi-user
notebook UX a scheduled batch job never uses. The single highest-ROI optimization in
most deployments.

**Detection SQL.** A row with a `job_id` in `usage_metadata` AND
`billing_origin_product = 'ALL_PURPOSE'`. Re-price the same DBUs at the current Jobs
rate to model the savings. **The `jobs_rate` CTE must yield exactly one rate per
`usage_unit`** — `%JOBS_COMPUTE%` matches multiple SKUs (per-cloud, per-tier,
serverless vs classic, Photon-jobs), all sharing `usage_unit='DBU'`; joining on
`usage_unit` against an un-deduped set fans out the join and inflates the math
non-deterministically. Restrict to `currency_code='USD'` and `GROUP BY usage_unit`
with `MIN(pricing.default)` to guarantee one deterministic rate per unit.

```sql
WITH priced AS ( /* …the CTE above… */ ),
jobs_rate AS (
  SELECT usage_unit, MIN(pricing.default) AS jobs_unit_price
  FROM system.billing.list_prices
  WHERE sku_name ILIKE '%JOBS_COMPUTE%'
    AND price_end_time IS NULL
    AND currency_code = 'USD'
  GROUP BY usage_unit
)
SELECT
  p.usage_metadata.job_id AS job_id,
  ROUND(SUM(p.usd), 2)    AS spend_on_all_purpose_30d_usd,
  ROUND(SUM(p.usage_quantity * jr.jobs_unit_price), 2)
                          AS would_cost_on_jobs_30d_usd,
  ROUND(SUM(p.usd) - SUM(p.usage_quantity * jr.jobs_unit_price), 2)
                          AS potential_savings_30d_usd
FROM priced p
JOIN jobs_rate jr ON p.usage_unit = jr.usage_unit
WHERE p.billing_origin_product = 'ALL_PURPOSE'
  AND p.usage_metadata.job_id IS NOT NULL
GROUP BY p.usage_metadata.job_id
HAVING SUM(p.usd) - SUM(p.usage_quantity * jr.jobs_unit_price) > 0
ORDER BY potential_savings_30d_usd DESC;
```

**Corroborate.** `clusters_list` / `clusters_get` (`cluster_source`) — confirm the
live compute type before recommending the move. Note: `job_id` present +
`billing_origin_product = 'ALL_PURPOSE'` is already the billing-accurate signal; the
REST check is belt-and-suspenders, not required for the dollar math.

**Remediation (single config change).** Move the job's cluster to Jobs Compute.

---

## Category 3 — Overprovisioned clusters idling below floor · Estimated

**Definition.** Clusters sized for peak load run with most workers idle most of the
time; production is typically overprovisioned 30–50%. The idle-pool variant is an
instance pool with `min_idle_instances > 0` keeping warm VMs the cloud bills directly.

**FinOps root cause.** You pay for provisioned capacity, not used capacity. A cluster
averaging < 25% CPU is burning ~75% of its spend on idle headroom. For pools, the
Databricks dashboard reads $0 while the cloud provider bills the idle VMs — an
invisible spend leak hidden by the dual-billing split.

**This figure is a modeled estimate, not billed waste** — `spend × (1 − CPU%)` is an
upper-bound heuristic. The column is honestly named `est_overprovision_30d_usd` and
the CFO report tags it `Estimated`.

**Detection SQL.** `system.compute.node_timeline` gives per-node-minute CPU;
aggregate mean utilization per cluster, join to spend, flag chronic low utilization.

```sql
WITH priced AS ( /* …the CTE above… */ ),
util AS (
  SELECT cluster_id,
         AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu_pct,
         COUNT(*)                                    AS node_minutes
  FROM system.compute.node_timeline
  WHERE start_time >= current_date() - INTERVAL 30 DAYS
  GROUP BY cluster_id
),
spend AS (
  SELECT usage_metadata.cluster_id AS cluster_id, SUM(usd) AS spend_30d_usd
  FROM priced
  WHERE billing_origin_product IN ('ALL_PURPOSE','JOBS_COMPUTE')
    AND usage_metadata.cluster_id IS NOT NULL
  GROUP BY usage_metadata.cluster_id
)
SELECT
  s.cluster_id,
  ROUND(u.avg_cpu_pct, 1)   AS avg_cpu_pct,
  ROUND(s.spend_30d_usd, 2) AS spend_30d_usd,
  ROUND(s.spend_30d_usd * (1 - LEAST(u.avg_cpu_pct,100)/100.0), 2)
                            AS est_overprovision_30d_usd
FROM spend s
JOIN util u ON s.cluster_id = u.cluster_id
WHERE u.avg_cpu_pct < 25 AND s.spend_30d_usd > 0
ORDER BY est_overprovision_30d_usd DESC;
```

**Corroborate.** `clusters_get` (REST nested `autoscale.min_workers` /
`autoscale.max_workers`); `instance_pools_list` (`min_idle_instances`,
`stats.idle_count`) for the idle-pool variant. Pool idle waste =
`min_idle × instance_hourly_rate × 730 hrs/month`.

**Remediation (single config change).** Turn on autoscaling and drop the floor
(REST `autoscale.min_workers` / pool `min_idle_instances`).

---

## Category 4 — Photon billed where it does not accelerate · At-risk

**Definition.** Photon enabled to "speed things up," but the workload (UDFs, Pandas
UDFs, RDD APIs) silently falls back to JVM Spark — the cluster still bills the Photon
premium.

**FinOps root cause.** Photon is a per-cluster (not per-query) billing toggle at a
~2× DBU multiplier. Every minute the cluster is up bills at the Photon rate
regardless of how much actually executed in the Photon engine. It only pays back at
a ≥2× speedup; real reports show ~4× cost for ~1.8× runtime gain.

**Detect Photon via the SKU, not a cluster column.** `system.compute.clusters` has NO
`runtime_engine` / Photon column. Photon-billed usage is identified by
`sku_name ILIKE '%PHOTON%'` on the priced usage row — the billing-accurate source.
The `~2× premium → half of spend` split is an at-risk approximation, not a derived
base-vs-Photon comparison, hence the `at-risk` tag.

```sql
WITH priced AS ( /* …the CTE above… */ )
SELECT
  p.usage_metadata.cluster_id AS cluster_id,
  ROUND(SUM(p.usd), 2)        AS photon_spend_30d_usd,
  ROUND(SUM(p.usd) / 2.0, 2)  AS photon_premium_at_risk_30d_usd
FROM priced p
WHERE p.sku_name ILIKE '%PHOTON%'
  AND p.billing_origin_product IN ('ALL_PURPOSE','JOBS_COMPUTE')
  AND p.usage_metadata.cluster_id IS NOT NULL
GROUP BY p.usage_metadata.cluster_id
HAVING SUM(p.usd) > 0
ORDER BY photon_premium_at_risk_30d_usd DESC;
```

**Corroborate.** `databricks-workspace-mcp` `clusters_get` (REST `runtime_engine` —
a config-plane field, NOT a system-table column); `pipelines_get` (`spec.photon` /
`serverless` / `edition`) for DLT. See `dlt-tier-cost-tradeoffs.md`.

**Remediation (single config change).** Disable Photon where it adds no runtime gain.

---

## Column-name notes (verify per workspace)

- `system.compute.clusters`: change-history (SCD) config with
  `auto_termination_minutes`, `worker_count`, `min_autoscale_workers`,
  `max_autoscale_workers`, `cluster_name`, `cluster_source`, `change_time`. There is
  **no** `runtime_engine` / Photon column on this table — Photon is detected via
  `sku_name`. Name columns explicitly, never `SELECT *`.
- `system.compute.node_timeline`: CPU columns `cpu_user_percent`,
  `cpu_system_percent`, `cpu_wait_percent`.
- `billing_origin_product` enum: `ALL_PURPOSE`, `JOBS_COMPUTE`, `SQL`, `DLT`,
  `MODEL_SERVING`, and others.
- REST/MCP-only fields (NOT system-table columns): `runtime_engine`,
  `autotermination_minutes`, nested `autoscale.min_workers` /
  `autoscale.max_workers`. Use these strictly via `clusters_get` corroboration.

## Reference DBU rate card (illustrative; use the customer's `list_prices`)

- Jobs Compute ~$0.15/DBU
- SQL Compute ~$0.22/DBU
- All-Purpose Compute ~$0.40–$0.55/DBU
- Serverless ~$0.07/DBU (user) / ~$0.70–$0.95/DBU (background features)
