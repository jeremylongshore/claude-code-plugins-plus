# DLT / Serverless / Photon Cost-Tier Tradeoffs

Loaded on demand when a leak touches DLT pipelines, serverless compute, or the Photon
toggle. This is the encyclopedia the always-loaded SKILL.md deliberately does not
carry — read it only when the customer's situation needs it.

## DLT pipeline edition tiers

Delta Live Tables (Lakeflow Declarative Pipelines) bill a DBU premium on top of the
underlying compute, scaled by **edition**. Read the live edition with
`databricks-workspace-mcp` → `pipelines_get` (`spec.edition`).

| Edition | What it adds | Cost posture |
|---------|--------------|--------------|
| `CORE` | Streaming ingest + transforms | Lowest DLT premium. Use when you do not need CDC or expectations. |
| `PRO` | Adds change-data-capture (`APPLY CHANGES`) | Mid premium. Justified only if the pipeline actually does CDC. |
| `ADVANCED` | Adds data-quality expectations + enforcement | Highest premium. Paying for `ADVANCED` with no `EXPECT` clauses is a silent leak. |

**The DLT edition leak.** A pipeline left on `ADVANCED` that uses no expectations, or
on `PRO` that does no CDC, pays the higher premium for unused capability. The fix is
to drop the edition to the lowest tier the pipeline's features actually require.

## Serverless vs classic compute

Serverless removes cluster management but reprices the DBU. The trap is **background
serverless** — platform features (Predictive Optimization, Lakehouse Monitoring,
materialized-view refresh, Vector Search, Lakeflow Connect) run on serverless
regardless of whether the account opted into serverless for user workloads.

- Serverless user compute: ~$0.07/DBU (bursty, per-second; cheaper for spiky loads).
- Serverless background features: ~$0.70–$0.95/DBU vs ~$0.40–$0.55 classic.
- These appear as surprise `billing_origin_product` line items with no visible
  cause-effect chain between a UI toggle and the charge — untagged, unattributable
  serverless spend with no budget-policy guardrail.

**The serverless-shadow leak.** Background features billing against an account that
never enabled serverless for users. Detect by ranking background
`billing_origin_product` line items by $/month in `system.billing.usage`; the fix is
a budget policy + reviewing whether each background feature is wanted.

## Photon on DLT

Photon on a DLT pipeline is `spec.photon = true` (read via `pipelines_get`, a
config-plane field). The same ~2× DBU premium rule applies: Photon only pays back at
a ≥2× speedup. On classic compute, Photon-billed usage is identified in
`system.billing.usage` by `sku_name ILIKE '%PHOTON%'` (NOT a `runtime_engine` column
— that field exists only on the REST/MCP config plane). The classic-compute Photon
premium math (surface ~half the Photon spend as at-risk) does NOT transfer cleanly to
serverless DLT, which is why the SKILL.md Category-4 query restricts to
`billing_origin_product IN ('ALL_PURPOSE','JOBS_COMPUTE')`.

## Pilot-scope note

Per the v2 CTO decision, the first pilot cut narrowed to the all-purpose-vs-jobs cost
leak, the idle-pool leak, and the DLT-serverless tier leak (with the serverless-shadow
audit optional). The per-query Photon-fallback category — parsing execution-plan JSON
to compute `task_time_in_photon / total_task_time` — was deferred to skill #2 because
plan-JSON parsing across DBR versions is the longest-pole risk. This skill still owns
Photon as the fourth named leak (the billing-premium view via `sku_name`), but
per-query Photon-coverage attribution is the follow-on skill's job.

## Quick decision guide

- Pipeline on `ADVANCED`/`PRO` with no expectations/CDC → drop the edition.
- Background serverless line items on a non-serverless account → budget policy +
  feature review.
- Photon `true` on a pipeline whose ops do not vectorize (UDF-heavy) → disable Photon.
- Bursty interactive query load on classic SQL warehouse → consider serverless SQL.
- Steady 24/7 batch load → classic Jobs compute beats serverless on cost.
