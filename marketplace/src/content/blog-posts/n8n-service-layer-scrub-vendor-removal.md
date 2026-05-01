---
title: "Service-Layer Scrub: Removing n8n from Intent Solutions Landing"
description: "Vendor removal isn't one edit. It's a service-layer scrub across hero copy, stack comparisons, and 81 internal links—all in one PR to keep the story coherent."
date: "2026-04-26"
tags: ["web-development", "devops", "claude-code", "automation"]
featured: false
---
Removing a vendor from your positioning isn't a single find-and-replace. It's a service-layer scrub: hunt every passive mention, rewrite the comparison surface, fix every internal link, and ship it all in one coherent commit so the story stays intact.

On the intent-solutions-landing repo, n8n needed to come out. The landing site had positioned it alongside Vertex AI in the automation stack, but the current narrative no longer claimed Jeremy actively uses it. Passive mentions lingered—stale context that muddied the signal.

I started by porting 15 field-notes posts from a stale PR. Fresh content first, then the scrub. The work flowed in three phases: service surfaces, link rewrite, and verification.

**Service surfaces.** The `/automation` hero section featured a three-way comparison: n8n, Vertex AI, and Zapier. I rewrote it to remove n8n entirely, collapsing the comparison down to the two tools Jeremy actually uses. The FAQSection and ProjectShowcase components each had passive n8n mentions—removed. The `content.config.ts` file held placeholder pricing text for n8n diagnostics tool; gone. These weren't links—they were *surface truth*. If the landing says Jeremy uses n8n, but the about page doesn't mention it, the visit lands in a contradiction.

**Link rewrite.** The port of 15 posts changed the content structure: they lived in `/posts/` on the old branch, but needed to resolve to `/field-notes/` on the new one. I ran a sed pass across the repo to rewrite canonical in-body links:

```bash
find . -name "*.astro" -o -name "*.ts" -o -name "*.md" | xargs sed -i 's|/posts/\([^/]*\)/|/field-notes/\1/|g'
```

81 link fixes, zero false positives. The build verified every internal path resolved correctly.

**Verification and commits.** Hugo built clean—72 pages, no schema validation errors. I split the work into 7 logical commits: beads cleanup, feature ports, the n8n scrub, link rewrites, bug fixes from code review, CLAUDE.md improvements, and beads sync. A minor wrinkle: the port accidentally swept the 15 new posts into commit 1. I split them cleanly and pushed again.

**PR #16** shipped with all changes coherent. One PR, one story: "We're consolidating around Vertex AI + Zapier; n8n is gone."

The lesson: vendor removal is a verb, not a typo fix. A good service-layer scrub owns its scope—surface rewrites, link integrity, and the commit narrative that proves nothing got missed.

---

## Related Posts

- [Claude Code + Astro: Automated Content Sync](https://startaitools.com/posts/claude-astro-content-sync/) — How to keep internal links coherent across structure changes
- [Git Commit Hygiene: One Story Per PR](https://startaitools.com/posts/git-story-discipline/) — Why logical commits matter for narrative integrity

