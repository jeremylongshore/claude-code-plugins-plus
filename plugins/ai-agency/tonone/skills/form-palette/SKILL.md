---
name: form-palette
description: |
  Use when asked to generate a color palette, create industry-matched colors, or
  pick colors for a product type. Examples: "color palette for fintech",
  "healthcare app colors", "SaaS brand colors"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# form-palette — Color Palette Generation

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

Product needs a color palette. Industry or product type is known or discoverable from context.

## Workflow

1. **Identify product type** from user request or project context
2. **Search product reasoning:**
   ```bash
   python3 -m form_agent.uiux search --domain product --query "{product_type}" --limit 3
   ```
3. **Search color conventions:**
   ```bash
   python3 -m form_agent.uiux search --domain color --query "{product_type}" --limit 3
   ```
4. **Output** a full shadcn-compatible token set using the format below

## Output format

```
┌─ Color Palette — {product_type} ───────────────────────────────────┐
│ Token                  │ Light            │ Dark             │ WCAG │
├────────────────────────┼──────────────────┼──────────────────┼──────┤
│ Primary                │ {hex}            │ {hex}            │ AA   │
│ On Primary             │ {hex}            │ {hex}            │ AA   │
│ Secondary              │ {hex}            │ {hex}            │ AA   │
│ On Secondary           │ {hex}            │ {hex}            │ AA   │
│ Accent                 │ {hex}            │ {hex}            │ AA   │
│ On Accent              │ {hex}            │ {hex}            │ AA   │
│ Background             │ {hex}            │ {hex}            │ —    │
│ Foreground             │ {hex}            │ {hex}            │ AA   │
│ Card                   │ {hex}            │ {hex}            │ —    │
│ Card Foreground        │ {hex}            │ {hex}            │ AA   │
│ Muted                  │ {hex}            │ {hex}            │ —    │
│ Muted Foreground       │ {hex}            │ {hex}            │ AA   │
│ Border                 │ {hex}            │ {hex}            │ —    │
│ Destructive            │ {hex}            │ {hex}            │ AA   │
│ On Destructive         │ {hex}            │ {hex}            │ AA   │
│ Ring                   │ {hex}            │ {hex}            │ —    │
└────────────────────────┴──────────────────┴──────────────────┴──────┘
```

## Anti-patterns

- Never violate WCAG AA contrast (4.5:1 for normal text, 3:1 for large text)
- Never ignore industry color conventions (e.g., red for destructive, green for success)
- Never output tokens without both light and dark values
- Never reuse the same hue for Primary and Destructive

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
