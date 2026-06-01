---
title: "Verified Plugins Program: Building a Quality Signal for the Marketplace"
description: "A plugin marketplace without quality signals is a junk drawer. The Verified Plugins Program adds a 100-point rubric, automated validation, and badge tiers to fix that."
date: "2026-03-09"
tags: ["web-development", "architecture", "ci-cd", "claude-code", "automation"]
featured: false
---
A plugin marketplace without quality signals is a junk drawer.

You can have 900 plugins. You can have keyword filtering, install buttons, and a blog. But if a user can't tell the difference between a polished tool and something someone pushed once and abandoned, your marketplace is noise. This week I built the system that fixes that.

## The Problem with Plugin Discovery

The claude-code-plugins marketplace had grown fast. Hundreds of plugins across agents, hooks, slash commands, and MCP servers. The explore page worked. Keyword filtering landed in PR #321. Install counts were visible.

But there was no quality signal.

A plugin with comprehensive documentation, error handling, and active maintenance looked identical to one with a two-line README and no tests. Users had to click into each plugin, read the source, and make their own judgment. That doesn't scale.

## The Verified Plugins Program

PR #326 introduced a structured quality evaluation system. Not a vague "editor's pick" badge. A 100-point rubric with transparent criteria across five categories:

```
Documentation      0-20 points
Code Quality       0-20 points
User Experience    0-20 points
Maintenance        0-20 points
Security           0-20 points
```

Each category has specific checkpoints. Documentation means a real README, usage examples, and configuration docs — not just a title. Code Quality checks for error handling, input validation, and TypeScript types. Security looks at permission scoping and whether the plugin requests more access than it needs.

### Badge Tiers

The score maps to four tiers:

| Tier | Score | Badge |
|------|-------|-------|
| Bronze | 40-59 | Meets baseline quality |
| Silver | 60-79 | Above-average quality and docs |
| Gold | 80-89 | Excellent across all categories |
| Platinum | 90-100 | Best-in-class, actively maintained |

Below 40, no badge. That's the point. The absence of a badge is itself a signal.

### Automated Validation

The rubric isn't just a checklist for humans. Parts of it run automatically. Does the plugin have a README over 200 words? Does it export proper TypeScript types? Does the `package.json` include a license field? These are binary checks that a script can evaluate without human judgment.

The manual review layer handles the subjective criteria: Is the documentation actually helpful? Does the error handling cover real failure modes? Is the permission scope justified?

This split — automated baseline, manual quality layer — means plugins can get instant feedback on fixable issues while still requiring a human to sign off on the badge.

## The Marketplace Professionalization Sprint

The Verified Plugins Program was the capstone of a week-long push to make the marketplace a real product. Here's what else shipped:

**Repo housekeeping (#319)** — Pruned empty categories, fixed plugin counts, added GitHub topics. The kind of work that isn't glamorous but stops users from clicking into a category and finding nothing.

**CONTRIBUTING.md + SEO (#320)** — An open-source contribution guide and structured data for search engines. If you want community contributions, you need to tell people how to contribute. Schema.org markup means Google understands the site structure.

**Keyword filtering (#321)** — The explore page got real-time filtering. Type "docker" and see only plugins related to Docker. Simple feature, but it dropped the time-to-relevant-plugin from "scroll and scan" to "type and click."

**UX improvements (#322)** — Install buttons on the explore page cards. Agent and hook count stats visible at a glance. Version display fixed. Small things that compound.

**Compare Marketplaces page (#323)** — A competitive positioning page. If someone googles "claude code plugin marketplace," they should find us and understand why this one matters.

**Blog with Astro content collections (#324)** — The marketplace itself now has a blog. Changelog posts, plugin spotlights, ecosystem updates. Built with Astro's content collections, which is worth discussing on its own.

## Astro Content Collections Migration

PR #325 converted 11 playbooks from static pages to Astro content collections. This is the kind of refactor that looks boring in the diff but changes how the site works.

Before: playbooks were individual `.astro` files with frontmatter baked into the component. Adding a new playbook meant creating a new file, copying the layout boilerplate, and hoping you matched the structure of the others.

After: playbooks are Markdown files in `src/content/playbooks/` with a Zod schema validating the frontmatter. Adding a new playbook means creating a Markdown file. The schema enforces required fields. The layout is automatic.

```typescript
const playbookSchema = z.object({
  title: z.string(),
  description: z.string(),
  category: z.enum(["getting-started", "advanced", "integration"]),
  order: z.number(),
  lastUpdated: z.date(),
});
```

The blog section (#324) uses the same pattern. Astro content collections give you type-safe content with build-time validation. If a blog post is missing a required field, the build fails. Not at runtime. At build time. That's the right failure mode.

## IntentCAD: Quiet Progress

While the marketplace was getting its professionalism upgrade, IntentCAD's PDF-to-DXF converter got tighter. Better line detection. Improved text positioning. Cleanup of unused code like the `_STANDARD_LINETYPES` dictionary that was defined but never referenced.

The README got a full rewrite for v0.9.0, positioning IntentCAD as a "Drawing Intelligence Platform" rather than just a converter. The gist audit followed the standard operator pattern.

Not flashy work. But the PDF-to-DXF pipeline is the core value proposition of IntentCAD. Every fidelity improvement means fewer manual corrections for users importing legacy drawings.

## Why Quality Signals Matter

The plugin marketplace is at the stage where quantity is no longer the bottleneck. There are enough plugins to be useful. The bottleneck is now trust. Can I install this and expect it to work? Will it break my workflow? Is anyone maintaining it?

Badge tiers answer those questions at a glance. Platinum means someone reviewed it, the automated checks passed, and it scored 90+ across documentation, code quality, UX, maintenance, and security. No badge means it hasn't been evaluated — or it was evaluated and didn't pass.

This is the difference between a marketplace and a directory. A directory lists things. A marketplace helps you choose.

---

## Related Posts

- [Scaling AI Batch Processing with Vertex AI Gemini](/blog/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) — Earlier infrastructure work that built the plugin catalog
- [Production Release Engineering: Shipping v4.5.0](/blog/production-release-engineering-v450/) — Automated release workflows for the marketplace
- [Three Projects, Two Reverts, One Day](/blog/three-projects-two-reverts-one-day/) — The previous week's marketplace work including domain migration
