---
name: draft-patterns
description: |
  Use when asked about UX patterns, interaction best practices, form design,
  navigation patterns, or loading states. Examples: "best practice for form
  validation", "navigation pattern for dashboard", "loading state UX"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# draft-patterns — UX Pattern Reference

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User asks about interaction patterns, best practices, form design, navigation, or loading/empty states.

## Workflow

1. **Identify pattern category** from user request (forms, navigation, loading, empty states, modals, etc.)
2. **Search UX knowledge base:**
   ```bash
   python3 -m draft_agent.uiux search --domain ux --query "{pattern_category}" --limit 5
   ```
3. **Cross-reference severity ratings** from results — surface Critical and High first
4. **Output** structured do/don't table with code examples and severity

## Output format

```
┌─ UX Patterns — {pattern_category} ──────────────────────────────────────────┐
│ Category    │ Issue              │ Do                  │ Don't    │ Severity │
├─────────────┼────────────────────┼─────────────────────┼──────────┼──────────┤
│ {category}  │ {issue}            │ {do}                │ {dont}   │ Critical │
│ {category}  │ {issue}            │ {do}                │ {dont}   │ High     │
│ {category}  │ {issue}            │ {do}                │ {dont}   │ Medium   │
└─────────────┴────────────────────┴─────────────────────┴──────────┴──────────┘

Code example ({do_example_label}):
{code_block}
```

## Anti-patterns

- Never recommend patterns without checking platform context (web vs. mobile vs. desktop)
- Never ignore severity ratings — Critical issues must be called out explicitly
- Never present more than 7 patterns per category without grouping
- Never omit code examples for implementation-level questions

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
