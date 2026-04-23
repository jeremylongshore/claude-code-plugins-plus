---
title: "Pre-Warmed Narratives, Stat Digests, and a Community PR"
description: "Pre-warming AI narratives so viewers never see spinners, feeding structured stat digests into the prompt so narratives quote real numbers, and a contributor shipping three plugins to the claude-code-plugins marketplace."
date: "2026-04-17"
tags: ["braves-booth", "llm", "claude-code-plugins", "open-source", "release-engineering"]
featured: false
---
Two repos, two small wins.

## Braves Booth: Kill the Spinner

The dashboard generates AI narratives about batters and pitchers in real time. That's expensive—Groq Llama 3.3 70B takes 2–3 seconds per narrative—and it was blocking paint. Viewers opening the page mid-broadcast saw spinners.

The fix was already half-built. The event bus already emits `game-discovery` (when the lineup is set), `batter-change`, and `pitcher-change` events. The concurrency pool was in place. The narrative cache existed. So: pre-generate everything the moment you know the game state. On `game-discovery`, warm narratives for the full lineup vs the opposing starter. On `batter-change`, pre-generate for on-deck and in-hole. On `pitcher-change`, re-fetch for all visible batters.

No more spinners. Paint time is cache-hit speed. On-demand generation is fallback-only.

## Narratives Need Numbers

The old prompts were generic: "Good hitter." The new ones are specific because they have data.

Built a `stat-digest-builder` that pulls season-to-date splits, last-7-days splits, opposing-pitcher matchup history, and recent game context, packs it into structured JSON, and feeds it to the narrative prompt. The LLM now quotes actual numbers: "3-for-12 against lefties this season, .315 in last 7 games."

One gotcha: the digest builder was pulling from a 5-minute cache that expired mid-game, producing stale narratives. Fix: fetch fresh for input, cache only the output.

```typescript
type StatDigest = {
  seasonToDate: { avg: number; ops: number; vsLhp: Splits; vsRhp: Splits };
  last7Days: Splits;
  matchup?: { pa: number; hits: number; hr: number; kPct: number };
  recent: { streak: string; last5: GameLine[] };
};
```

Cache what you output, not what you input—especially when the input is a time-varying signal.

## claude-code-plugins: Community Ship

@vdk888 from Bubble Invest shipped three production-tested plugins to the marketplace:

- **`local-tts`** — Offline text-to-speech via VoxCPM2. 30 languages, voice design, voice cloning. Apache-2.0.
- **`security-audit`** — Five-module security audit for Claude Code agents. Python stdlib only. MIT.
- **`boycott-filter`** — Personal brand boycott list and Chrome extension. MIT.

All three packaged with `marketplace.json` per contributor docs. Two are registered in the marketplace index. `security-audit` is in security review (routine, nothing alarming).

The interesting part isn't the plugins. It's the security review. Original PR requested broad `Bash(*)` permissions. We tightened it to specific patterns needed for model download and inference. The contributor was responsive. That's the move: external contributions only scale if review is actionable and maintainers act on feedback. Both sides did here.

Also fixed docs that day—plugin/skill/agent counts were stale, feature table had wrong repo slugs, and we promoted web-analytics to "Killer Skill of the Week" with Umami + MCP details in the description.

## The Thread

Two different repos, one theme: build the scaffolding so the next thing is easier. Pre-warming eliminates the UI problem. Stat digests eliminate the generic-prompt problem. External contributions eliminate the "we ship everything" bottleneck. Small edges compound.

## Related Posts

- [Collaboratively Shaped Roadmap](/posts/collaboratively-shaped-roadmap/)
- [AI Code Review Without Context: Blind Test](/posts/ai-code-review-without-context-blind-test/)
- [AI-Assisted Technical Writing Automation Workflows](/posts/ai-assisted-technical-writing-automation-workflows/)

