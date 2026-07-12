# Photon Eligibility and the Silent Fallback to Spark

Photon is enabled per cluster and billed on cluster uptime at a premium DBU rate, but
it only accelerates the operators it actually supports. When a query hits something
Photon cannot execute — most often a Python or Scala UDF — that operator (sometimes the
whole query) falls back to the JVM Spark engine. The fallback is silent: no exception,
no warning, no log line the user sees. The job succeeds, runs at roughly plain-Spark
speed, and still bills every minute at the Photon premium.

This reference owns the **per-query plane** — reading the execution plan to prove
whether Photon carried the work. The billing-side view (identifying Photon-billed
compute by `sku_name ILIKE '%PHOTON%'`, no `runtime_engine` column on
`system.compute.clusters`) lives in the cost-leak-hunter pack:
`../../databricks-cost-leak-hunter/references/cost-leak-categories.md` (Category 4) and
its `dlt-tier-cost-tradeoffs.md`. Use this doc when the Photon line item went up but the
runtime barely moved — the classic fingerprint of paying the premium for work Spark did.

## What Photon is and how it is billed

- Photon is Databricks' native, vectorized query engine — a C++ reimplementation of
  Spark's execution operators that runs columnar, SIMD-vectorized work in place of the
  JVM. It is a drop-in accelerator for the Spark SQL / DataFrame path; it changes
  neither your code nor your results.
- Photon is a **cluster/runtime-level toggle, not a per-query one**. Enable it and every
  workload on that compute attempts to run in Photon. There is no query-level "use
  Photon here, plain Spark there" switch.
- Billing is on **cluster uptime at a higher DBU rate** — commonly cited as up to ~2x
  the non-Photon DBU consumption for the same instance. Verify the exact multiplier
  against the customer's `system.billing.list_prices`; it varies by SKU, cloud, and
  tier. The premium is applied to the DBUs the cluster accrues *while running*,
  independent of how much of any given query Photon actually executed.
- The consequence is the whole trap: Photon coverage is a **per-operator** property, but
  the bill is a **per-uptime** charge. A query that is 100% Python UDF gets 0% Photon
  acceleration and still bills at the full Photon DBU rate for its entire runtime. The
  premium only pays back when the real speedup on *your* workload beats the DBU
  multiplier (≥~2x). Field reports routinely show ~4x cost for ~1.8x runtime — a net
  loss that no dashboard flags for you.
- Detect that a cluster is Photon-billed from the SKU (`sku_name ILIKE '%PHOTON%'` on
  the priced usage row) or the config plane (`runtime_engine = PHOTON` via `clusters_get`;
  `spec.photon = true` on a DLT pipeline). The cost dashboard shows the Photon spend but
  never *why* it was wasted — that answer is in the plan.

## What drops a query (or operator) off Photon back to Spark

Photon supports a growing but incomplete subset of Spark's operators, expressions, and
types. When the physical plan contains something Photon has not implemented, that
operator runs on Spark and a columnar↔row transition is inserted at the seam. The
unsupported surface, most-common first:

- **User-defined functions — the dominant cause.**
  - Python UDFs (`@udf`) execute in a separate Python worker via a `BatchEvalPython`
    operator — a Spark node, never Photon.
  - Scala/Java UDFs evaluate as JVM Spark `Project` expressions — not Photon.
  - pandas / Arrow "vectorized" UDFs execute via `ArrowEvalPython` — still a Spark
    operator, so still not a Photon node. Whether Photon retains any surrounding
    vectorization benefit is DBR-version-dependent *(verify)*.
- **RDD API operations.** Photon accelerates only the DataFrame/SQL (Catalyst) path.
  Any drop to the RDD API (`.rdd`, `mapPartitions`, custom partitioners) runs on Spark.
