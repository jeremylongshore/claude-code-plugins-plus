---
title: "Pregame Storylines Stuck Forever and a Docs Sync That Should Have Been Boring"
description: "The pregame view showed 'Generating storylines...' forever when the background prefetch failed. A cache-only read with no fallback was the culprit."
date: "2026-04-10"
tags: ["debugging", "typescript", "full-stack", "python"]
featured: false
---
The Braves Booth pregame view had a spinner that never stopped spinning.

Open the dashboard before a game. The lineup loads. The matchup previews load. The storylines section says "Generating storylines..." and stays there. Forever. No error. No timeout. Just a loading state that never resolves.

Two repos got commits today. One was a real bug. The other was a docs consistency audit. Maintenance day.

## The Cache-Only Read

The pregame route fetched storylines with a synchronous cache read:

```typescript
const storylines = getStorylines(gamePk);
```

That function did one thing: check the cache and return whatever was there. If the background prefetch had already run and populated the cache, great. If the prefetch failed, or hadn't run yet, or the cache key expired — `null`. Permanently `null`. The route returned null to the frontend, the frontend saw no storylines, and the loading spinner waited for data that would never arrive.

The background prefetch was supposed to run on a schedule. Most of the time it did. But when it didn't — network hiccup, cold start, timing race — there was no recovery path. The route trusted the cache completely and had no fallback.

## The Fix

Replace the cache-only read with a function that tries the cache first and falls back to inline generation:

```typescript
export async function getOrGenerateStorylines(
  gamePk: number
): Promise<NarrativeResult | null> {
  const cached = getStorylines(gamePk);
  if (cached) return cached;

  try {
    await prefetchStorylines(gamePk);
    return getStorylines(gamePk);
  } catch (err) {
    logger.warn({ err, gamePk }, "Inline storyline generation failed");
    return null;
  }
}
```

If the cache has data, return it immediately. If not, call the same prefetch function the background job uses, which populates the cache, then read the cache again. If even that fails, log it and return null — but at least the failure is visible in logs instead of silently manifesting as an eternal spinner.

The route call changed from synchronous to async:

```typescript
const storylines = await getOrGenerateStorylines(gamePk);
```

Three files touched. Twenty-one lines added. The test mock updated from `getStorylines` to `getOrGenerateStorylines` and from `mockReturnValue` to `mockResolvedValue` because the function is now async.

## The Pattern

This is a common trap with background prefetch architectures. You build a prefetch job that warms the cache. You build a route that reads the cache. Everything works in testing because the prefetch always runs first. In production, the prefetch fails silently once, and every downstream consumer shows a loading state forever.

The fix is always the same: treat the cache as an optimization, not a dependency. If the cache misses, generate inline. The first request is slower. Every subsequent request hits the warm cache. The user never sees an infinite spinner.

## IntentCAD Docs Sync

The other commit was a docs consistency audit on cad-dxf-agent. Test counts drifted — README said ~4500, actual count was 4,687. The project description in `pyproject.toml` didn't match the README tagline. The docs index was missing entries for two recent documents.

Five files, fifteen lines changed. The kind of chore that prevents documentation rot from compounding into real confusion six months from now.

## The Day

Two repos. Three commits total. One real bug that would have bitten the broadcast team during the next pregame segment. One housekeeping pass that keeps docs honest. Not every day needs to be a 40-commit marathon.

---

### Related Posts

- [Braves Booth -- Idle Recap, Dashboard Density, and AI Pitcher Narratives](/posts/braves-booth-dashboard-ui-refactor-ai-pitcher-narrative/) -- the pregame/idle view architecture this bug lived in
- [Braves Booth v1.0.0: Player Drill-Down, Lineup Cache Bug, and Shipping 1.0](/posts/braves-booth-v1-release-player-drilldown/) -- another cache bug caught in the same codebase
- [Resizable Columns and WCAG Contrast Fixes on the Braves Dashboard](/posts/resizable-columns-wcag-contrast-braves-dashboard/) -- recent polish work on the same dashboard
