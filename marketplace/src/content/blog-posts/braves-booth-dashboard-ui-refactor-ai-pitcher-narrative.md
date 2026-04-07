---
title: "Braves Booth — Idle Recap, Dashboard Density, and AI Pitcher Narratives"
description: "Refactoring the Braves broadcast dashboard idle view, eliminating sub-10px fonts, and replacing duplicated AI narrative logic with a structured buildPitcherFacts function."
date: "2026-04-03"
tags: ["react", "typescript", "full-stack", "ai-agents", "architecture"]
featured: false
---
Between games, the Braves Booth dashboard used to show a tab bar with RECAP and PREVIEW buttons. Pick one. The problem: announcers don't want to choose. They want the full picture — what just happened and what's coming next — on a single screen with no clicks.

Two commits, 29 files, 600 lines changed. The idle view got rebuilt, the entire UI got tighter, and the AI pitcher narrative system got replaced with something that actually works.

## The Idle View Problem

The old between-games state showed either a recap or a preview, toggled by tab buttons in the GameStateBar. This forced a decision that shouldn't exist. When there's no live game, the announcer needs both: the line score and AI recap from the last game, plus a clickable card previewing the next one.

The fix removes the tab buttons entirely. The idle page now renders the full recap — line score plus AI-generated game summary — with a next-game preview card below it. Click the preview card and it expands into the full pregame view.

The backend side needed a new pregame route that fetches game context from the MLB schedule API for future games. The existing schedule fetcher only handled today's games. Now it looks ahead, pulls the matchup, and caches it with a `TTL.GAME_SCHEDULE` of 300 seconds.

```typescript
// DRY pregame fallback — one helper instead of three scattered checks
static fromGameState(gameState: GameState): PregameContext {
  return {
    homeTeam: gameState.homeTeam,
    awayTeam: gameState.awayTeam,
    probablePitchers: gameState.probablePitchers,
    venue: gameState.venue,
    gameTime: gameState.gameTime,
  };
}
```

PR review caught the duplication early. Three different components were building pregame fallback objects with slightly different shapes. The `fromGameState()` helper killed all three.

## Dashboard Density Overhaul

The dashboard runs on a three-column grid. Before this refactor, the columns had loose padding and inconsistent widths across breakpoints. The new layout uses responsive rails: 280px at the smallest breakpoint, 320px at medium, 360px at large.

Changes that sound small but affect every panel:

- **GameStateBar** got a gradient background with larger score and inning text. The old bar had redundant labels — "Home:" and "Away:" before team names that were already obvious from the logo and position. Removed.
- **PanelHeader** gained a `variant` prop. The center column uses `primary` (red accent border) to visually anchor it as the main content area. Side columns use the default.
- **Weather card** absorbed the Wind Impact panel. Two separate cards for weather and wind was a waste of vertical space. One card, two sections.
- **Ticker** got slowed from its original scroll speed to 75 seconds per cycle and reduced in height. The old ticker was distracting during live broadcasts.

## The Font Floor Sweep

The second commit started with a specific fix — pitcher scouting reports — and turned into a codebase-wide audit. While tightening the center column, I found `text-[7px]` and `text-[8px]` classes scattered across 15 files. Sub-10px text on a dashboard meant for glancing during a live broadcast is useless.

Every instance got bumped. OnDeckPanel, CohostPanel, BullpenPanel — all labels moved to a 10px minimum. The ghost number (a decorative large number behind panel content) got removed entirely. It looked clever in the mockup and was visual noise in practice.

The center column went full TweetDeck-density: reduced padding, tighter gaps, more data per viewport pixel.

## Replacing AI Narrative Duplication

The PitcherCard had an AI narrative block that was supposed to give announcers a quick scouting summary. The problem: it duplicated the same narrative generation logic that existed elsewhere, and the output was unstructured prose that varied wildly between pitchers.

The replacement is a dedicated `buildPitcherFacts()` function in a new file:

```typescript
// frontend/src/lib/build-facts.ts

export function buildPitcherFacts(pitcher: PitcherStats): string[] {
  const facts: string[] = [];

  if (pitcher.era !== undefined) {
    facts.push(`ERA ${pitcher.era.toFixed(2)}`);
  }

  if (pitcher.strikeouts && pitcher.inningsPitched) {
    const kPer9 = (pitcher.strikeouts / pitcher.inningsPitched) * 9;
    facts.push(`${kPer9.toFixed(1)} K/9`);
  }

  if (pitcher.whip !== undefined) {
    facts.push(`WHIP ${pitcher.whip.toFixed(2)}`);
  }

  // Velocity trend, pitch arsenal, awards follow the same pattern
  return facts;
}
```

78 lines. Structured output. Every fact is a string the announcer can read verbatim: "ERA 3.42", "11.2 K/9", "WHIP 1.08". No prose, no variation, no AI hallucination risk. The stats come from the MLB API, not from an LLM making up numbers.

When stats aren't available — early season, minor league callup, whatever — the function returns an empty array and the card falls back to the basic stat line. No "Unable to generate narrative" error states.

## H2H Matchup Polish

The head-to-head matchup display got two changes that matter more than they sound:

**Larger text.** The batter-vs-pitcher matchup numbers were the same size as surrounding panel text. They should be the focal point. Bumped up.

**OPS conditional coloring.** An OPS over .800 against the current pitcher is green. Under .600 is red. Between is neutral. The announcer glances at the card and instantly knows if the batter owns this pitcher or struggles against him. A summary callout line below reinforces it in plain English.

## The CSS Hover Fix

The PR review flagged React `onMouseEnter`/`onMouseLeave` handlers on the next-game preview card. These were controlling a hover state that CSS can handle natively:

```css
.next-game-card:hover {
  transform: scale(1.02);
  border-color: var(--braves-red);
}
```

No state management. No re-renders. CSS does this better in every dimension.

## What Changed

Two commits. 605 insertions, 335 deletions across 29 files. One new file (`build-facts.ts`). The dashboard went from a tab-based idle view to a unified recap-plus-preview layout. Every font in the codebase is now 10px or larger. The AI pitcher narrative system went from duplicated LLM prose to a deterministic fact builder that announcers can trust.

The pattern is the same one that keeps showing up on this project: broadcast tools need to be glanceable, trustworthy, and zero-interaction. Every change here moved in that direction.

---

### Related Posts

- [Building a Production Multi-Agent AI System](/posts/building-production-multi-agent-ai-brightstream-vertex-ai/) — multi-agent architecture patterns relevant to the AI narrative pipeline
- [Building an AI-Friendly Codebase](/posts/building-ai-friendly-codebase-documentation-real-time-claude-md-creation-journey/) — the CLAUDE.md-driven development approach used across this project
- [Building Production-Grade Testing Infrastructure](/posts/building-production-grade-testing-infrastructure-playwright-case-study/) — testing patterns that apply to dashboard components