- **Unsupported expressions / built-in functions.** A minority of SQL functions are not
  yet in Photon (certain regex, some higher-order/collection functions, some cast and
  decimal edge cases). An unsupported expression falls back at the operator that
  evaluates it. The supported-function set grows every DBR release, so treat any specific
  "not supported" claim as version-scoped *(verify)*.
- **Unsupported or unusual data types.** Photon covers the common types (numeric,
  decimal, string, boolean, date, timestamp, and nested array/map/struct on recent
  DBRs). Exotic or older-unsupported types (e.g. `INTERVAL`, very wide decimals, some
  nested-type operations) can force fallback *(verify against the DBR in use)*.
- **Structured Streaming.** Photon covers a subset — largely stateless streaming on
  recent DBRs. Stateful or complex streaming operators commonly fall back to Spark
  *(verify — streaming coverage has expanded materially across versions)*.
- **Miscellaneous.** Some write paths, some join/sort variants on older DBRs, and
  constructs Catalyst lowers to nodes Photon has not implemented. When in doubt, the plan
  is authoritative (next section).

Fallback is either whole-query (the entire plan runs on Spark) or partial (Photon runs
the scan/filter/agg, hands the one unsupported operator to Spark, then resumes). Partial
fallback is the more expensive trap: the cluster still looks "Photon-enabled," but every
columnar↔row transition adds CPU overhead *and* the bill is still the Photon rate.

## Detecting fallback

The billing tables tell you a cluster is Photon-billed; only the query plan tells you
whether Photon actually ran the work. Ground truth is the fraction of task time spent in
Photon — `task_time_in_photon / total_task_time`. Signals, cheapest to most
authoritative:

- **Triage with `system.query.history`.** Rank the candidate queries on Photon-billed
  compute, then inspect the top offenders' plans. Query-history is DBSQL-warehouse-scoped
  and carries no direct Photon-coverage column, so it is the triage layer, not the proof.

```sql
SELECT
  statement_id,
  LEFT(statement_text, 120) AS stmt,
  execution_duration_ms,
  total_task_duration_ms,
  spilled_local_bytes,
  read_bytes
FROM system.query.history
WHERE start_time >= current_date() - INTERVAL 7 DAYS
  AND execution_status = 'FINISHED'
  AND statement_type = 'SELECT'
ORDER BY total_task_duration_ms DESC
LIMIT 25;
```

- **Read the physical plan** with `EXPLAIN FORMATTED <query>` (or `df.explain("formatted")`).
  Photon operators are prefixed `Photon` (`PhotonScan`, `PhotonProject`,
  `PhotonGroupingAgg`, `PhotonShuffleExchangeSink`/`Source`, `PhotonBroadcastHashJoin`).
  Plain Spark operators (`Project`, `HashAggregate`, `BatchEvalPython`, `ArrowEvalPython`)
  are the fallback zones. DBR also emits a diagnostic naming the reason — commonly
  rendered as a "Photon does not fully support the query because:" note listing the
  unsupported node (exact wording varies by DBR — *verify*):

```text
== Physical Plan ==
Photon does not fully support the query because:
    Unsupported node: BatchEvalPython (Python UDF).

*(2) Project [pythonUDF0#41 AS score#55]
+- BatchEvalPython [score_udf(amount#12)], [pythonUDF0#41]
   +- ColumnarToRow
      +- PhotonResultStage
         +- PhotonProject [amount#12]
            +- PhotonScan parquet main.sales.orders [amount#12] ...
```

- **Look for transition nodes at the Photon↔Spark seam** — `ColumnarToRow` /
  `RowToColumnar` (and the `PhotonAdapter` boundary node). One transition at the top of a
  Photon plan is normal; many transitions scattered through the plan mean the query is
  ping-ponging between engines (partial fallback), and the transitions themselves burn
  CPU that you are billing at the Photon rate.
- **Spark UI → SQL / DataFrame tab → open the query → the DAG.** Photon operators are
  labeled and styled distinctly; any standard Spark node in the middle of the graph marks
  where Photon dropped out. The DBSQL Query Profile surfaces the same graph plus a "Task
  time in Photon" metric *(verify exact label)* — a low value against total task time is
  the quantified fallback.
