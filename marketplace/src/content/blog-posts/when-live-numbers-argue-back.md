---
title: "When Live Numbers Argue Back"
description: "Live data surfaces bugs static builds never could. The jeremylongshore.com rebuild caught two in production."
date: "2026-08-02"
tags: ["nextjs", "web-development", "debugging", "release-engineering"]
featured: false
canonical: "https://startaitools.com/posts/when-live-numbers-argue-back/"
---
jeremylongshore.com moved from a Ruby/Linkyee static-site generator to a Next.js 15 hub (App Router, standalone, Tailwind v4, TypeScript) with live data over ISR in a single day. Same-day arc:

PR #22 landed the full rebuild with CI green and visual sign-off. The site went live on a Next.js container, pipeline end to end verified. PR #23 caught the first bug: the Umami analytics fetcher was sending `type=url` to the `/metrics` endpoint, which returned a 400. The instance actually needed `type=path` for a 200. This endpoint was flagged during the data-layer port as unverified. The first integration test against the live VPS caught it immediately. PR #24 deleted the entire Ruby/Linkyee stack the same day as cutover (scaffold.rb, Gemfile, plugins, build.sh, 4000 lines gone). No dual-stack debt.

Then two more issues surfaced before shipping further. PR #25 reordered the homepage project grid to lead with Claude Code Plugins, Bob's Big Brain, Intent Eval Platform, and ScorecardEcho as flagship projects. PR #26 caught a real bug: the new cards were rendering `star 0` badges for repos with zero GitHub stars. On a page whose whole voice is "claim, then the live count, then the link," a zero-star badge is proof of the opposite. The fix was one line: only render the badge when the count is greater than zero. Six more PRs followed for profile updates, IRSB promotion, content passes, dark mode, and final polish. Production Lighthouse score ended at 85/100/100/100. Epic closed.

The connective thread: a static site can only be wrong about things that were wrong at build time. The moment jeremylongshore.com started pulling live numbers (Umami views, GitHub stars) instead of hardcoding them, it started being able to be wrong in *new ways*, live, in production. Both bugs that shipped that day are exactly that class of bug. Not "we wrote the wrong code," but "we wrote code that assumed the live number would always look like proof, and it didn't."

Intent-os kept landing pieces of the estate-wide Buzz notification migration. A watchdog got an owner-neutral failure trap. The repository-portfolio collector moved off the old notify-lib code path. Semantically drifted Buzz alerts got rejected before they could reach the channel.

bobs-big-brain-umbrella regenerated its live system-dependency-graph stats and filed a new "truth-maintenance" epic (PR #75). claude-code-plugins shipped a neobrutalist rebrand of the plugin marketplace (zero border-radius, monospace type, one clear call-to-action per page) and fixed a version-number bug: the homepage was resolving versions by counting directories, which is fragile. Now it searches instead.

## Related Posts

- [The Version Number That Only Existed on the Client](https://startaitools.com/posts/the-version-number-that-only-existed-on-the-client/) is the preceding day, same theme: a system telling the truth about its own live state instead of a label.
- [The Ghost in the Catalog](https://startaitools.com/posts/the-ghost-in-the-catalog/) covers the same class of failure from the other direction: a claim that looked live but was not.
