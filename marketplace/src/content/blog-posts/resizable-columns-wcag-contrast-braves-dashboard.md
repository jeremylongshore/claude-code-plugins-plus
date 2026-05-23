---
title: "Resizable Columns and WCAG Contrast Fixes on the Braves Dashboard"
description: "Adding drag-to-resize panels and fixing WCAG AA contrast ratios on the Braves Booth dashboard — the kind of polish that separates prototypes from broadcast tools."
date: "2026-04-07"
tags: ["react", "full-stack", "web-development", "architecture"]
featured: false
---
Light day. Two PRs merged on Braves Booth Intelligence, both polish work. No new features, no new endpoints. Just making the existing dashboard better for the people who actually use it during live broadcasts.

## Resizable Columns with a Batter-First Layout

The dashboard has two main columns: batter stats on the left, pitcher stats on the right. The original layout gave the pitcher card the flex space. That was backwards. During a broadcast, the batter is the primary focus — who's at the plate drives the conversation.

Flipped it. The batter card now gets 50% of the viewport as the hero panel. The pitcher column compresses to fit.

More importantly, operators can now drag to resize both columns. Added `react-resizable-panels` for this:

```tsx
<PanelGroup direction="horizontal" autoSaveId="dashboard-columns">
  <Panel defaultSize={50} minSize={30}>
    <BatterCard />
  </Panel>
  <PanelResizeHandle className="resize-handle" />
  <Panel minSize={25}>
    <PitcherCard />
  </Panel>
</PanelGroup>
```

The `autoSaveId` prop persists the user's column sizes to `localStorage`. An operator sets their preferred layout once, and it survives page refreshes and browser restarts. No backend storage needed.

To make the pitcher tables fit a narrower column, I stripped the `min-width` constraints from `PitcherCard.tsx`. The tables now wrap naturally instead of forcing horizontal scroll.

62 lines changed in `DashboardGrid.tsx`, 4 in `PitcherCard.tsx`, plus the package dependency. Small diff, big usability win.

## WCAG AA Contrast Compliance

The dark theme had a contrast problem. The `text-3` color (#6e7681) was hitting a 3.42:1 ratio against the background surfaces. WCAG AA requires 4.5:1 for normal text. Failing.

This is the kind of thing you don't notice on a high-end monitor in a well-lit office. You absolutely notice it in a broadcast booth with mixed lighting and a laptop screen at an angle.

Four CSS variable changes in `globals.css`:

```css
--color-text-3: #848d97;    /* was #6e7681 — now passes AA */
--color-text-2: #9198a1;    /* was #8b949e — bumped for consistency */
--color-border: #444c56;    /* was #30363d — ~40% more visible */
--color-border-bright: #636e7b;  /* was #484f58 — same treatment */
```

All text tokens now pass WCAG AA. The borders got the same treatment — not because they fail contrast requirements (borders aren't covered by WCAG text rules), but because they were too subtle on lower-quality displays.

Four lines changed. Every text element on the dashboard is now accessible.

## Why This Matters

These two PRs are the definition of unsexy work. No one tweets about resizable panels or contrast ratios. But this is exactly what separates a demo from a production tool.

A broadcast operator working a three-hour game doesn't want to squint at low-contrast text. They don't want to fight a fixed layout that wastes screen space on the wrong stats. They want to set up their workspace and forget about it.

That's what shipped today.

---

### Related Posts

- [Braves Booth — Idle Recap, Dashboard Density, and AI Pitcher Narratives](/posts/braves-booth-dashboard-ui-refactor-ai-pitcher-narrative/)
- [Braves Booth v1.0.0: Player Drill-Down, Lineup Cache Bug, and Shipping 1.0](/posts/braves-booth-v1-release-player-drilldown/)
- [Brand Consistency, CSS Variables, and a Sponsor Page Redesign](/posts/brand-consistency-css-variables-sponsor-page-redesign/)