- **Driver logs (log4j).** Photon records its unsupported-operation reasons for the same
  query — useful when you cannot capture `EXPLAIN` interactively.

The `BatchEvalPython` / `ArrowEvalPython` / Scala-UDF `Project` node is the single
highest-signal fingerprint: find it in the plan and you have found the operator that
pulled the query off Photon while the cluster kept billing the premium.

## The decision — is the premium worth it, and how to restore coverage

Photon earns its premium when the workload is CPU-bound, vectorizable Spark SQL /
DataFrame work: large scans, filters, joins, aggregations, and Delta writes over
supported types — analytical queries and native-expression ETL. There it commonly clears
the ≥2x bar and the premium pays back.

Photon is **not** worth it when:

- The job is UDF-heavy (Python/Scala UDFs dominate the plan) — the hot operators run on
  Spark regardless, so you pay the premium for near-zero acceleration.
- The job is RDD-based, or dominated by shuffle / network / I/O wait rather than CPU —
  Photon accelerates compute, not the wire.
- The workload is stateful streaming or otherwise sits mostly outside Photon's supported
  surface on the DBR in use.

Two levers, in order of preference:

1. **Restore Photon coverage by removing the fallback.** Rewrite the UDF as a native SQL
   expression or built-in so Photon executes it:
   - String/parse UDFs → `regexp_extract`, `regexp_replace`, `substr`, `split`, `translate`.
   - Arithmetic/conditional UDFs → plain column expressions plus `CASE WHEN` / `coalesce` / `nullif`.
   - Array/map UDFs → higher-order functions `transform`, `filter`, `aggregate`, `exists`.
   - Lookups → a broadcast `JOIN` against a reference table instead of a UDF closure.

   Re-run `EXPLAIN` after the rewrite: the `BatchEvalPython` node should be gone and the
   operator should now read `Photon...`. If a UDF is genuinely unavoidable, isolate it so
   the rest of the plan still Photonizes — compute it in a separate, narrow stage and keep
   the expensive scans/joins on Photon.

2. **If the workload cannot be made Photon-eligible, turn Photon off** for that
   job/cluster and drop back to the standard (cheaper) DBU rate. A job running at Spark
   speed should pay the Spark price.

Decision math: because Photon roughly doubles the DBU rate, it only pays back at a ≥~2x
wall-clock speedup on your workload. Measure it directly — run a representative job once
with Photon on and once off, compare `execution_duration_ms` (and cost = DBUs × rate),
and keep Photon only where the runtime win beats the premium. Do not assume; the fallback
is silent precisely because nothing warns you when the assumption fails.

## Sources

- Databricks — "What is Photon?" and Photon-enabled compute limitations (unsupported
  UDFs, RDD APIs, expressions, data types, streaming coverage). The coverage surface is
  DBR-version-scoped; verify against the runtime in use.
- Databricks — Photon pricing / DBU-multiplier guidance (the Photon-enabled DBU rate is
  applied on cluster uptime). Confirm the exact multiplier in the customer's
  `system.billing.list_prices`.
- Databricks — reading query plans (`EXPLAIN FORMATTED`, the Spark UI SQL / DataFrame
  DAG) and the DBSQL Query Profile "Task time in Photon" metric.
- Databricks system tables — `system.query.history` schema (DBSQL-warehouse-scoped, no
  direct Photon-coverage column) for triage, and `system.billing.usage` /
  `list_prices` for the SKU-based Photon-billing view.
- Companion references in this pack:
  `../../databricks-cost-leak-hunter/references/cost-leak-categories.md` (Category 4 —
  Photon billed where it does not accelerate) and the same skill's
  `dlt-tier-cost-tradeoffs.md` (Photon on DLT and the `task_time_in_photon / total_task_time`
  coverage metric).
