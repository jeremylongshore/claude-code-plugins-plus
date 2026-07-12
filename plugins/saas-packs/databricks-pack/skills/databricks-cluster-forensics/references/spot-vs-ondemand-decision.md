# Spot vs On-Demand — the cluster configuration decision tree

Spot (AWS) / spot (Azure) / preemptible (GCP) instances are the single largest compute
discount Databricks exposes — routinely **60–90% off** the on-demand VM price. The catch
is that the cloud can **reclaim** a spot node at any moment with a ~2-minute warning
(often less), because you are renting spare capacity the provider can take back the
instant a full-price customer wants it. For a stateless map-only job that reclamation is
a shrug: the lost tasks just re-run on surviving nodes. For a **shuffle-heavy** job it can
be a full-job abort, and the failure mode is subtle enough that teams turn spot on for the
discount, eat an intermittent production abort weeks later, and never connect the two.

This reference is the decision tree for **which nodes go spot, which stay on-demand, and
per job class how aggressive the spot ratio should be**. The load-bearing rule underneath
all of it: the **driver is never spot**, and the more shuffle a job does, the more of its
worker floor should stay on-demand too.

## Why spot saves money and where it bites

The reclaim model is asymmetric. You save on every spot-node-hour you actually keep, but
you pay a **recompute tax** every time a node is reclaimed mid-flight, and that tax is not
linear in shuffle-heavy stages — it can cascade to a full abort.

Here is the cascade, precisely:

1. A wide transformation (`join`, `groupBy`, `repartition`, `distinct`) writes **shuffle
   map output** to the **local disk of each worker**. That data lives only on the node
   that produced it — it is not replicated.
2. A spot worker is reclaimed. Every shuffle block it held is gone.
3. Reduce-side tasks that try to fetch those blocks throw `FetchFailedException`. Spark's
   lineage handles this: it marks the parent **map stage** for re-submission and
   **recomputes only the lost partitions** on surviving nodes. So far, so resilient — one
   reclaim is survivable.
4. The bite: if **another** spot node is reclaimed *during that recompute*, you get a
   second `FetchFailedException` and a second consecutive stage attempt. Consecutive
   failures accumulate against **`spark.stage.maxConsecutiveAttempts` (default 4)**. Cross
   that ceiling and the stage — and the whole job — aborts with
   `Job aborted due to stage failure: ... failed the maximum allowable number of times: 4`.

So the danger is not a single reclaim; Spark absorbs that. The danger is **serial reclaims
inside one stage's recompute window**, which is exactly what happens when a large fraction
of a long-running, wide-shuffle cluster is spot and the provider pulls capacity in waves.
Short jobs rarely see it (the window is small); long shuffle-bound jobs see it precisely
when spot markets tighten.

## The load-bearing mitigation: driver-on-demand-always

**The driver must never be a spot instance.** The driver holds the `SparkContext`, the
DAG scheduler, the block-manager master, and (for streaming) the checkpoint coordinator.
Lose a worker and Spark recomputes; lose the **driver** and the entire cluster dies —
every executor is orphaned, the job fails hard, and there is no lineage recovery because
the thing that *owns* the lineage is gone. A spot driver turns a routine capacity reclaim
into a guaranteed total loss. There is no discount that justifies it.

On AWS, the field that enforces this is **`aws_attributes.first_on_demand`**. Nodes are
allocated **driver-first**, so the first node in the count is always the driver:

- `first_on_demand: 1` → driver on-demand, **all** workers spot.
- `first_on_demand: N` → driver **plus the first N-1 workers** on-demand, the rest spot.

Pair it with **`availability: SPOT_WITH_FALLBACK`** so that if spot capacity cannot be
acquired (or an acquired node is reclaimed and no spot replacement exists), Databricks
provisions an **on-demand** node instead of leaving the cluster under-sized. The Databricks
UI's "Spot instances" checkbox sets `first_on_demand: 1` for exactly this reason — it is
the floor, not an aggressive setting.

A shuffle-heavy production cluster: pin the driver **and the autoscale floor** to
on-demand, and let only the burst capacity above the floor be spot. With
`min_workers: 4`, set `first_on_demand: 5` (driver + 4 floor workers). The steady-state
minimum cluster is then fully on-demand — a reclaim wave can only shrink the *burst*
nodes, never the floor holding the bulk of shuffle output:

