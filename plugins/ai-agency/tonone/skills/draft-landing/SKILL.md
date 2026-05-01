---
name: draft-landing
description: |
  Use when asked to structure a landing page, design page layout for conversion,
  or plan landing page information architecture. Examples: "landing page structure
  for SaaS", "conversion-optimized layout"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# draft-landing — Landing Page Information Architecture

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User needs a landing page structure, section order, or conversion-optimized layout. Product type is known or discoverable.

## Workflow

1. **Identify product type** from user request or project context
2. **Search landing page patterns:**
   ```bash
   python3 -m draft_agent.uiux search --domain landing --query "{product_type}" --limit 3
   ```
3. **Search product reasoning for audience + conversion context:**
   ```bash
   python3 -m draft_agent.uiux search --domain product --query "{product_type}" --limit 3
   ```
4. **Validate each section** against the "so what?" test — every section must earn its place
5. **Output** section order with CTA placement markers

## Output format

```
┌─ Landing Page IA — {product_type} ──────────────────────────────────┐
│ #  │ Section            │ Purpose                    │ CTA?          │
├────┼────────────────────┼────────────────────────────┼───────────────┤
│  1 │ {section_name}     │ {purpose}                  │ Primary CTA   │
│  2 │ {section_name}     │ {purpose}                  │ —             │
│  3 │ {section_name}     │ {purpose}                  │ Secondary CTA │
│  … │ …                  │ …                          │ …             │
└────┴────────────────────┴────────────────────────────┴───────────────┘

Conversion strategy: {strategy}
CTA copy guidance:   {cta_guidance}
```

## Anti-patterns

- Never skip the "so what?" test per section — if a section can't answer it, cut it
- Never add sections without a clear conversion purpose
- Never place the primary CTA below the fold on the first screen
- Never structure the page without knowing the primary audience and their job-to-be-done

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
