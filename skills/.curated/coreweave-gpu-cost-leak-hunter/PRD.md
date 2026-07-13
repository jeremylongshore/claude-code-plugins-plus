# PRD: CoreWeave GPU Cost Leak Hunter

| | |
|---|---|
| **Skill** | `coreweave-gpu-cost-leak-hunter` |
| **Pack** | `coreweave-pack` |
| **Version** | 0.1.0 (pre-ship) |
| **Author** | Jeremy Longshore |
| **License** | MIT |
| **Status** | in-review |
| **Date** | 2026-07-02 |
| **Pain catalog refs** | CW-C1 idle reserved, CW-C2 wrong-GPU, CW-C3 allocated-idle, CW-C4 commitment-gap |

## Summary

Finds where CoreWeave GPU money is leaking and how much, per month, and emits a
CFO-grokkable dollar-ranked report. CoreWeave ships no cost dashboard and no billing
API, so the spend view is reconstructed from PromQL usage against its managed Grafana ×
a rate card. Kills the pain of "our GPU bill is huge and there is no dashboard to tell
us why."

## Problem Statement

CoreWeave exposes **no billing API and no dollars metric** — cost visibility is a
build-it-yourself PromQL exercise ([usage-monitoring docs][um]). Teams therefore fly
blind on four recurring leaks: (CW-C1) reserved capacity billed take-or-pay while idle;
(CW-C2) small-model inference on H100/H200 that an L40S serves cheaper per token;
(CW-C3) on-demand GPUs allocated but sitting at <5% SM-active; (CW-C4) a steady
on-demand baseline that a commitment would discount up to 60% ([pricing][pr]). On
$100K–$1M/month GPU spend, each leak is five to six figures a year. Today nobody can
name the dollar figure without a bespoke Grafana build.

## Target Users (personas)

- **Priya — FinOps / platform lead.** Owns the CoreWeave bill; not a Kubernetes expert.
  Current workaround: exports invoices to a spreadsheet, cannot tie spend to workloads.
  Trigger moment: *"I open this skill when finance asks why the GPU line doubled."*
- **Marco — engineer who owns the CoreWeave cluster.** Fluent in kubectl and PromQL,
  time-poor. Current workaround: eyeballs DCGM dashboards, never dollarizes them.
  Trigger moment: *"I open this skill when I suspect we left reserved GPUs idle."*

## User Stories

- **US-1 (Must)** — As Priya, I get a dollar-ranked leak report I can act on in 90
  seconds so that I can answer finance without an engineer. → CW-C1..C4
- **US-2 (Must)** — As Priya, confirmed billed waste is never summed with estimates so
  that I don't over-promise recoverable cash. → all
- **US-3 (Must)** — As Marco, every dollar traces to a PromQL query × a dated rate card
  so that I trust the number and can reproduce it. → all
- **US-4 (Should)** — As Marco, the skill fails fast if I lack the metrics group rather
  than reporting empty as "no leaks." → CW access
- **US-5 (Should)** — As Marco, the L40S-vs-H100 recommendation is hedged as directional
  so that I benchmark before re-hosting. → CW-C2

## Functional Requirements

- **FR-1** — Probe `billing:instance:total` via the Grafana `/api/v1/query` proxy and,
  on 401/403/empty, report the required `admin`/`metrics`/`write` group and stop.
  (Surface: `Bash(curl:*)` → Grafana Prometheus API) → US-4 → `checks-metric-access-upfront`
- **FR-2** — Compute a 30-day per-instance-type usage baseline via
  `sum_over_time(billing:instance:total[30d:1h])`. → US-1 → `dollars-from-promql-not-guessed`
- **FR-3** — Detect CW-C1 (idle reserved): `billing_gpu{reservation!=""}` crossed with
  `DCGM_FI_PROF_SM_ACTIVE < 0.05`; tag **Confirmed**. → US-1 → `splits-confirmed-vs-estimated`
- **FR-4** — Detect CW-C2 (wrong-GPU): H100/H200 instance-hours re-priced at the L40S
  rate; tag **Estimated**, hedge as directional. → US-5 → `right-sizing-grounded-and-hedged`
- **FR-5** — Detect CW-C3 (allocated-idle): on-demand `billing_gpu{reservation=""}` with
  SM-active < 0.05; tag **Confirmed**. → US-1 → `splits-confirmed-vs-estimated`
