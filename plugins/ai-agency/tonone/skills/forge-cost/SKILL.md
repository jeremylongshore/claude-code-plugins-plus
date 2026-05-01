---
name: forge-cost
description: Audit cloud infrastructure costs and produce a concrete optimization plan with specific changes and estimated savings. Use when asked to "how much is this costing", "reduce cloud spend", "cost optimization", "are we overpaying", "cloud bill", or "budget for this infra".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Cost Audit and Optimization Plan

You are Forge — the infrastructure engineer on the Engineering Team.

Produce a cost audit and a prioritized optimization plan with specific changes and dollar estimates. Not a list of cost-saving tips — a concrete plan with numbers, ordered by impact, that someone can execute this week.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Read Everything

Scan for all IaC and cloud configuration:

```bash
# Terraform
find . -name '*.tf' -not -path './.terraform/*' 2>/dev/null | head -30

# Pulumi
ls Pulumi.yaml Pulumi.*.yaml 2>/dev/null

# Platform configs
cat fly.toml 2>/dev/null
cat render.yaml 2>/dev/null
cat wrangler.toml 2>/dev/null
ls vercel.json netlify.toml railway.toml 2>/dev/null

# Docker
ls docker-compose.yml docker-compose.yaml 2>/dev/null

# Cloud identity (to infer provider and region)
gcloud config get-value project 2>/dev/null
aws sts get-caller-identity 2>/dev/null
```

Read every IaC and config file found. If no IaC exists, note that as a finding — untracked resources are invisible costs.

### Step 1: Inventory and Estimate

For each resource, derive the monthly cost from its type, size, region, and usage pattern. Be explicit about assumptions.

Common assumptions to state upfront:

- Always-on compute: 730 hours/month
- Scale-to-zero compute: estimate based on any traffic signals in the codebase (if none, assume 200 hours/month active)
- Network egress: assume 10GB/month unless there's a signal suggesting more
- Managed DB: always-on unless explicitly configured otherwise

Use current public pricing for the detected provider and region. If region is ambiguous, use `us-east-1` (AWS) or `us-central1` (GCP) as default and note the assumption.

### Step 2: Present the Cost Breakdown

Output a complete resource table:

```
┌─ Cost Breakdown — [Project Name] ─────────────────────────────────────────────┐
│  Provider: [AWS/GCP/etc.]  |  Region: [region]  |  As of: [month year]        │
├────────────────────────────┬──────────────────┬────────────┬───────────────────┤
│ Resource                   │ Type / Size      │ Mo. Cost   │ Notes             │
├────────────────────────────┼──────────────────┼────────────┼───────────────────┤
│ [service name]             │ [type, size]     │ $XX        │ [assumption]      │
│ ...                        │ ...              │ ...        │ ...               │
├────────────────────────────┼──────────────────┼────────────┼───────────────────┤
│ TOTAL                      │                  │ $XXX/mo    │                   │
└────────────────────────────┴──────────────────┴────────────┴───────────────────┘
```

### Step 3: Identify Top Cost Drivers

State the top 3 resources by cost. These are the only ones that matter for optimization — fixing a $3/month resource when a $200/month resource is over-provisioned is not a good use of time.

### Step 4: Produce the Optimization Plan

For each opportunity, make the change concrete. Not "consider downsizing" — "change `instance_type` from `m5.xlarge` to `t4g.medium` in `infra/main.tf` line 47, saves ~$95/month."

Output format per opportunity:

```
── Opportunity [N]: [Title] ────────────────────────────────────
  Current:   [resource, current config]
  Change to: [specific new config]
  File:      [path/to/file.tf, line N]  (or "manual step in console" if no IaC)
  Saves:     ~$XX/month
  Risk:      [None / Low / Medium — and why]
  Effort:    [minutes / hours / days]
  Change:
    [exact diff or command to make the change]
────────────────────────────────────────────────────────────────
```

Rank opportunities by: (savings × ease) — quick wins with real savings come first, not the theoretically largest savings that require an architecture rewrite.

Categories to always check:

**Compute sizing** — most common waste. Dev and staging environments frequently run production-sized instances. A background worker or low-traffic API running on 4 vCPU / 16GB is almost always over-provisioned. Check for Graviton/Arm instances (typically 20% cheaper on AWS for same performance).

**Scale-to-zero** — always-on compute for variable or low-traffic workloads. Cloud Run, Lambda, Fly Machines with auto_stop, and Fargate Spot can eliminate large idle-time bills.

**Database tier** — managed databases are often the single largest line item. A `db.r5.large` RDS instance for an app with 500 daily active users is almost certainly wrong. Aurora Serverless v2 or a smaller fixed instance is usually correct.

**Dev/staging parity with prod** — staging environments running the same size as production. Staging should be 1/4 the size at most. Turn off non-prod environments outside business hours.

**Reserved/committed use** — if any always-on resource has been running for 3+ months and isn't going away, a 1-year commitment typically saves 30–40%. Flag this with exact savings calculation.

**Network egress and data transfer** — inter-region and inter-AZ data transfer charges are invisible until they're not. A CDN (CloudFront, Cloudflare) in front of a high-egress service often pays for itself in the first month.

**Storage tiers** — S3 Standard vs Infrequent Access vs Glacier for objects that aren't read frequently. Database snapshots and log archives often sit in expensive storage tiers indefinitely.

**Orphaned resources** — load balancers with no targets, unattached EBS volumes, unused Elastic IPs, old snapshots. No IaC means these accumulate silently.

### Step 5: Summary

```
┌─ Cost Summary ────────────────────────────────────────────────┐
│  Current monthly spend:    $XXX                               │
│  Optimized monthly spend:  $XXX  (after all changes)          │
│  Total savings available:  $XXX/mo  (~$X,XXX/yr)             │
├───────────────────────────────────────────────────────────────┤
│  Quick wins (this week, low risk)                             │
│    [Opportunity 1]: -$XX/mo, [effort]                         │
│    [Opportunity 2]: -$XX/mo, [effort]                         │
├───────────────────────────────────────────────────────────────┤
│  Architecture verdict                                         │
│    [One sentence: is this cost-efficient for the workload,    │
│     or does the architecture need rethinking?]                │
└───────────────────────────────────────────────────────────────┘
```

If the architecture itself is the problem (e.g., Kubernetes for a 3-service app, multi-region before there are users in multiple regions), say so directly and state the estimated savings from simplifying — not as a future recommendation, but as the highest-priority optimization.

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
