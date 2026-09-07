---
name: fondo-cost-tuning
description: 'Optimize Fondo costs by maximizing R&D tax credits, choosing the right
  plan,

  and reducing unnecessary bookkeeping complexity.

  Trigger: "fondo costs", "fondo pricing", "maximize R&D credit", "fondo ROI".

  '
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Cost Tuning

## Overview

Maximize Fondo ROI: the R&D tax credit alone should exceed the annual Fondo cost for most startups.

## Prerequisites

- Current contract/billing information reviewed by the finance owner and an approved decision process.
- Aggregate usage data only; individual employee, payroll, tax, and account data stays in authorized systems.

## Instructions

1. Measure cost and workflow value using current data and document assumptions for review.
2. Consider operational simplification only when it preserves compliance, retention, reconciliation, and professional-review requirements.
3. Obtain finance approval before changing plan, scope, integrations, or tax workflow.

## Output

Record the measurement period, aggregate inputs, decision owner, approved action, verification date, and exceptions. This is not a tax, legal, or financial conclusion.

## Error Handling

- Stop if data is incomplete or a proposed saving reduces auditability, access controls, or required review.
- Route eligibility or filing questions to the designated professional rather than automating a decision.
- Keep evidence redacted and reversible.

## Examples

Compare two fictional aggregate workload profiles, have the finance owner approve the selected option, and verify no account, payroll, or tax information was copied into the analysis.

## ROI Analysis

```
Fondo TaxPass cost:      ~$4,000-8,000/year (varies by plan)
Average R&D credit:      $21,000/year
Bookkeeping savings:     $12,000-24,000/year (vs. dedicated bookkeeper)
Tax prep savings:         $5,000-10,000/year (vs. separate CPA)
                         ------------------
Net ROI:                 $24,000-47,000/year benefit
```

## Maximize R&D Credits

| Action | Impact |
|--------|--------|
| Convert key contractors to W-2 employees | W-2 wages qualify at 100% vs 65% for contractors |
| Tag cloud compute (AWS/GCP) to R&D projects | Qualifies as supply expense |
| Document technical uncertainty in projects | Strengthens audit defense |
| Track contractor hours on R&D activities | Maximizes contractor credit |
| Include software tools used for R&D | Figma, GitHub, testing tools qualify |

## Choose the Right Plan

| Your Situation | Recommended Plan |
|----------------|-----------------|
| Pre-revenue, < 10 employees | Bookkeeping only |
| Revenue-generating, any size | TaxPass (includes R&D credits) |
| Series B+, complex structure | Enterprise (dedicated team) |
| Multi-entity or international | Enterprise |

## Cost Reduction Strategies

- Simplify chart of accounts (fewer custom categories = less CPA time)
- Use auto-categorization rules (reduces manual review)
- Connect all tools via OAuth (reduces manual CSV uploads)
- Respond promptly to CPA questions (reduces back-and-forth cost)

## Resources

- [Fondo Pricing](https://fondo.com)
- [R&D Tax Credits](https://fondo.com/tax-credits)

## Next Steps

For architecture overview, see `fondo-reference-architecture`.