```json
{
  "cluster_name": "etl-heavy-shuffle-prod",
  "spark_version": "15.4.x-scala2.12",
  "node_type_id": "i3.2xlarge",
  "driver_node_type_id": "i3.2xlarge",
  "autoscale": {
    "min_workers": 4,
    "max_workers": 20
  },
  "aws_attributes": {
    "availability": "SPOT_WITH_FALLBACK",
    "first_on_demand": 5,
    "spot_bid_price_percent": 100,
    "zone_id": "auto"
  },
  "spark_conf": {
    "spark.stage.maxConsecutiveAttempts": "10",
    "spark.decommission.enabled": "true",
    "spark.storage.decommission.enabled": "true",
    "spark.storage.decommission.shuffleBlocks.enabled": "true"
  },
  "autotermination_minutes": 30
}
```

**Azure** uses `azure_attributes` with the same `first_on_demand` semantics; availability
is `SPOT_WITH_FALLBACK_AZURE`, and the bid cap is `spot_bid_max_price` (set to `-1` to cap
at the on-demand price, so you are only ever evicted for **capacity**, never for price):

```json
"azure_attributes": {
  "availability": "SPOT_WITH_FALLBACK_AZURE",
  "first_on_demand": 1,
  "spot_bid_max_price": -1
}
```

**GCP** differs: there is **no `first_on_demand`** field, and the **driver is always
placed on an on-demand instance** by the platform — you cannot make the GCP driver
preemptible even if you wanted to. Workers go preemptible via `availability`, with fallback
to on-demand:

```json
"gcp_attributes": {
  "availability": "PREEMPTIBLE_WITH_FALLBACK_GCP"
}
```

## Decision tree

Choose the row matching the job, then apply the config. The governing variables are
**shuffle weight** (how badly a reclaim cascades) and **cost-of-failure** (what a missed
run costs versus the discount).

| Job class | Driver | Worker availability | Spot ratio | Rationale |
| --- | --- | --- | --- | --- |
| Interactive / notebook | on-demand | `SPOT_WITH_FALLBACK` | high (`first_on_demand: 1`) | Exploratory, short-lived tasks; a reclaim just re-runs a cell. Take the full discount. |
| Short batch (< ~30 min, light shuffle) | on-demand | `SPOT_WITH_FALLBACK` | high (`first_on_demand: 1`) | Recompute window is tiny; even a full re-run is cheap. Aggressive spot is safe. |
| Long batch, heavy shuffle | on-demand | `SPOT_WITH_FALLBACK` | **moderate** (`first_on_demand` = min_workers + 1) | The cascade zone. Keep the floor on-demand so serial reclaims cannot starve the stage. |
| Structured Streaming | on-demand | `SPOT_WITH_FALLBACK` or all on-demand | low / none | Stateful, checkpoint-driven, latency-SLA'd. Reclaims force micro-batch restarts + state reload. |
| SLA-critical prod | on-demand | **all on-demand** | none | Cost-of-miss (regulatory / downstream-blocking) dwarfs the compute discount. |

Reasoning per class:

- **Interactive / notebook** — Developers tolerate a re-attach; the workload is bursty and
  short. Maximum spot (`first_on_demand: 1`) is the right default; auto-termination matters
  more here than spot ratio.
- **Short batch** — With little shuffle and a sub-30-minute runtime, the probability of two
  reclaims landing inside one stage's recompute is negligible. Full spot workers with
  fallback; do not over-engineer.
- **Long batch, heavy shuffle** — This is the only class where spot genuinely bites. Pin
  the driver **and** the autoscale floor on-demand (`first_on_demand` = `min_workers` + 1),
  cap spot at the burst tier, and turn on graceful decommissioning (below). If the job is
  both long *and* mission-adjacent, bias further toward on-demand — the discount on the
  burst nodes is real, the abort risk on the floor is not worth it.
