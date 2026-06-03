# 014-DR-DRFT — Cost-leak output spec for CFO audience (draft for @Gingiris-1031 review)

> Status: **DRAFT** — pending review by Yipei Wei ([#795](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/795) thread).
> If she signs off, this becomes the binding output contract for `databricks-cost-leak-hunter` and code shipping starts. If she doesn't, redesign before code.
>
> Related: [#790](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/790) (skill issue), [`007-AT-ADEC § Decision 2`](007-AT-ADEC-databricks-v2-cto-decision.md) (pilot pick rationale), [`009-RA-REVW`](009-RA-REVW-pilot-timing-pressure-test.md) (pilot timing).

## The bar (Yipei's framing, verbatim)

> "If a CFO can skim it in 90 seconds and say 'we're wasting $X here, fix it' without needing an engineer to translate."

## The structure (Yipei's AFFiNE-derived model)

> "One sentence of what this does + one visual proof it works — for a CFO audience swap the visual for a dollar number with a date range."

For each detected leak category, the output is **one row** following this template:

```
$X,XXX/month wasted on N <unit>, week of <YYYY-MM-DD>, fix in Y <atomic action>.
```

Below that one row, an evidence collapse: itemized list with names + per-item dollar figure + the math. The CFO skims rows. The engineer expands evidence when they go to act.

## What gets cut (cannot appear in CFO output)

- Cluster topology diagrams
- DBU efficiency ratios, utilization percentages
- Spark UI execution plans
- Bytes-shuffled, partition counts, Photon stats
- Any term that requires "what's a DLT pipeline?" context
- Skill version, runtime version, SDK version

Engineers get those via a separate `--engineer` flag. CFO output is the default.

## The four categories — format + worked example

Each category headline is **one sentence**. CFO reads four headlines + one summary. Time-to-comprehension ≤ 90 seconds.

### 1. All-purpose vs job cluster overspend

**Pain source:** [`002-RL-RSRC § D07`](002-RL-RSRC-databricks-compute-pain-research.md) — production batch workloads on interactive clusters at the 2-4x DBU premium.

**Headline format:**
```
$X,XXX/month wasted on N production jobs running on interactive clusters, week of <date>, fix in 3 clicks per job (change cluster type in Jobs UI).
```

**Worked example:**
```
$2,840/month wasted on 7 production jobs running on interactive clusters, week of 2026-05-26, fix in 3 clicks per job (Jobs > [job] > Compute > switch to Job cluster).
```

**Evidence block (expand for engineer use):**

| Job name | Runs/week | Current DBU/run | Job-cluster DBU/run | Monthly waste |
|---|---|---|---|---|
| `bronze-ingest-orders` | 168 | 4.2 (all-purpose) | 1.6 (job) | $1,092 |
| `gold-attribution-rollup` | 42 | 8.4 | 3.0 | $680 |
| `feature-store-refresh` | 168 | 2.1 | 0.8 | $546 |
| `mlflow-experiment-cleanup` | 7 | 12.0 | 4.5 | $315 |
| `cdc-replication-warehouse` | 168 | 1.4 | 0.5 | $151 |
| `ds-notebook-orchestrator` | 30 | 3.5 | 1.3 | $33 |
| `dlt-state-snapshot` | 7 | 6.0 | 2.3 | $23 |

Sum row: $2,840/month total. 7 fixable items.

### 2. Instance pool `min_idle` dual-billing trap

**Pain source:** [`002-RL-RSRC § D09`](002-RL-RSRC-databricks-compute-pain-research.md) — the most-cursed leak in the dataset. Databricks UI shows $0 DBU while the cloud provider bills the underlying VMs 24/7. Invisible until the cloud bill arrives.

**Headline format:**
```
$X,XXX/month wasted on N instance pools billing cloud VMs while showing $0 DBU, week of <date>, fix in 1 click per pool (set min_idle = 0).
```

**Worked example:**
```
$1,920/month wasted on 3 instance pools billing cloud VMs while showing $0 DBU, week of 2026-05-26, fix in 1 click per pool (Compute > Pools > [pool] > Min idle instances = 0).
```

**Evidence block:**

| Pool name | min_idle | Hours idle/week | Cloud VM rate | Monthly waste |
|---|---|---|---|---|
| `prod-i3-2xlarge-pool` | 4 | 168 | $0.624/hr | $1,680 |
| `staging-r5-xlarge-pool` | 2 | 168 | $0.252/hr | $168 |
| `dev-m5-large-pool` | 1 | 132 | $0.096/hr | $51 |

Sum row: $1,899/month total. 3 fixable items. (The $1,920 in the headline rounds up to the nearest $20 for skim-readability — see "rounding rules" below.)

### 3. DLT serverless misuse

**Pain source:** [`003-RL-RSRC § D08, D11`](003-RL-RSRC-databricks-delta-streaming-research.md) — DLT pipelines on serverless when their usage pattern (steady, predictable, multi-hour) fits classic compute at lower cost. The serverless premium is justified for spiky/short workloads — these aren't those.

**Headline format:**
```
$X,XXX/month wasted on N DLT pipelines on serverless that fit classic compute better, week of <date>, fix in 2 clicks per pipeline (toggle serverless off).
```

**Worked example:**
```
$3,400/month wasted on 4 DLT pipelines on serverless that fit classic compute better, week of 2026-05-26, fix in 2 clicks per pipeline (DLT > [pipeline] > Settings > Serverless: off).
```

**Evidence block:**

| Pipeline | Runtime/week | Pattern | Serverless premium | Monthly waste |
|---|---|---|---|---|
| `cdc-ingestion-bronze` | 168h | Steady (24/7) | 1.7x | $1,680 |
| `silver-dedupe-rollup` | 96h | Steady business hours | 1.7x | $1,008 |
| `gold-attribution-streaming` | 80h | Predictable peaks | 1.5x | $560 |
| `feature-store-stream` | 40h | Predictable | 1.5x | $152 |

Sum row: $3,400/month total. 4 fixable items.

**The "fits classic compute better" test:** runtime ≥ 20 hours/week AND coefficient-of-variation in hourly compute load ≤ 0.4 (i.e., not spiky). Pipelines that fail either test stay on serverless and aren't reported.

### 4. Idle SQL warehouse

**Pain source:** [`002-RL-RSRC § D11`](002-RL-RSRC-databricks-compute-pain-research.md) — warehouses left running with auto-stop > 10 min, racking up DBU on idle time.

**Headline format:**
```
$X,XXX/month wasted on N SQL warehouses idle but not auto-stopped, week of <date>, fix in 2 clicks per warehouse (set auto-stop = 10 min).
```

**Worked example:**
```
$960/month wasted on 2 SQL warehouses idle but not auto-stopped, week of 2026-05-26, fix in 2 clicks per warehouse (SQL > Warehouses > [warehouse] > Auto stop = 10 min).
```

**Evidence block:**

| Warehouse | Size | Auto-stop | Idle hours/week | DBU/hour | Monthly waste |
|---|---|---|---|---|---|
| `analytics-large` | Large | 60 min | 42h | $4.20 | $740 |
| `bi-dashboards-small` | Small | None | 28h | $2.10 | $244 |

Sum row: $984/month total. 2 fixable items.

## The summary row (sits at top of output)

**Rollup format:**
```
$X,XXX/month total waste across N fixable items, week of <date>, ~Z min to fix all.
```

**Worked example (using all four sections above):**
```
$9,120/month total waste across 16 fixable items, week of 2026-05-26, ~30 min to fix all.
```

## Rendering order in the actual skill output

```
$9,120/month total waste across 16 fixable items, week of 2026-05-26, ~30 min to fix all.

  $3,400/mo — 4 DLT pipelines on serverless that fit classic compute better
  $2,840/mo — 7 production jobs running on interactive clusters
  $1,920/mo — 3 instance pools billing cloud VMs while showing $0 DBU
  $  960/mo — 2 SQL warehouses idle but not auto-stopped

Expand any line above for the per-item evidence + the click path to fix.
```

Headline at top (the conversion moment). Four rows sorted highest waste → lowest (the CFO reads top-down and stops where the dollars stop being interesting). Single literal instruction at the bottom (the engineer trigger).

## Rounding rules

- Sum rows: round to **nearest $20** for skim-readability.
- Per-item evidence: report exact (no rounding) — engineer trusts it precisely.
- The headline number is always the rounded sum; the evidence-block sum is exact. Footnote IF the two differ by more than $40 (rare; happens only when many items round same direction).

## Date range semantics

- "Week of \<date>" = the 7-day window ending the last completed calendar week (Sunday).
- Data source: `system.billing.usage` rows for that window.
- We never extrapolate. We never project. We report observed waste in the window — extrapolated to monthly via `× 4.33`.
- Multi-week consistency: if the same leak appears 3+ weeks running, the next iteration of this skill (out of scope for v1) starts surfacing trend annotations. v1 ships the single-week view only.

## What we are NOT shipping in v1

- Trend / longitudinal analysis (≥3 week pattern detection)
- Comparison-to-peer or industry-benchmark numbers
- Predicted-savings simulation (changes are reported as observed waste, not projected)
- Multi-workspace rollup (single workspace per invocation; teams with N workspaces run N times)
- Cost attribution to teams / projects / cost-centers (Databricks tags exist; using them is its own design problem)

If any of these matter to the CFO test, surface in the review and we cut differently.

## Questions back at Yipei

1. **Headline word count.** Each headline is ~16-22 words. AFFiNE's "one sentence" — does a 22-word sentence still pass the skim test, or does it need to be shorter? Sample shortest version of #2 above: *"$1,920/month wasted on 3 idle instance pools, week of 2026-05-26, 1 click each to fix"* — 18 words. Worth it, or does losing "dual-billing trap" lose the WHY a CFO needs?

2. **Rounding readability.** Is rounding to $20 the right granularity for skim, or does $100 work better? My instinct said $20; user-testing might prefer $100 for round-number cognitive load.

3. **Click count semantics.** "fix in 3 clicks" is literal-clicks-in-the-Databricks-UI. Should that be navigation-clicks only, or include the confirm-dialog click? My count includes the confirm because it's part of the fix; some readers might expect "3 navigation steps + a confirm."

4. **Sort order.** Currently sorted highest waste → lowest. Alternative: sort by "easiest to fix first" (the `min_idle = 0` single-click row would lead, even though it's not the biggest dollar number). Adoption thesis: do CFOs want biggest-impact-first, or do they want fastest-quick-wins-first to build momentum?

5. **Anything missing from the four categories.** These four came out of the pain research ([`002`](002-RL-RSRC-databricks-compute-pain-research.md), [`003`](003-RL-RSRC-databricks-delta-streaming-research.md)) being most-cursed AND most-detectable from `system.billing.usage` + control-plane reads. Other categories exist (DBU-per-query tuning, Photon-without-vectorized-operators, etc.) but require deeper sampling. If you've seen a fifth category that beats one of these on the 90-second test, swap recommendation welcome.

## Sign-off block

When this draft passes your review, mark below:

- [ ] @Gingiris-1031 — headline format + structure approved
- [ ] @Gingiris-1031 — four categories cover the right surface
- [ ] @Gingiris-1031 — open questions answered (or accepted as-is)
- [ ] Jeremy — code work greenlit, bead `claude-0co4` closes, skill build proceeds against this spec

If you redline anywhere above, send the redline however works (here on the issue, on `claude-0co4`, voice memo). Spec becomes the binding output contract once all four boxes check.

---

**File status:** draft — superseded only by a successor `014-AT-ADEC-cost-leak-output-contract.md` once approved.
**Author:** Jeremy Longshore (Intent Solutions)
**Reviewer:** Iris Wei ([@Gingiris-1031](https://github.com/Gingiris-1031))
**Created:** 2026-06-03
