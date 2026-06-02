---
name: surge-landing
description: |
  Use when asked to design growth-optimized landing pages, activation funnel
  layouts, or experiment-friendly page structures. Examples: "growth-optimized
  landing", "activation funnel layout", "A/B testable page"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# surge-landing — Growth-Optimized Landing Page

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User needs a landing page designed for growth: activation funnels, A/B testing, acquisition, or PLG flows.

## Workflow

1. **Identify product type and growth goal** from user request (acquisition, activation, PLG, trial, freemium, etc.)
2. **Search landing page patterns:**
   ```bash
   python3 -m surge_agent.uiux search --domain landing --query "{product_type}" --limit 3
   ```
3. **Search product reasoning:**
   ```bash
   python3 -m surge_agent.uiux search --domain product --query "{product_type}" --limit 3
   ```
4. **Search UX for friction points:**
   ```bash
   python3 -m surge_agent.uiux search --domain ux --query "forms validation loading" --limit 3
   ```
5. **Output** experiment-friendly structure with activation triggers and friction audit

## Output format

```
┌─ Growth Landing Page — {product_type} ──────────────────────────────┐
│ #  │ Section            │ Purpose                    │ Experiment?   │
├────┼────────────────────┼────────────────────────────┼───────────────┤
│  1 │ {section_name}     │ {purpose}                  │ A/B headline  │
│  2 │ {section_name}     │ {purpose}                  │ —             │
│  3 │ {section_name}     │ {purpose}                  │ A/B CTA copy  │
│  … │ …                  │ …                          │ …             │
└────┴────────────────────┴────────────────────────────┴───────────────┘

Activation triggers:   {activation_triggers}
Funnel structure:      {funnel_structure}
Friction points:       {friction_points}
Experiment surfaces:   {experiment_surfaces}
```

## Anti-patterns

- Never optimize for vanity metrics (page views, time on page) over activation metrics
- Never add friction (sign-up gates, long forms) before demonstrating product value
- Never design sections that can't be independently A/B tested
- Never ship a growth page without identifying at least one experiment surface

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
