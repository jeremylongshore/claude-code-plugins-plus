---
title: "PDF Extraction Bugs, Broadcast Persistence, and a 42-Commit Sweep Day"
description: "Sub-pixel noise, color inheritance, and coordinate conventions. Fixing PDF entity extraction in cad-dxf-agent plus persistence work across four projects."
date: "2026-03-05"
tags: ["python", "debugging", "architecture", "full-stack", "release-engineering", "cad"]
featured: false
---
Forty-two commits across six repos in one day. No new features. Just closing loops, killing bugs, and hardening things that almost worked.

The most interesting work was in PDF extraction. The rest was necessary. Here's the breakdown.

## PDF Entities Are Not DXF Entities

The comparison engine in [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent) works great on native DXF files. Geometry normalization, spatial binning, quantized fingerprints — all tuned for how DXF stores entities.

The problem: users also upload PDFs of engineering drawings. Scanned shop drawings, exported revision sets, vendor submittals as PDF.

Converting PDF to comparison-ready entities revealed three bugs that don't exist in the DXF path.

### Bug 1: Sub-Pixel Noise

PDF renderers leave artifacts. Tiny line segments, invisible rectangles, hairline paths — entities with dimensions under 0.001 inches that aren't real drawing content. They're rendering artifacts from how the PDF producer tessellated curves or clipped regions.

In the DXF path, this never happens. DXF entities are authored by humans (or CAD software acting on human intent). PDF entities come from a print pipeline that makes no promises about geometric cleanliness.

The fix is a noise filter that runs before entity classification:

```python
MIN_ENTITY_DIMENSION = 0.001  # inches

def filter_sub_pixel_noise(entities: list[Entity]) -> list[Entity]:
    """Remove entities too small to be intentional drawing content."""
    filtered = []
    for entity in entities:
        bbox = entity.bounding_box
        width = bbox.max_x - bbox.min_x
        height = bbox.max_y - bbox.min_y

        if width < MIN_ENTITY_DIMENSION and height < MIN_ENTITY_DIMENSION:
            continue  # sub-pixel noise

        filtered.append(entity)
    return filtered
```

Simple threshold. You could get clever with adaptive sizing based on drawing scale, but 0.001 inches handles every real-world case I've tested. The smallest intentional feature in any engineering drawing I've processed is a dimension tick mark at ~0.01 inches. Order of magnitude margin.

### Bug 2: Color Inheritance

DXF has a clear color model. Each entity has a color. If it's BYLAYER, check the layer. If it's BYBLOCK, check the block. Three levels, well-defined precedence.

PDF has no such model. Colors come from the graphics state stack — stroke color, fill color, color space transforms, transparency groups. The extractor was reading direct color attributes and ignoring the inherited state. Result: entities showing up as black when they should be red, or vice versa.

The fix required walking the graphics state at extraction time and capturing the *resolved* color, not just the directly-assigned one. Three levels of fallback:

1. Direct color on the path operation
2. Current graphics state stroke/fill color
3. Default (black)

This mirrors the DXF BYLAYER/BYBLOCK pattern but the implementation is completely different. PDF color resolution is a stack walk. DXF color resolution is a table lookup.

### Bug 3: Text Coordinate Conventions

DXF text entities use insertion point + height + rotation. The insertion point is the bottom-left of the first character (usually). The text grows rightward from there.

PDF text uses a text matrix — a full affine transform that encodes position, scale, rotation, and skew in one 6-element array. The "position" of a PDF text entity is wherever the text matrix says it is, which might be the baseline origin, might be the top-left, depends on the font metrics and the PDF producer.

The comparison engine matches text entities by position + content. When the positions are in different coordinate conventions, identical text on identical drawings doesn't match.

The fix normalizes PDF text positions to baseline-origin before entity creation. Font metrics give you the ascent, and you subtract it from the text matrix position to get the baseline.

These three fixes shipped across PRs #67, #68, and #72. Together they brought PDF comparison quality to parity with native DXF comparison.

### The Render Quality Guard

On top of the individual fixes, PR #67 also added a render quality guard — a pre-comparison check that rejects PDF extractions below a confidence threshold. If the noise filter removes more than 40% of extracted entities, or if color resolution fails on more than 20% of paths, the system flags the extraction as unreliable and tells the user to supply a native DXF instead.

This matters because not all PDFs are equal. A PDF exported directly from AutoCAD retains clean geometry. A PDF that's been through a scan-to-PDF pipeline, or printed and re-scanned, produces garbage entities. Better to reject early than to show a comparison full of phantom differences.

