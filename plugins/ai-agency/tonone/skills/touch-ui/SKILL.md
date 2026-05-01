---
name: touch-ui
description: |
  Use when asked about mobile UI guidelines, touch targets, platform-specific UI
  rules, or mobile interaction patterns. Examples: "iOS touch targets", "Android
  UI guidelines", "mobile form design"
allowed-tools: Read, Bash, Glob, Grep
version: 0.6.6
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# touch-ui — Mobile UI Guidelines

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## When to use

User asks about mobile UI, touch targets, platform conventions, or mobile interaction patterns.

## Workflow

1. **Identify platform and topic** from user request (iOS / Android / cross-platform; touch targets, navigation, forms, gestures, etc.)
2. **Search app-interface knowledge base:**
   ```bash
   python3 -m touch_agent.uiux search --domain app-interface --query "{platform} {topic}" --limit 5
   ```
3. **Search stack conventions if framework is mentioned:**
   ```bash
   python3 -m touch_agent.uiux search --domain stacks --query "{framework}" --limit 3
   ```
4. **Output** platform-specific rules with code examples

## Output format

```
┌─ Mobile UI Guidelines — {platform} ─────────────────────────────────┐
│ Rule                   │ Spec                    │ Severity          │
├────────────────────────┼─────────────────────────┼───────────────────┤
│ Touch target min size  │ 44×44pt (iOS)           │ Critical          │
│ Touch target min size  │ 48×48dp (Android)       │ Critical          │
│ {rule}                 │ {spec}                  │ {severity}        │
└────────────────────────┴─────────────────────────┴───────────────────┘

Code example ({platform}):
{code_block}
```

## Anti-patterns

- Never apply iOS Human Interface Guidelines patterns on Android (and vice versa)
- Never set touch targets below 44×44pt on iOS or 48×48dp on Android
- Never use hover-dependent interactions on touch-primary interfaces
- Never skip platform detection — always confirm iOS vs. Android before outputting guidelines

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
