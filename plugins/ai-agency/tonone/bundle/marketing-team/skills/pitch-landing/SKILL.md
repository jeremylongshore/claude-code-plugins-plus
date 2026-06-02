---
name: pitch-landing
description: |
  Use when asked to structure a landing page for positioning, plan a
  conversion-optimized page layout, or design a launch page. Examples: "landing
  page for product launch", "conversion-optimized layout for SaaS"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# pitch-landing — Launch & Positioning Landing Page

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User needs a landing page structured around product positioning, launch messaging, or conversion for a specific audience.

## Workflow

1. **Identify product type and positioning anchor** from user request or brief
2. **Search landing page patterns:**
   ```bash
   python3 -m pitch_agent.uiux search --domain landing --query "{product_type}" --limit 3
   ```
3. **Search product reasoning for audience + messaging context:**
   ```bash
   python3 -m pitch_agent.uiux search --domain product --query "{product_type}" --limit 3
   ```
4. **Layer in positioning:** CTA strategy, social proof placement, objection handling
5. **Output** section order with conversion and messaging optimization

## Output format

```
┌─ Launch Landing Page — {product_type} ──────────────────────────────┐
│ #  │ Section            │ Purpose                    │ CTA?          │
├────┼────────────────────┼────────────────────────────┼───────────────┤
│  1 │ {section_name}     │ {purpose}                  │ Primary CTA   │
│  2 │ {section_name}     │ {purpose}                  │ —             │
│  3 │ {section_name}     │ {purpose}                  │ Secondary CTA │
│  … │ …                  │ …                          │ …             │
└────┴────────────────────┴────────────────────────────┴───────────────┘

CTA strategy:          {cta_strategy}
Social proof:          {social_proof_placement}
Objection handling:    {objection_section}
Positioning anchor:    {positioning_anchor}
```

## Anti-patterns

- Never structure copy without a clear positioning anchor (who it's for + what makes it different)
- Never add sections that don't serve conversion or objection handling
- Never place social proof after the primary CTA — it should reinforce before the ask
- Never launch without a single, unambiguous primary CTA per viewport

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
