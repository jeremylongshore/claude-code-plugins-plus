---
title: "Usable, Not Just Functional: Entity Selection, Binary Eval, and 6 UX Fixes Across 4 Repos"
description: "40+ commits across 4 repos. CAD entity selection gets real bounding boxes, a binary eval framework bootstraps to v0.2.8, and the X triage plugin ships 6 UX features."
date: "2026-03-24"
tags: ["ai-agents", "python", "testing", "architecture", "claude-code", "debugging", "full-stack", "react"]
featured: false
---
Functional is table stakes. Usable is the moat.

March 24th was a 40+ commit day spread across four repositories. The theme wasn't new capabilities. It was making existing capabilities pleasant to operate. Entity selection that highlights the right rectangle instead of a wrong one. Confirmation feedback after every review command. Color-coded tags that match their overlay boxes. The kind of work that separates a prototype from a tool someone uses twice.

## CAD Entity Selection: The Bounding Box Problem

The entity selection UX in [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent) had a fundamental problem. When you clicked an entity in the viewer, the highlight overlay was wrong.

Not subtly wrong. Wrong by entire model units.

The frontend was using hardcoded `±10` model units from the entity centroid to draw selection rectangles. For a door schedule text block that spans 200 units, the highlight covered maybe 5% of the actual entity. For a tiny dimension tick, the highlight was 20x too large. Every selection looked broken because it was.

### Real Bounding Boxes from the Backend

The fix required the backend to compute actual entity bounding boxes and send them to the frontend. Not approximate. Not "close enough." Real bounds from the DXF geometry.

```python
def compute_entity_bounds(entity) -> dict:
    """Compute actual bounding box from entity geometry, not centroids."""
    if entity.dxftype() == 'LINE':
        start, end = entity.dxf.start, entity.dxf.end
        return {
            'min_x': min(start.x, end.x),
            'min_y': min(start.y, end.y),
            'max_x': max(start.x, end.x),
            'max_y': max(start.y, end.y),
        }
    # INSERT, TEXT, MTEXT, LWPOLYLINE — each has its own geometry extraction
    ...
```

Every DXF entity type stores its geometry differently. A LINE has start/end points. A LWPOLYLINE has a vertex list. An INSERT (block reference) requires resolving the block definition, applying scale and rotation, then computing the transformed bounds. TEXT and MTEXT need font metrics to get the width right.

The hardcoded `±10` was a shortcut from week one. It worked well enough to prove the concept. But "well enough" in a selection UI means "wrong every time in a way the user notices immediately."

### Color-Cycling Selection Highlights

With correct bounding boxes, the next step was visual differentiation. When you select three entities for a chat prompt, which highlight goes with which tag?

Six-color palette, assigned by selection index:

```javascript
const SELECTION_COLORS = [
  'rgba(59, 130, 246, 0.3)',   // blue
  'rgba(16, 185, 129, 0.3)',   // emerald
  'rgba(245, 158, 11, 0.3)',   // amber
  'rgba(139, 92, 246, 0.3)',   // purple
  'rgba(236, 72, 153, 0.3)',   // pink
  'rgba(6, 182, 212, 0.3)',    // cyan
];
```

The same color index applies to both the viewer overlay rectangle and the entity tag in the chat panel. Select entity #1, get a blue box and a blue tag. Entity #2 gets emerald. No guessing which tag maps to which highlight.

### Click-to-Focus Operations

The diff comparison already generates a planned operations checklist — "MOVE door D-101 from grid A to grid B," "DELETE redundant hatch pattern." Those operations sat in a text list. You had to find the referenced entity yourself.

Now they're clickable. Click an operation, the viewer pans and zooms to the target entity. The backend computes bounds per operation, the frontend does the camera math. The drawing is the navigation UI.

### The Diff Detection Fix

Separate from the UX work, the diff comparison engine had a bug: MODIFIED and MOVED categories never appeared. Everything was either ADDED or DELETED.

Root cause: `match_search_radius` and geometric `tolerance` were the same value. The search radius determines how far the algorithm looks for potential matches. The tolerance determines how close two entities must be to count as the same entity. When they're identical, the algorithm finds a candidate and immediately rejects it — the match is *exactly* at the boundary, and floating-point rounding pushes it out.

The fix split them:

```python
MATCH_SEARCH_RADIUS = 50.0   # how far to look for candidates
GEOMETRIC_TOLERANCE = 1.0     # how close to count as "same entity"
MOVE_THRESHOLD = 5.0          # minimum distance to classify as MOVED vs MODIFIED
```

Three distinct thresholds for three distinct questions. The `move_threshold` was also too low — entities with minor coordinate drift from re-export were classified as MOVED when they should have been MODIFIED. Raising it to 5.0 model units resolved the false positives.

A separate bug: block ATTRIBs (text attributes on block references) weren't captured during comparison. Two otherwise-identical door blocks with different room number ATTRIBs looked identical to the diff engine. Now ATTRIB text is included in the entity fingerprint.

PR #129 landed with 16 files changed. PR review caught a missing `<label>` element for accessibility, an undocumented magic number, and a SIM103 lint warning. All fixed before merge.

## j-rig-binary-eval: Zero to v0.2.8

