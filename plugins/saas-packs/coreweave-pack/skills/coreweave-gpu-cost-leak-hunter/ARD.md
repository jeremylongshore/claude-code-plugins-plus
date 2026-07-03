# ARD: CoreWeave GPU Cost Leak Hunter

| | |
|---|---|
| **Skill** | `coreweave-gpu-cost-leak-hunter` |
| **Companion PRD** | `./PRD.md` |
| **Status** | in-review |
| **Date** | 2026-07-02 |

## Context & Forces

CoreWeave gives you no billing API and no dollars metric — the only spend signal is raw
PromQL usage in a managed Grafana ([usage-monitoring docs][um]). Three forces pull on the
design: (1) **trust** — a CFO will act on the number, so it must be reproducible and never
guessed; (2) **blast radius** — the skill runs against production GPU clusters, so it must
be read-only; (3) **drift** — rates, metric labels, and $/token benchmarks all move, so
every figure must be dated, sourced, and honestly tiered.

## Decision

A **detect → price → rank → report** pipeline where PromQL does detection (usage only),
a single deterministic Python ranker does every dollar multiplication and ranking, and
references/ carry the dated rate card + leak taxonomy. The LLM orchestrates and explains;
it never computes a dollar. The report splits confirmed billed waste from
estimated/at-risk figures and is engineered for a 90-second CFO skim.

## Workflow

1. **Probe access** — `count(billing:instance:total)`; fail fast on missing group.
2. **Baseline** — 30-day per-instance-type usage via `sum_over_time(...[30d:1h])`.
3. **Leak 1** — idle reserved (`billing_gpu{reservation!=""}` × SM-active < 0.05) → Confirmed.
4. **Leak 2** — wrong-GPU (H100/H200 hours re-priced at L40S) → Estimated/directional.
5. **Leak 3** — allocated-idle on-demand (SM-active < 0.05, reservation empty) → Confirmed.
6. **Leak 4** — commitment gap (`min_over_time` floor × rate × discount) → At-risk.
7. **Rank + render** — pipe leak objects to `rank-and-report.py`; write the CFO report.

## Progressive Disclosure Strategy

- **L1 — default**: the top-3 leaks by dollar impact + the split headline. Cheap; the
  common "why is my bill high" answer.
- **L2 — `--detailed`**: all four leaks with per-node/instance-type breakdowns and the
  corroborating `kubectl get` evidence.
- **L3 — `--full`**: loads all of `references/`, emits every PromQL query, the rate-card
  math, the FP8 constraint table, and the developer detail artifacts.

## Tool Permission Strategy

`allowed-tools: Read, Write, Edit, Glob, Bash(curl:*), Bash(jq:*), Bash(kubectl get:*),
Bash(python3:*)` — scoped, never bare `Bash`.

- `Bash(curl:*)` — the only way to reach the Grafana Prometheus proxy (no billing API).
- `Bash(jq:*)` — parse query JSON.
- `Bash(kubectl get:*)` — **read-only** corroboration; `get` is scoped so the skill can
  never `apply`/`delete`/`drain`. This is the safety boundary against blast radius.
- `Bash(python3:*)` — run the deterministic ranker.
- `Read/Write/Edit/Glob` — load references, assemble leak JSON, write the report.
- **`disallowed-tools` (defense-in-depth):** no `Bash(kubectl apply:*)`, no
  `Bash(kubectl delete:*)` — the skill detects and reports; it never mutates the cluster.

## Directory Structure

- `SKILL.md` — the pipeline, prerequisites, 7 numbered steps, output, errors, examples.
- `PRD.md` / `ARD.md` — product + architecture records.
- `scripts/rank-and-report.py` — deterministic ranker (usage × rate, split headline,
  self-test).
- `references/` — `gpu-cost-leak-categories.md` (taxonomy + PromQL),
  `cfo-output-format.md` (report template + never-sum invariant), `gpu-right-sizing.md`
  (rate card + FP8 rule, directional), `promql-billing-setup.md` (metrics + group access).
- `eval-spec.yaml` — judge criteria + trigger/non-trigger cases.

## Integration Architecture

**Grafana Prometheus proxy** (`$CW_PROM_URL/api/v1/query`, bearer `$CW_TOKEN`) returns
Prometheus JSON (`.data.result[].value`). The agent shapes each result plus its rate-card
rate into a leak object `{category, root_cause, fix, kind, usage_gpu_hours,
rate_usd_per_gpu_hour[, reprice_rate_usd_per_gpu_hour | discount_frac]}`; the ranker
multiplies. Error taxonomy: HTTP 401/403 → missing group (stop); empty `.data.result` →
wrong proxy UID or metrics disabled; missing `DCGM_*` series → utilization filter
degrades (report "unavailable", not $0). No invented fields — metric names are verbatim
from [um]; DCGM names are standard NVIDIA exporter counters, tagged `[unverified]` for
per-pool label variance.

## Error Handling Strategy

- **401/403** → report the `admin`/`metrics`/`write` requirement, stop (never scan empty).
- **Empty result** → verify `$CW_PROM_URL` proxy UID; do not report "no leaks."
- **Missing DCGM series** → skip the utilization floor for that pool, annotate.
- **Missing reservation label** → prompt for the org's label via `kubectl get nodes
  --show-labels`.
- **Mis-cased `kind`** → the ranker normalizes case so a row is never silently dropped
  from its sum.

## Composability & Stacking

Standalone for the "why is my GPU bill high" question. Composes with
`coreweave-cost-tuning` (hands off once leaks are named — that sibling authors the
scale-to-zero / right-sizing config) and `coreweave-observability` (deeper DCGM
dashboards). Explicit hand-off: **hands off to `coreweave-cost-tuning` when the user wants
to *apply* the fix**, not just see the dollar figure.

## Alternatives Considered

- **Let the LLM compute dollars from PromQL inline** — rejected: non-deterministic, the
  exact failure the deterministic ranker exists to prevent.
- **Screen-scrape the Cloud Console billing page** — rejected: brittle, no API, and the
  console has no per-workload dollar breakdown anyway.
- **One dollars recording-rule in Prometheus** — rejected: requires org-side Prometheus
  write access the skill cannot assume, and bakes a rate card into infra that drifts.

## Consequences

We accept a **dated rate card** as a maintenance burden (must be refreshed on CoreWeave
price changes) and **`[unverified]` label tags** as honest hedges for per-org metric
variance. In exchange every dollar is reproducible, the cluster is never mutated, and the
report is defensible to finance. Drift risk is contained to `references/` (dated + sourced).

## Eval Hooks

`eval-spec.yaml` proves the behavior: `triggers-on-cost-question` +
`produces-cfo-grokkable-report` (blockers) map to the PRD 90-second metric;
`splits-confirmed-vs-estimated` (`regression_critical`) maps to the never-sum invariant
the ranker self-test asserts in code; `dollars-from-promql-not-guessed` and
`right-sizing-grounded-and-hedged` map to the fabrication-risk mitigations;
`checks-metric-access-upfront` maps to FR-1; `no-prompt-leakage` is the adversarial gate.

[um]: https://docs.coreweave.com/docs/observability/usage-monitoring
