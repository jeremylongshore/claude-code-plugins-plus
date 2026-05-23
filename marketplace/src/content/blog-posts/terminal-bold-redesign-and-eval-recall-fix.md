---
title: "Terminal-Bold Redesign and the 0% Recall Bug"
description: "Phase 2 of the marketplace facelift brings monospace headings and sharper contrast. Plus: why the eval script reported 0% recall for skills that were clearly working."
date: "2026-03-14"
tags: ["web-development", "claude-code", "testing", "css"]
featured: false
---
Yesterday was OKLCH. Today is what you do with it.

Phase 2 of the marketplace facelift landed with a "Terminal-Bold" aesthetic. Monospace headings. Sharper contrast ratios. More deliberate use of the OKLCH color tokens from Phase 1. The goal: make the marketplace feel like a tool built by developers, for developers.

## The Terminal-Bold Aesthetic

The first facelift pass replaced the color system. This pass replaced the personality. Every page — homepage, explore, blog, skill details — got the same treatment:

- **Monospace headings** — `font-family: monospace` on all `h1`–`h3` elements. Sounds simple. Changes the entire feel of the site. Headers now read like terminal output, not marketing copy.
- **Contrast cranked up** — OKLCH makes this easy. Bump the `L` channel, leave chroma and hue alone. Perceptually correct brightness without color shifting.
- **Tighter spacing** — Reduced padding and margin on card components. More content above the fold.

PR review from Phase 1 caught inline styles, hardcoded OKLCH shadow values, and an unused CSS variable. All addressed in a cleanup commit before Phase 2 started. This is why PR review matters even on solo projects — you catch the shortcuts before they become tech debt.

The OKLCH values are now fully tokenized as CSS custom properties:

```css
:root {
  --color-primary: oklch(0.7 0.15 250);
  --color-surface: oklch(0.15 0.02 260);
  --shadow-md: 0 4px 12px oklch(0 0 0 / 0.3);
}
```

No more magic numbers scattered across stylesheets.

## The 0% Recall Bug

Unrelated to CSS, but worth the debugging story.

`run_eval.py` is the evaluation harness for the plugin system's skill discovery. It tests whether the search algorithm can find the right plugin for a given query. Standard information retrieval metrics: precision and recall.

It was reporting 0% recall. For skills that were obviously working. You could install them, run them, get correct output. But the eval said the system couldn't find them.

The bug: the search algorithm skips already-installed skills. Makes sense in production — if you already have it, why show it in search results? But the eval harness expected those skills to appear in the result set. Every skill in the test corpus was pre-installed. So the search returned nothing. Recall: 0/N = 0%.

The fix:

```python
# Before: only count newly discovered skills
found = [s for s in results if s not in installed]

# After: count all relevant skills, installed or not
found = [s for s in results if s in expected]
```

Three lines. The kind of bug where the code is doing exactly what it's told — just not what you meant.

## Performance Budget Bump

With 343+ plugins in the marketplace, the asset bundle was approaching the old performance budget. Bumped the limit to 16MB. Not ideal — I'd rather shrink the bundle — but the plugin metadata JSON is inherently large and the priority right now is shipping features, not optimizing payload size.

## Related Posts

- [OKLCH: Why Your CSS Color System Is Lying to You](/posts/oklch-color-system-marketplace-facelift/)
- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/posts/verified-plugins-program-quality-signal-for-the-marketplace/)
- [Marketplace Quality Blitz: 130 Stubs, 4300 Warnings](/posts/marketplace-quality-blitz-130-stubs-4300-warnings/)
