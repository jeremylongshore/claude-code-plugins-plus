---
title: "Mobile Fixes, Crypto Upgrades, and Killer Skills"
description: "Fixing overlapping cards at 480px, upgrading all 25 crypto skills to A-grade, and launching the Killer Skills spotlight — a lighter day with real impact."
date: "2026-03-11"
tags: ["web-development", "claude-code", "devops", "firebase"]
featured: false
---
Your marketplace looks great on a 1440px monitor. Nobody uses a 1440px monitor.

March 11th was a lighter day — five commits instead of the usual fifteen. But lighter doesn't mean shallow. A mobile UX bug that had been annoying me for a week finally got fixed. Every crypto skill in the marketplace passed quality review. And a new homepage section started turning the marketplace into something people actually want to come back to.

## Cards Don't Stack Themselves

The `/explore` page had a problem at 480px. The plugin cards overlapped. Not dramatically — just enough to make the install buttons unclickable and the descriptions unreadable. The kind of bug that doesn't show up in desktop testing and makes mobile users bounce.

The root cause was the grid. The responsive breakpoints jumped from a two-column layout straight to single-column at 320px, with nothing in between. At 480px — the exact width of most phones held vertically — the cards were trying to fit two across but didn't have enough room. They'd render, overflow, and stack on top of each other.

The fix in PR #340 was straightforward:

```css
@media (max-width: 480px) {
  .skills-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .filter-bar {
    flex-direction: column;
    gap: 0.5rem;
  }
}
```

Single column at 480px. The filter bar also needed its own treatment — the horizontal button row was wrapping awkwardly on narrow screens, so it goes vertical. Small change. Big difference in usability.

## 25 Crypto Skills, Zero Warnings

PR #339 was a full quality pass on every crypto-related skill in the marketplace. Twenty-five plugins covering price tracking, wallet analysis, DeFi protocols, and exchange integrations. All twenty-one that could hit A-grade did. Zero warnings.

This wasn't cosmetic. The audit touched real problems:

- **Broken API endpoints.** Several skills were pointing at deprecated exchange APIs. CoinGecko changed their v3 endpoint structure. Binance deprecated a public ticker route. These skills would silently fail and return nothing.
- **Stale provider references.** Some plugins referenced providers that had rebranded, merged, or shut down entirely. The code still ran but returned confusing error messages.
- **Missing error handling.** The original implementations treated API calls as infallible. Network timeout? Crash. Rate limited? Crash. Invalid token symbol? You guessed it.

Every skill now validates inputs, handles rate limits gracefully, and points at current API endpoints. The kind of work that's invisible to users until the moment it saves them from a broken experience.

## Killer Skills Spotlight

PR #341 added the most visible change: a curated **Killer Skills** section on the homepage. Instead of dumping users into a grid of 900+ plugins and hoping they find something good, the homepage now surfaces the best ones.

This isn't algorithmic. It's editorial. I pick the skills that are genuinely excellent — well-documented, well-tested, solving real problems — and feature them prominently. Think of it as an opinionated "start here" list.

The same PR added an email signup form and a footer redesign. The signup captures interest for a newsletter that'll announce new verified plugins and marketplace updates. The footer got cleaned up to match the rest of the visual refresh that's been rolling out over the past two weeks.

## Firebase Deploy: Split Your Targets

Quick hit. The Firebase deploy was failing with a `serviceusage.services.use` permission error. The monolithic deploy command was trying to push hosting and functions in a single operation, and the service account didn't have blanket permissions across both.

The fix: split the deploy into separate targets. Hosting deploys with hosting permissions. Functions deploy with functions permissions. Each target gets the minimum scope it needs.

```bash
# Before (fails)
firebase deploy

# After (works)
firebase deploy --only hosting
firebase deploy --only functions
```

This is a Firebase footgun that bites everyone exactly once. If your deploys suddenly break after tightening IAM roles, check whether you're deploying everything at once. You probably are.

---

Five commits, four meaningful improvements. Not every day needs to be a marathon.

### Related Posts

- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/posts/verified-plugins-program-quality-signal-for-the-marketplace/)
- [Three Projects, Two Reverts, One Day](/posts/three-projects-two-reverts-one-day/)
- [Scaling AI Batch Processing: Enhancing 235 Plugins with Vertex AI Gemini on the Free Tier](/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/)