- **Structured Streaming** — The driver owns checkpoint continuity, so it is on-demand
  without exception. Worker reclaims drop in-flight micro-batches and force stateful
  operators to reload state from the checkpoint, adding latency and (for tight SLAs)
  breaching it. Cost-tolerant streams can run a small spot fraction with fallback; latency-
  sensitive ones run all on-demand workers.
- **SLA-critical prod** — Financial close, regulatory filings, jobs that gate downstream
  pipelines. When a missed deadline costs more than a day of on-demand compute, the spot
  discount is a false economy. Go all on-demand, or keep a full on-demand floor with only
  trivial spot burst headroom.

## Tuning knobs

- **`first_on_demand`** (AWS / Azure) — the primary lever. It is a **count**, not a
  ratio: it fixes the driver plus the first N-1 workers on-demand and makes everything
  above spot. Set it to your on-demand floor. It does not adapt as the cluster autoscales,
  so size it against `min_workers`, not `max_workers`.
- **`availability` = `SPOT_WITH_FALLBACK`** — always prefer the fallback variant over bare
  `SPOT`. Bare `SPOT` leaves the cluster under-provisioned when capacity is unavailable;
  the fallback variant substitutes on-demand so the job keeps its parallelism. The small
  price is that during a spot drought you quietly pay on-demand rates — which is the
  correct trade for a job you want to *finish*.
- **`spot_bid_price_percent`** (AWS, default `100`) — the max bid as a percent of the
  on-demand price. **Leave it at 100.** Bidding at 100% does **not** mean you pay
  on-demand — you pay the (usually far lower) spot market price and are only reclaimed for
  **capacity**, never outbid on **price**. Lowering it below 100 saves nothing on the
  bill (you already pay market) and adds a second, price-driven reclaim trigger on top of
  the capacity one — strictly more interruptions for no gain. On Azure the equivalent is
  `spot_bid_max_price: -1` (cap at on-demand price).
- **`spark.stage.maxConsecutiveAttempts`** (default `4`) — the ceiling the reclaim cascade
  hits. Raising it (e.g. to `8`–`10`) buys tolerance for serial shuffle-fetch failures so
  a couple of back-to-back reclaims do not abort a long job. It is a **supplement, not a
  substitute** for an on-demand floor: raising it too high masks genuinely failing stages
  and burns compute retrying a doomed job. Pair a modest bump with the floor, do not lean
  on it alone.
- **Graceful decommissioning** (`spark.decommission.enabled`,
  `spark.storage.decommission.enabled`,
  `spark.storage.decommission.shuffleBlocks.enabled`) — when the cloud sends the ~2-minute
  spot-interruption notice, Spark tries to **migrate shuffle (and cached RDD) blocks off
  the doomed node** to survivors before it dies, so a reclaim need not trigger a
  `FetchFailedException` at all. It is **best-effort inside a short window** — large
  shuffle spills may not finish migrating — so it lowers the cascade probability rather
  than eliminating it. Enable it on every spot-bearing shuffle-heavy cluster; still keep
  the on-demand floor.

The through-line: spot is a **capacity gamble scoped to the worker burst tier**. Keep the
driver and the shuffle-holding floor on-demand, let graceful decommissioning and a modestly
raised attempt ceiling soak up the occasional reclaim, and reserve aggressive full-spot
ratios for short or stateless jobs where a re-run is cheap.

## Sources

- Databricks compute configuration — spot instances, `first_on_demand`, availability, bid price (AWS) — https://docs.databricks.com/aws/en/compute/configure
- Databricks Clusters API — `aws_attributes` / `azure_attributes` / `gcp_attributes` reference — https://docs.databricks.com/api/workspace/clusters/create
- Databricks compute configuration (Azure) — `spot_bid_max_price`, `SPOT_WITH_FALLBACK_AZURE` — https://learn.microsoft.com/en-us/azure/databricks/compute/configure
- Apache Spark configuration — `spark.stage.maxConsecutiveAttempts` and shuffle-fetch retry behavior — https://spark.apache.org/docs/latest/configuration.html
- Apache Spark — node decommissioning / shuffle-block migration (`spark.decommission.enabled`, `spark.storage.decommission.*`, SPARK-20624) — https://spark.apache.org/docs/latest/configuration.html
- AWS EC2 Spot Instances — interruption model and ~2-minute reclaim notice — https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html
