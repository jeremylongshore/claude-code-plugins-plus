# databricks-cost-leak-hunter — CFO sample output

**Status:** Draft for design review (issue [#790](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/790) / [#795](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/795))
**Audience:** CFO / FinOps — the 90-second skim test
**Live demo:** <https://demos.intentsolutions.io/databricks-cost-leak-hunter/>
**Purpose:** Show the *output format* of the pilot skill before code lands. Every rate, multiplier, and waste percentage below is published and cited; the **only** assumed input is one labeled example workspace spend.

---

## Why this doc exists

Iris Wei (cofounder/ex-COO of Toeverything / AFFiNE) gave the bar in the #795 design-review
thread: *"if a CFO can skim it in 90 seconds and say 'we're wasting $X here, fix it' without
needing an engineer to translate, it works."* The AFFiNE README pattern she pointed to is
**one sentence + one proof** — for a CFO, the proof is a dollar number with a date range.

This is deliberately **not** built on the standard one-pager template
(`gist-auditor/references/one-pager-template.md`). That template is a full landing-page +
operator audit — the right instrument for the *developer-facing* skill README, the wrong one
for a 90-second CFO hook. This artifact is the top-of-funnel hook that sits *in front* of the
full one-pager.

**Numbers discipline (this revision):** the first draft used invented totals. This version
replaces them with a cited derivation — the headline is computed from a published cloud-waste
rate applied to one clearly labeled example workspace spend, and every per-row mechanic carries
a footnote to its primary or authoritative source. Anything that could not be confirmed against
a source was discarded.

---

## The sample output

> ### A $100K/month Databricks workspace is likely burning **~$27,000/month**
>
> That's **~$324K/year**. The single assumed input is the $100K/month spend; the 27% waste rate
> is published.¹ Every line below is one config change.

| # | Where it's leaking | $/month | The fix |
|---|---|--:|---|
| 1 | **Clusters that never auto-terminate** — idle compute is one of the largest cloud-waste categories; utilization is chronically low ³ ⁹ | **$12,000** | Set auto-termination (e.g. 30 min) |
| 2 | **Scheduled jobs on All-Purpose Compute** — billed at **$0.55/DBU** vs **$0.15/DBU** for Jobs Compute, **2–3× more** for the same work ⁴ ⁵ ⁶ | **$7,000** | Move job clusters to Jobs Compute |
| 3 | **Clusters sized for peak, idling below threshold** — production is typically **overprovisioned 30–50%** ³ ¹⁰ | **$5,000** | Turn on autoscaling, drop the floor |
| 4 | **Photon billed at ~2× DBU on jobs it doesn't accelerate** — only pays off at a **≥2× speedup** ⁷ ⁶ | **$3,000** | Disable Photon where it adds no runtime gain |

**The #1 line alone — idle clusters — is ~$144K/year, fixed in one setting.**

> **What's assumed vs. what's cited.** The **$100K/month workspace spend is the only assumed
> input** (your number goes here). The **27% waste rate**¹, the **$0.55-vs-$0.15 rate gap and
> 2–3× multiplier**⁴ ⁵, the **~2× Photon premium**⁷, and the **idle-and-overprovisioned-dominate ranking**³ are all
> from published sources. The per-row dollar split is an illustrative allocation of the $27K,
> ranked by documented waste-category size. **When the skill runs, every dollar figure is
> computed from the customer's own `system.billing.usage` table — never estimated.**

For scale: Nucleus Research measured a **375% ROI / 6-month payback** for one Databricks
customer ⁸ — the upside of getting the platform's cost posture right is real and independently
audited.

---

## Sources

1. **Flexera, 2025 State of the Cloud Report** — respondents estimate **27% of cloud spend is
   wasted** (28% in 2022–23; 27% in 2024–25), and **84% say managing cloud spend is the top
   cloud challenge**.
   [Press release](https://www.flexera.com/about-us/press-center/new-flexera-report-finds-84-percent-of-organizations-struggle-to-manage-cloud-spend)
   · [Report PDF](https://resources.flexera.com/web/pdf/Flexera-State-of-the-Cloud-Report-2025.pdf)
2. **CloudZero — Reduce Cloud Waste** — cloud waste runs **~32% of spend (up to one-third)**,
   over $200B globally, corroborating the Flexera figure.
   [cloudzero.com/blog/cloud-waste](https://www.cloudzero.com/blog/cloud-waste/)
3. **CloudZero — Cloud Rightsizing** — overprovisioned and idle resources are the largest waste
   categories: production is typically **overprovisioned 30–50%** (non-production 70%+), and on
   Kubernetes average cluster CPU utilization is ~10% — *"90 cents of every dollar spent on
   Kubernetes compute buys idle capacity."*
   [cloudzero.com/blog/cloud-rightsizing](https://www.cloudzero.com/blog/cloud-rightsizing/)
4. **Flexera, Databricks pricing guide (2026)** — **All-Purpose Compute $0.55/DBU**, **Jobs
   Compute $0.15/DBU** (AWS Premium, US East); *"Using All-Purpose Compute for jobs that belong
   on Jobs Compute can cost 2 to 3 times more for the same workload."*
   [flexera.com/blog/finops/databricks-pricing-guide](https://www.flexera.com/blog/finops/databricks-pricing-guide/)
5. **CloudZero, Databricks pricing guide** — *"All-Purpose Compute clusters … can cost 2–3X more
   per DBU than Jobs Compute clusters used for automated pipelines."*
   [cloudzero.com/blog/databricks-pricing](https://www.cloudzero.com/blog/databricks-pricing/)
6. **Databricks, Best Practices for Cost Management (2022)** — customers *"saved tens of
   thousands of dollars by simply moving just ten percent of their workloads from all-purpose
   clusters to jobs clusters"*; Photon delivers a **3–8× performance** gain; spot instances give
   **up to 90%** off underlying VM compute.
   [databricks.com/blog/best-practices-cost-management-databricks](https://www.databricks.com/blog/best-practices-cost-management-databricks)
7. **Photon ~2× DBU premium on classic compute** — *"Databricks charges approximately 2× DBUs
   for Photon … the breakeven point is roughly a 2× speed improvement,"* so it only saves money
   when it makes the job at least 2× faster.
   [B EYE — Databricks Photon guide](https://b-eye.com/blog/databricks-photon-performance-optimization-guide/)
   · [Databricks Community](https://community.databricks.com/t5/data-engineering/why-is-photon-increasing-dbu-used-per-hour/td-p/41481)
8. **Nucleus Research, "Databricks ROI Case Study: Texas Rangers" (Mar 2024)** — **375% ROI**,
   **6-month payback**, **4× cost-effectiveness** vs the prior cloud data warehouse, **61%**
   data-team productivity gain.
   [nucleusresearch.com](https://nucleusresearch.com/research/single/databricks-roi-case-study-texas-rangers/)
9. **Q. Liu & Z. Yu, "The Elasticity and Plasticity in Semi-Containerized Co-locating Cloud
   Workload: a View from Alibaba Trace," ACM Symposium on Cloud Computing, 2018** — datacenter
   resource utilization is *"very low, which wastes a huge amount of infrastructure investment
   and energy."* (118 citations.)
   [doi.org/10.1145/3267809.3267830](https://doi.org/10.1145/3267809.3267830)
10. **I. Matthew, "Enhancing Cloud Sustainability by Optimizing Cloud Computing Through
    Right-Sizing and Autoscaling," IEEE ACDSA, 2026** — right-sizing plus threshold-based
    autoscaling measurably reduce idle and overprovisioned resource use.
    [doi.org/10.1109/ACDSA67686.2026.11467824](https://doi.org/10.1109/ACDSA67686.2026.11467824)

---

## Design notes

- **"Single config change," not "N clicks."** A CFO forwards this to an engineer; "clicks"
  undersells that these are real workspace changes. Kept the punch, dropped the overpromise.
- **The number leads.** Per Iris: *"if the number is ugly enough, it sells itself; no preamble
  needed."* No problem-statement prose above the fold.
- **One assumption, everything else cited.** The $100K/month spend is the only number we invent;
  it is labeled as such. The waste rate, rate deltas, and category ranking are all sourced, so
  rescaling the workspace preserves the proportions — and a live run replaces the assumption
  with the customer's actual `system.billing.usage` totals.

- Jeremy Longshore
intentsolutions.io
