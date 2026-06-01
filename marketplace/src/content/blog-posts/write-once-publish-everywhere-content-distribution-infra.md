---
title: "Write Once, Publish Everywhere: Building Content Distribution Across Three Sites"
description: "Three sites now share content through automated pipelines: Hugo to Astro backfill, cross-repo plugin sync with repository_dispatch, and a CodeRabbit-caught no-op filter."
date: "2026-03-25"
tags: ["automation", "architecture", "ci-cd", "web-development", "claude-code"]
featured: false
---
Three websites. One hundred blog posts. Thirty-one field notes. Four plugin repos. All synced automatically. None of it existed yesterday.

March 25th was about content distribution infrastructure. Not writing content — moving it. The problem: Intent Solutions runs three public-facing sites (startaitools.com, tonsofskills.com, intentsolutions.io) plus a plugin marketplace. Each site had its own content silo. Posts written here never appeared there. Plugin updates in source repos required manual marketplace syncs. The content existed. The distribution didn't.

Eight commits across two primary repos fixed that.

## 100 Posts: Hugo to Astro

tonsofskills.com is an Astro marketplace. startaitools.com is a Hugo blog. They use different content formats, different frontmatter schemas, different directory structures. Hugo uses TOML frontmatter with `+++` delimiters. Astro expects YAML with `---` delimiters. Hugo puts posts in `content/posts/`. Astro wants them in `src/content/blog/`.

The backfill pulled 100 posts from the Hugo site into tonsofskills.com's new blog section. This isn't an RSS embed or an iframe. It's actual content transformation — frontmatter conversion, path rewriting, image reference updates.

The section launched as "Blog" and got immediately renamed to "Work Diary." The name matters. A marketplace blog competes with the source blog for SEO. A work diary is a different content type — it's the builder's log, not the tutorial. Different intent, different audience, same underlying content.

The `/pro` page also got deactivated with a 301 redirect to homepage. One less page to maintain, one less nav link to confuse visitors. The Pro nav slot got replaced with the Work Diary link. Every page on a site should earn its place.

## 31 Field Notes: intentsolutions.io Gets Content

The corporate site at intentsolutions.io had the opposite problem — no content section at all. A services company without published thinking is a brochure. Brochures don't rank and they don't build trust.

The fix was a Field Notes section with 31 curated posts backfilled from startaitools.com. Not all 100. Thirty-one, filtered by professional tags. The corporate site gets the architecture posts, the production engineering posts, the CI/CD deep-dives. It doesn't get the daily work diary entries.

The implementation touched six files:

- `content.config.ts` — Astro content collection with field-notes schema
- Listing page with card-slate design and JSON-LD structured data
- Detail pages with prose styles and canonical URL override
- RSS feed at `/field-notes/rss.xml` via `@astrojs/rss`
- Nav updates across desktop, mobile menu, and footer
- `Layout.astro` modified to accept optional canonical prop

The canonical URL override is the key detail. When the same post lives on both startaitools.com and intentsolutions.io, Google needs to know which is the original. The canonical prop lets each field note point back to the source URL, avoiding duplicate content penalties while still serving the content on both domains.

A backfill script (`sync-to-intentsolutions.sh`) handles the ongoing sync. Write a post on startaitools.com, run the script, it appears on intentsolutions.io if the tags match.

## CodeRabbit Catches a No-Op Filter

The second intentsolutions.io commit is the small one with the lesson. The field notes listing page had a filter:

```typescript
posts.filter(post => !post.data.featured || post.data.featured !== undefined)
```

This filter does nothing. If `featured` is falsy, the first condition is true. If `featured` is truthy, it's definitely not undefined, so the second condition is true. Every post passes. It's a no-op masquerading as a filter.

CodeRabbit caught it in PR review. Not a human. An AI reviewer. The fix was one line — remove the dead filter. But the pattern is instructive: conditional logic with OR operators where both branches are always true. It's the boolean equivalent of `if (true)`. Easy to write, hard to spot in review, especially when the variable names suggest the filter should be doing something meaningful.

## Cross-Repo Plugin Sync: repository_dispatch

The plugin marketplace at tonsofskills.com lists plugins from four external repos: box-cloud-filesystem, x-bug-triage-plugin, claude-code-slack-channel, and pr-to-prompt. Until today, syncing required manual triggers. Push to a source repo, remember to trigger the marketplace sync, wait for CI, check it landed.

The fix uses GitHub's `repository_dispatch` event. Each source repo got a `notify-marketplace.yml` workflow:

```yaml
on:
  push:
    branches: [main]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.MARKETPLACE_SYNC_PAT }}
          repository: owner/marketplace-repo
          event-type: external-plugin-update
          client-payload: '{"repo": "${{ github.repository }}"}'
```

The marketplace repo's `sync-external.yml` listens for `repository_dispatch` events with that event type. Push to any source repo, the marketplace syncs automatically. No human in the loop.

The x-bug-triage-plugin was the first to use this pipeline. Five skills, four agents, and an MCP server synced to the marketplace on the same commit that deployed the dispatch trigger. box-cloud-filesystem also got re-synced with its latest upstream.

This closes the loop on [the external sync system](/blog/external-plugin-sync-keeping-community-plugins-fresh/) built in January. That system used a cron schedule — daily syncs at midnight. The `repository_dispatch` approach is event-driven. Push to source, marketplace updates in minutes instead of waiting for the next cron window.

## The Distribution Graph

After today, the content flow looks like this:

**startaitools.com** (Hugo, source of truth) publishes daily work diary posts. A subset gets synced to **intentsolutions.io** (Astro, corporate) as field notes, filtered by professional tags, with canonical URLs pointing back to source. The full archive gets synced to **tonsofskills.com** (Astro, marketplace) as the Work Diary section.

Plugin repos push to main. `repository_dispatch` fires. The marketplace syncs within minutes. No cron. No manual triggers.

Three sites. One content pipeline. Zero manual steps after the initial publish.

## The Broader Pattern

Content distribution is a solved problem for media companies. Syndication, RSS, cross-posting APIs — the tooling exists. For small dev shops running three Astro/Hugo sites and a plugin marketplace, the tooling doesn't exist. You build it yourself.

The investment was eight commits across two repos. The return is that every post written on startaitools.com now reaches three audiences automatically, and every plugin update reaches the marketplace without human intervention. The marginal cost of the next post or the next plugin sync is zero.

That's the whole point of infrastructure. You pay once, then it compounds.

---

**Related Posts:**

- [Building External Plugin Sync: Keeping Community Plugins Fresh](/blog/external-plugin-sync-keeping-community-plugins-fresh/) — The January cron-based sync system that today's `repository_dispatch` replaces
- [X Bug Triage Plugin: Zero to v0.4.3 in One Day](/blog/x-bug-triage-plugin-zero-to-v043-one-day/) — The plugin that got its first marketplace sync today
- [Content Quality War: 7-Check Audit Across 340 Plugins](/blog/content-quality-war-7-check-audit-across-340-plugins/) — The content quality standards that the sync pipeline now enforces automatically