A brand new project went from `git init` to v0.2.8 in a single day. Thirty-plus commits.

j-rig-binary-eval is a calibration framework for evaluating Claude Code skill quality. Not "does this skill run without errors" — that's CI. Binary eval asks "does this skill produce output that a senior engineer would approve?" Judgment layers, calibration curves, scoring rubrics, experiment design.

The day broke into phases.

**Phase 1: Governance scaffolding.** CLAUDE.md, beads integration, doc-filing index, master build blueprint. Ten epic reference files (EPIC-01 through EPIC-10) defining the full system architecture before writing a line of application code.

**Phase 2: Templates library.** Forty-seven reference files imported from the enterprise template collection. Immediately audited for bloat: 9 files deleted (~975 lines), 6 stale enterprise standards removed (~7,500 lines). The templates library was bigger than the project it was meant to serve.

This is a pattern worth calling out. Enterprise template libraries grow monotonically. Nobody deletes templates. The audit removed files that hadn't been referenced in 6+ months and standards documents from a previous org structure. The remaining templates are the ones that actually get used.

**Phase 3: Pattern A README.** The one-pager + operator-grade system analysis format. Title, tagline, badges, links, W5 table, stack table, key differentiators, then the full operator section. This README format exists so any engineer can understand the project in 90 seconds and operate it in 5 minutes.

The project is pre-code. All 30+ commits are governance, architecture, and planning artifacts. No application logic yet. That's intentional. The binary eval framework needs to be right before it's fast. Getting the epic structure, scoring rubrics, and experiment design wrong means rebuilding the calibration pipeline later.

## X Bug Triage Plugin: Six UX Enhancements

The [x-bug-triage-plugin](https://github.com/jeremylongshore/x-bug-triage-plugin) shipped v0.4.4 with six targeted UX improvements via PR #19. Yesterday was the [zero-to-v0.4.3 sprint](/blog/x-bug-triage-plugin-zero-to-v043-one-day/). Today was making it feel finished.

**E1: Action confirmation feedback.** All 11 review commands (approve, reject, defer, escalate, etc.) now emit a structured confirmation response. Before: the command ran silently. The user had to query the state to confirm it worked. After: immediate feedback with the action taken, the affected entity, and the new state.

**E2: Freshness assessment.** Source data ages. A tweet from 3 hours ago is fresh. A tweet from 3 weeks ago might reference a bug that's already fixed. The freshness system assigns `date_confidence` bands — HIGH (< 24h), MEDIUM (1-7d), LOW (7-30d), STALE (> 30d) — and surfaces warnings when the triage pipeline processes stale data.

**E3: Source status header.** Aggregates a `DegradationReport` per X API endpoint. If the tweets endpoint is returning 429s, the header shows it. If the search endpoint is slow, the header shows latency. Operators see API health at a glance instead of discovering it when a command fails.

**E4: File-based JSON cache.** Opt-in caching layer for X API responses. Development and testing no longer require live API calls. The cache writes JSON files with request fingerprints as filenames. `DEBUG_CACHE` logging shows hit/miss rates.

**E5: Hybrid dedup.** The original dedup was exact-match on tweet ID. Duplicate *content* across different tweets (retweets, quote tweets, copy-paste reports) passed through. The new hybrid approach combines character-trigram similarity with token-Jaccard scoring. Two tweets with 85%+ trigram overlap and 80%+ token-Jaccard get flagged as semantic duplicates before clustering.

**E6: Per-tier evidence counts.** The summary and detail views now show evidence counts broken down by severity tier. "3 CRITICAL, 7 HIGH, 12 MEDIUM" instead of just "22 bugs." Operators triage by tier, so the counts should match.

Eight new files, 14 modifications, 70 new tests (348 total), zero breaking changes.

PR review caught three things: magic numbers that should be extracted constants, fixed-width column padding that should be dynamic, and `DEBUG_CACHE` logging that was always on instead of opt-in. All addressed before merge.

The mermaid architecture diagram in the README was also replaced with a plain text flow diagram. Mermaid doesn't render on GitHub Pages. A tool that documents itself with diagrams nobody can see isn't documenting itself.

## The Pattern

Three projects, same lesson. The CAD tool had real entity selection from day one — the highlight was just in the wrong place. The triage plugin had all 11 review commands — they just didn't confirm they worked. The binary eval framework had enterprise templates — most of them were dead weight.

Functional is the first 80%. Usable is the remaining 80%.

The common thread across all of today's work: removing the gap between "this technically works" and "this is pleasant to use." Correct bounding boxes. Color-coded selections. Confirmation messages. Freshness warnings. Evidence counts by tier. None of these are features. They're the absence of friction.

---

**Related Posts:**

- [X Bug Triage Plugin: Zero to v0.4.3 in One Day](/blog/x-bug-triage-plugin-zero-to-v043-one-day/) — the bootstrap sprint this work builds on
- [PDF Extraction Bugs, Broadcast Persistence, and a 42-Commit Sweep Day](/blog/pdf-extraction-sweep-day-42-commits/) — another heavy multi-repo day with CAD debugging
- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/) — the original diff engine that today's MODIFIED/MOVED fix corrects
