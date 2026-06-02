---
name: form-style
description: |
  Use when asked to select a UI style, choose a design direction, pick a visual
  approach for a product, or match a style to an industry. Examples: "what style
  fits a fintech app", "choose between neumorphism and glassmorphism", "design
  direction for healthcare SaaS"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# form-style — UI Style Selection

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

Product needs a visual direction. Industry or product type is known or discoverable from context.

## Workflow

1. **Identify product type** from user request or project context
2. **Search product reasoning:**
   ```bash
   python3 -m form_agent.uiux search --domain product --query "{product_type}" --limit 3
   ```
3. **Get recommended style details:**
   ```bash
   python3 -m form_agent.uiux search --domain style --query "{recommended_style}" --limit 3
   ```
4. **Cross-reference anti-patterns** from the product search results — check the Anti_Patterns field
5. **Output** the recommendation using the format below

## Output format

```
┌─ Style Recommendation ─────────────────────┐
│ Product:     {product_type}                 │
│ Style:       {primary_style}                │
│ Fallback:    {secondary_style}              │
├─ Effects ───────────────────────────────────┤
│ {key_effects from style search}             │
├─ Anti-patterns ─────────────────────────────┤
│ ✗ {anti_pattern_1}                          │
│ ✗ {anti_pattern_2}                          │
├─ Implementation Checklist ──────────────────┤
│ □ {checklist_item_1}                        │
│ □ {checklist_item_2}                        │
└─────────────────────────────────────────────┘
```

## Anti-patterns

- Never pick style based on aesthetics alone — match to product type + audience
- Never ignore anti-pattern list from reasoning rules
- Never recommend more than 2 combined styles (primary + fallback)
- Never recommend a style marked as incompatible with the target framework

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