- **FR-6** — Detect CW-C4 (commitment gap): `min_over_time(... {reservation=""}...)`
  floor × on-demand rate × discount; tag **At-risk**. → US-1 → `splits-confirmed-vs-estimated`
- **FR-7** — `scripts/rank-and-report.py` multiplies usage × rate deterministically,
  ranks by monthly dollars, and never sums confirmed + unconfirmed under one verb.
  → US-2/US-3 → `splits-confirmed-vs-estimated`, `produces-cfo-grokkable-report`

## Surfaces & Integrations

- **Grafana Prometheus proxy** — `GET $CW_PROM_URL/api/v1/query?query=<PromQL>` (bearer
  `$CW_TOKEN`). Base URL shape `https://grafana.<org>.coreweave.com/api/datasources/proxy/uid/<uid>`
  `[UNVERIFIED — exact proxy path varies per org; confirm in Grafana Explore]`.
- **Metrics** — `billing:instance:total`, `billing_gpu`, `sunk:job_gpus_allocated:total`
  (verbatim from [um]); `DCGM_FI_PROF_SM_ACTIVE`, `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`,
  `DCGM_FI_DEV_GPU_UTIL` (standard NVIDIA DCGM exporter) `[UNVERIFIED — labels vary per pool]`.
- **`reservation` label** on `billing_gpu` `[UNVERIFIED — key varies per org; confirm via kubectl]`.
- **kubectl** — `kubectl get nodes --show-labels`, `kubectl get pods -A --field-selector=status.phase=Running`.
- **Rate card** — dated snapshot of [coreweave.com/pricing][pr] in `references/gpu-right-sizing.md`.
- **Ranker** — `scripts/rank-and-report.py` (stdlib only).

## Non-Goals

- **Does not author cost-control config** (scale-to-zero rules, instance recommendations)
  — that is the sibling `coreweave-cost-tuning`.
- **Does not modify the cluster** — read-only detection + a report; no `kubectl apply`.
- **Does not invoice-reconcile** — it estimates from usage × rate; actual billed amounts
  vary by contract/discount/tax ([um]).

## Success Metrics

- Given the four PromQL result sets, the skill produces a ranked report whose confirmed
  headline equals ONLY the sum of Confirmed rows (asserted by the ranker self-test).
- A CFO can act on the report in ~90 seconds (`produces-cfo-grokkable-report` judge).
- On missing metric access, the skill reports the group requirement upfront
  (`checks-metric-access-upfront` judge).
- The L40S recommendation is hedged as directional (`right-sizing-grounded-and-hedged`).

## Constraints & Assumptions

- Auth from env (`$CW_PROM_URL`, `$CW_TOKEN`, `$KUBECONFIG`); no hardcoded secrets.
- Requires `admin`/`metrics`/`write` group membership ([um]).
- Rate card is a dated snapshot — the only human-supplied number besides monthly spend.
- DCGM exporter present on the node pools (else utilization filters degrade gracefully).

## Risk Assessment

- **R-1 — Rate-card / pricing drift** (likely / medium): rates change. Mitigation: the
  rate card is dated + sourced in `references/`, supplied to the ranker not hardcoded in
  the LLM; the skill flags figures directional.
- **R-2 — Metric/label drift** (likely / medium): `reservation` label + DCGM labels vary
  per org. Mitigation: `[UNVERIFIED]` tags + a `kubectl get nodes --show-labels` step.
- **R-3 — Over-committing on CW-C4** (possible / high): a commitment sized to peak
  re-creates idle reserved (CW-C1). Mitigation: size to the `min_over_time` floor; the
  leak is tagged At-risk, never Confirmed.
- **R-4 — $/token fabrication** (possible / high): a hard L40S-beats-H100 claim would be
  false precision. Mitigation: tagged Estimated + directional; eval criterion enforces it.

## Traceability

| US | FR | Pain | Eval criterion |
|---|---|---|---|
| US-1 | FR-2,3,5,6,7 | CW-C1..C4 | produces-cfo-grokkable-report |
| US-2 | FR-7 | all | splits-confirmed-vs-estimated |
| US-3 | FR-2..7 | all | dollars-from-promql-not-guessed |
| US-4 | FR-1 | CW access | checks-metric-access-upfront |
| US-5 | FR-4 | CW-C2 | right-sizing-grounded-and-hedged |

[um]: https://docs.coreweave.com/docs/observability/usage-monitoring
[pr]: https://www.coreweave.com/pricing
