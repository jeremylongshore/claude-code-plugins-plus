# PromQL Billing Setup — Metrics + Group Access

_Last updated: 2026-07-02. Sourced from [CoreWeave usage-monitoring docs][um] and
[CoreWeave pricing][pr]._

CoreWeave ships **no cost dashboard and no billing API**. The only way to see spend is to
query usage metrics from CoreWeave's managed Grafana in PromQL and multiply by the rate
card yourself ([um]). This is the access + metric reference the skill probes in Step 1.

## Why this is the most common failure

Grafana's Prometheus data source is reachable **only to a member of the `admin`,
`metrics`, or `write` group** in the CoreWeave Cloud Console ([um]). A user with console
access but none of those groups gets an empty result or a 401/403 on `/api/v1/query` —
which looks like "no leaks" rather than "no access." Detecting it upfront and naming the
exact group requirement is the difference between a clean "ask your admin to add you to
`metrics`" and a confusing empty report.

## Access checklist

1. You are logged into the CoreWeave Cloud Console.
2. Your principal is in `admin`, `metrics`, **or** `write` ([um]).
3. `$CW_PROM_URL` points at the Grafana Prometheus data-source proxy, e.g.
   `https://grafana.<org>.coreweave.com/api/datasources/proxy/uid/<uid>`.
4. `$CW_TOKEN` is a bearer token for that Grafana.
5. `$KUBECONFIG` is the CoreWeave-issued cluster config (for `kubectl get` corroboration).

## The Step 1 probe

```bash
curl -sS -H "Authorization: Bearer $CW_TOKEN" \
  --data-urlencode 'query=count(billing:instance:total)' \
  "$CW_PROM_URL/api/v1/query" | jq -r '.status, (.data.result | length)'
```

`status: success` with a non-zero result length → access is good. Anything else → report
the group requirement and stop; do not run the leak scans on empty data.

## The billing metrics (verbatim from the docs)

| Metric | What it measures |
|---|---|
| `billing:instance:total` | Running instances, by `instance_type` — the base of every spend figure |
| `billing_gpu` | GPU allocation (filter by the reservation label for reserved vs on-demand) |
| `billing:object_storage_used_bytes:total` | Object-storage volume |
| `billing_resource_usage_storage` | Provisioned storage volumes |
| `billing_ip_address` | Public IP addresses |
| `sunk:job_gpus_allocated:total` | SUNK-scheduled job GPU allocation |

Utilization counters come from the DCGM exporter CoreWeave scrapes out of the box —
`DCGM_FI_PROF_SM_ACTIVE` (SM-active fraction, the truest "GPU working" signal),
`DCGM_FI_DEV_GPU_UTIL` (coarse 0–100 utilization), `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`
(tensor-core activity), `DCGM_FI_DEV_FB_USED` (framebuffer/VRAM used). Standard NVIDIA
DCGM names; `[unverified — exporter labels and availability vary per node pool, confirm
in Grafana Explore]`.

## There is no dollars metric

The docs are explicit: to estimate cost you multiply usage counts by hourly rates and sum
— e.g. the month-to-date example multiplies H200 instance counts by `* 50.44` (the 8-GPU
node rate) ([um]). The docs also warn: _"This provides an estimate based on standard
On-Demand rates and your real-time usage metrics. Actual billed amounts can vary based on
contracts, discounts, taxes, and billing cycle specifics."_

That is exactly why this skill:

1. Pulls **usage** from PromQL (deterministic, from your own Grafana).
2. Multiplies by a **dated rate card** ([gpu-right-sizing.md](gpu-right-sizing.md)) in the
   ranker, never in the LLM.
3. Labels confirmed billed idle waste separately from modeled/at-risk figures.

## The 30-day usage idiom

```promql
# resource-hours over 30 days (hourly samples summed)
sum by (instance_type) (sum_over_time(billing:instance:total[30d:1h]))

# mean level over 30 days (for utilization floors)
avg by (node) (avg_over_time(DCGM_FI_PROF_SM_ACTIVE[30d:1h]))

# always-on floor (for the commitment-gap leak)
min_over_time(sum by (instance_type) (billing:instance:total{reservation=""})[30d:1h])
```

[um]: https://docs.coreweave.com/docs/observability/usage-monitoring
[pr]: https://www.coreweave.com/pricing
