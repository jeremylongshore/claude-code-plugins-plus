# The Four GPU Cost-Leak Categories

_Last updated: 2026-07-02. Sourced from [CoreWeave usage-monitoring docs][um] and
[CoreWeave pricing][pr]._

Each category carries a plain-English definition, the FinOps root cause (why the money
leaks, in dollar terms), the PromQL detection query, and the single change that fixes
it. CoreWeave exposes **no dollars metric** — every query returns _usage_, and the
ranker (`scripts/rank-and-report.py`) multiplies usage × the rate card
([gpu-right-sizing.md](gpu-right-sizing.md)) deterministically.

Confidence tiers (carried into the CFO report's `Confidence` column):

- **Confirmed** (Categories 1, 3): GPU-hours actually billed for zero useful work.
  Recoverable.
- **Estimated** (Category 2): a right-sizing model — the rate delta is exact, but
  throughput equivalence on the cheaper GPU is modeled.
- **At-risk** (Category 4): a commitment decision — the up-to-60% saving is pending, and
  a commitment is itself a paid obligation.

## Metric primitives (all from CoreWeave managed Grafana)

- `billing:instance:total` — count of running instances, by `instance_type`. The base
  of every spend figure. [[um]]
- `billing_gpu` — GPU allocation; filter by the reservation label to split reserved vs
  on-demand. The `reservation` label key is **provider-specific — confirm yours** with
  `kubectl get nodes --show-labels`. `[unverified — label key varies per org]`
- `DCGM_FI_PROF_SM_ACTIVE` — fraction of time the streaming multiprocessors were active
  (0–1); the truest "is the GPU actually working" signal. `DCGM_FI_DEV_GPU_UTIL` (0–100)
  is a coarser fallback. Standard NVIDIA DCGM-exporter counters, scraped by CoreWeave out
  of the box. `[unverified — exporter labels vary per node pool]`
- `sunk:job_gpus_allocated:total` — SUNK-scheduled job GPU allocation, for training
  clusters. [[um]]

A 30-day usage window uses a subquery: `sum_over_time(<metric>[30d:1h])` ≈ resource-hours
(hourly samples summed). `avg_over_time(<metric>[30d:1h])` gives the mean level.

---

## Category 1 — Idle reserved capacity · Confirmed

**Definition.** Reserved (committed) GPUs left running below a utilization floor.
Reserved capacity is billed **whether used or not**, so an idle reserved GPU is pure
confirmed waste.

**FinOps root cause.** A committed reservation trades an up-to-60% discount for a
take-or-pay obligation ([pr]). Below break-even utilization the discount is a loss:
you pre-paid for GPU-hours that delivered nothing, and unlike on-demand you cannot
scale them to zero to stop the bill. `[unverified — the pricing page directs reserved
terms to sales; the take-or-pay behavior is standard committed-spend economics, not a
figure quoted by CoreWeave.]`

**Detection PromQL.** Reserved GPUs whose SM-active sat below 5% over the window:

```promql
sum by (instance_type,node) (avg_over_time(billing_gpu{reservation!=""}[30d:1h]))
  and on(node)
(avg by (node) (avg_over_time(DCGM_FI_PROF_SM_ACTIVE[30d:1h])) < 0.05)
```

**Corroborate.** `kubectl get nodes -l <reservation-label> -o wide` to confirm the node
is a reserved one; `kubectl get pods -A --field-selector=status.phase=Running` to prove
nothing is scheduled.

**Remediation (single change).** Right-size the reservation to observed steady demand,
or release it at renewal.

---

## Category 2 — Wrong-GPU-type (right-sizing waste) · Estimated

**Definition.** H100/H200 running small-model (~7B–30B) inference where an L40S serves
the same tokens for less. Top-tier Hopper silicon is training-grade; for mid-size
inference it is often over-bought.

**FinOps root cause.** Cost-per-token, not cost-per-hour, is what matters for inference.
In the 7B–30B regime L40S is frequently cheaper per token than H100/H200 (directional —
figures swing by model, batch size, quantization, and month; see
[gpu-right-sizing.md](gpu-right-sizing.md)). The rate delta itself is exact rate-card
math (H100 ≈ $6.16/GPU-hr vs L40S ≈ $2.25/GPU-hr, derived from the 8-GPU node prices in
[pr]); the _throughput equivalence_ is the modeled part, hence **Estimated**.

**Detection PromQL.** Hopper-class instance-hours that are candidates for re-hosting:

```promql
sum by (instance_type) (
  sum_over_time(billing:instance:total{instance_type=~".*(h100|h200).*"}[30d:1h])
)
```

**Corroborate.** Confirm the served model size with the cluster owner; check tensor-core
activity (`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`) — chronically low tensor utilization on a
Hopper node is a strong "this workload does not need H100" signal. FP8 serving needs
Hopper/Ada, not Ampere — do not re-host an FP8 workload onto A100.

**Remediation (single change).** Move the small-model inference deployment to L40S.

---

## Category 3 — Allocated-but-idle instances · Confirmed

**Definition.** On-demand GPUs that are allocated (billing) but running at low
SM-utilization / low MFU — the GPU twin of an idle cluster. They bill the full on-demand
rate for no work.

**FinOps root cause.** You pay for allocated capacity, not used capacity. An on-demand
GPU averaging < 5% SM-active is burning ~95% of its spend on idle headroom — and unlike
a reservation, it can be scaled to zero the moment it goes idle, so every idle hour is
avoidable confirmed waste.

**Detection PromQL.** On-demand nodes below the SM-active floor that were still
allocated:

```promql
(avg by (node,instance_type) (avg_over_time(DCGM_FI_PROF_SM_ACTIVE[30d:1h])) < 0.05)
  and on(node)
(sum by (node) (avg_over_time(billing_gpu{reservation=""}[30d:1h])) > 0)
```

**Corroborate.** `kubectl get pods -A --field-selector=status.phase=Running -o wide`
filtered to the flagged node — confirm no GPU pod is actually scheduled.

**Remediation (single change).** Enable scale-to-zero (KServe / Knative
`autoscaling.knative.dev/minScale: "0"`) or deschedule the idle deployment.

---

## Category 4 — On-demand spend that should be committed · At-risk

**Definition.** A stable on-demand floor — GPUs of one type always running across the
window — paying on-demand for capacity a commitment would discount up to 60% ([pr]).
The inverse over-reservation case (a committed reservation you don't use) is Category 1.

**FinOps root cause.** On-demand is the right price for spiky/experimental load and the
wrong price for a 24/7 baseline. Any GPU count that never drops to zero over 30 days is
baseline you are renting at rack rate.

**Detection PromQL.** The always-on on-demand floor (min instance count over the window):

```promql
min_over_time(sum by (instance_type) (billing:instance:total{reservation=""})[30d:1h])
```

**Corroborate.** Plot the same series over 30 days in Grafana — a floor that never
touches zero confirms a committable baseline. Size the commitment to the floor, **not**
the peak, or you re-create Category 1 (idle reserved capacity).

**Remediation (single change).** Commit the stable floor (contact CoreWeave sales for
committed-use terms); leave the spiky remainder on-demand.

**At-risk caveat.** The up-to-60% figure is a ceiling, not a guarantee, and a commitment
is a paid take-or-pay obligation — over-commit and the saving inverts into Category 1.
That two-way risk is why this leak is tagged At-risk, never Confirmed.

[um]: https://docs.coreweave.com/docs/observability/usage-monitoring
[pr]: https://www.coreweave.com/pricing