Also in this batch: PR #70 cleaned dead code. Unused test fixtures, orphaned helper modules, junk files from early prototyping. Not exciting but the repo is 15% smaller. PR #71 kicked off EPIC-CAD-01 — a formal capability audit with architecture baseline and evaluation plan. Sweep day isn't just bug fixes. It's also documentation of what the system can and can't do.

Released as v0.5.0.

## Braves: Persistence and Broadcast Intelligence

The Braves Booth Intelligence dashboard got two significant PRs.

**PR #16 — SQLite persistence + back-of-card + on-deck lookahead.** Three features in one PR because they're all about the same thing: giving the broadcaster information without them asking for it.

"Back of card" is a broadcast term. It's the summary stats printed on the back of a baseball card — batting average, home runs, RBIs, the numbers you rattle off when a batter steps up. The dashboard now generates this automatically for the current batter.

On-deck lookahead does the same for the *next* batter. You prep your notes while the current at-bat is still happening.

SQLite persistence means broadcast notes survive across sessions. The broadcaster's custom annotations, narrative threads, and game context don't disappear when the service restarts. WAL mode, single-writer, zero-config.

**PR #17 — Prefetch hardening.** Three edge cases that only surface in live game conditions:

1. **Boot discovery**: the service finds today's game automatically on startup instead of requiring manual configuration. No more editing a config file at 6:55 PM before first pitch
2. **Pitcher-change re-prefetch**: when a reliever comes in, all batter stat cards need to be regenerated for the new matchup. The system detects the pitcher change and re-fetches. This is the one that matters most — a broadcaster citing stats against the *previous* pitcher is worse than citing no stats at all
3. **Idempotency**: don't re-fetch data that's already cached. Sounds obvious but the original prefetch had no dedup. A pitching change was triggering full re-fetches for batters whose data hadn't changed

None of these are hard problems individually. They're the kind of thing you only find by running the system during an actual game and watching it misbehave.

## Quick Hits

**claude-code-plugins** — Disabled all cron schedules that were burning GitHub Actions minutes for no reason. Fixed mobile horizontal overflow on the /explore page — badge text was too large on small screens and the cowork plugin card was breaking its container. Accepted a community plugin submission (deAPI Skills for AI media generation), reverted it due to quality issues, then re-accepted after the author fixed them. Updated Playwright tests for dark theme changes.

**hustle** — The authentication system had an OpenTelemetry instrumentation that created a deadlock on login POST requests. The request would hang permanently — no timeout, no error, just an infinite spinner. The OTel middleware was wrapping the Firebase Auth call in a span that held a lock the auth callback also needed. Removing the OTel middleware was the fix. Sometimes observability tooling is the bug. Also cleared a stale fallback cookie on logout that was causing session ghosts — users who logged out still appeared authenticated on the next page load.

Neither of these was complex to fix once diagnosed. Both had been annoying for days.

## The Sweep Day Pattern

Forty-two commits across six repos sounds chaotic. It's not. It's what happens when you spend a week doing focused feature work and let the edges accumulate. The PDF bugs were noticed during demo prep. The prefetch issues surfaced in real game testing. The mobile overflow showed up when someone actually used a phone.

There's a rhythm to it. You context-switch between projects, but each switch is to a problem you already understand. You diagnosed the PDF noise issue three days ago while testing something else. You just didn't fix it because you were in the middle of building the comparison wizard. Sweep day is when you cash in all those mental IOUs.

The risk is scope creep. Every bug you fix reveals the next one. The color inheritance fix exposed the text coordinate problem. The prefetch idempotency fix revealed the pitcher-change gap. You have to draw a line: fix what you've found, release, move on. That's what v0.5.0 represents — not perfection, but a known-good boundary.

Sweep days are maintenance. They're not glamorous. But shipping v0.5.0 of the CAD agent with PDF parity — that only happens because someone spent a day on sub-pixel noise thresholds and color inheritance chains.

---

## Related Posts

- [Building a Deterministic DXF Comparison Engine in One Day](/posts/deterministic-dxf-comparison-engine-one-day-build/) — the engine these PDF fixes extend
- [Engine to Product: Three Interfaces, One Codebase](/posts/engine-to-product-three-interfaces-one-codebase/) — CLI, API, and wizard on the comparison engine
- [Zero to CI: Full-Stack Dashboard in One Session](/posts/zero-to-ci-full-stack-dashboard-one-session/) — the Braves dashboard from first commit to green CI
