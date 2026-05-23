---
title: "Nuclear Option Day: Validator Rewrite, 63 New Packs, 414 Plugins"
description: "Rewrote the universal validator from scratch to match Anthropic's 14-field spec, generated 63 SaaS packs, scored every skill in the catalog, and eliminated all D/F grades. 40+ commits in one day."
date: "2026-03-21"
tags: ["claude-code", "architecture", "automation", "release-engineering", "ai-agents", "typescript"]
featured: false
---
Some days you file tickets. Some days you refactor a module. March 21st was not one of those days.

Forty commits across claude-code-plugins. A complete validator rewrite. 63 new SaaS packs generated. Gold standard documentation across every Jeremy plugin. A compliance pipeline that ran until zero D/F grades remained. The marketplace went from ~350 plugins to 414.

This was the nuclear option. Rip out the old validator, replace it with one built to Anthropic's 2026 spec, then score every single skill against it. Fix everything that fails. Ship it.

## Universal Validator v5.0

The validator had been patched too many times. Every quality sweep — the [7-check audit](/posts/content-quality-war-7-check-audit-across-340-plugins/), the [130-stub blitz](/posts/marketplace-quality-blitz-130-stubs-4300-warnings/), the [design tokens alignment](/posts/design-tokens-and-validator-parity-marketplace-foundations/) — added checks, adjusted thresholds, bolted on edge cases. The result was a validator that worked but couldn't be reasoned about. Nobody could tell you exactly what "valid" meant without reading 400 lines of conditional logic.

Anthropic published their 2026 plugin specification with 14 required fields. Not 12. Not "12 plus 2 optional that everyone treats as required." Fourteen. Defined, typed, documented.

The old validator checked some of them. Missed others. Had extra checks that didn't map to any spec field. A plugin could pass marketplace validation and fail when Claude Code loaded it. A valid plugin could fail marketplace checks. Both happened regularly. Both eroded trust.

v5.0 is a rewrite, not a refactor. The entire validation surface maps 1:1 to Anthropic's schema registry. Fourteen fields. Each one has a type check, a presence check, and a format check. Nothing else.

```typescript
// Anthropic 2026 Plugin Schema — 14 required fields
interface PluginSchema {
  name: string;           // kebab-case, unique across registry
  version: string;        // semver, no build metadata
  description: string;    // 20-200 chars, no markdown
  author: string;         // GitHub username or org
  license: string;        // SPDX identifier
  type: PluginType;       // "agent" | "hook" | "slash-command" | "mcp-server"
  entrypoint: string;     // relative path to main file
  permissions: string[];  // scoped capability declarations
  tags: string[];         // 1-5 taxonomy tags
  compatibleWith: string; // semver range for Claude Code version
  skillCount: number;     // total skills in plugin
  documentation: string;  // relative path to SKILL.md
  repository: string;     // GitHub URL
  checksum: string;       // SHA-256 of packaged artifact
}
```

The old validator had checks scattered across three files with shared mutable state between validation passes. The new one is a single function. Feed it a plugin manifest, get back a typed result with field-level errors. No shared state. No conditional paths based on plugin type. Every plugin type validates against the same 14 fields.

### Plugin-as-Unit Validation

The bigger architectural change: validation now runs at the plugin level, not the skill level.

Previously, each SKILL.md was validated independently. A plugin with 10 skills got 10 validation runs. This made sense when skills were the atomic unit. But plugins are what users install. A plugin where 9 out of 10 skills pass and 1 fails is still a broken plugin.

v5.0 treats the plugin as the unit. All skills within a plugin are validated together. The plugin passes or fails as a whole. The rubric scoring reflects the aggregate — one weak skill drags the entire plugin's grade down.

This changes incentives. Before, you could have a plugin with mostly-good skills and one stub nobody noticed. Now that stub is visible in the plugin's overall grade. Fix all of them or live with the score.

### Removing Legacy Validators

The rewrite also killed the old code. Not deprecated. Removed. `validate-skill.ts`, `validate-pack.ts`, `schema-compat.ts` — three modules that had been "temporary" for months. Each had callers. Each had tests. All of it went. Single source of truth means one validator, one set of tests, one place to look when something breaks.

## 63 New SaaS Packs

While the validator was being rewritten, the catalog was growing.

63 new SaaS integration packs hit the marketplace, bringing the total from 42 to 105 pack directories. These aren't stubs — each pack contains skills for a specific SaaS product with real integration patterns, authentication flows, and API examples.

The marketplace catalog jumped from ~350 to 414 total plugins. 63 packs in one batch. Generated, validated against the new v5.0 schema, graded, documented.

The generation pipeline is the same Vertex AI infrastructure from the [batch processing work](/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/), but tuned for SaaS pack structure. Each pack gets:

1. A plugin manifest with all 14 fields populated
2. Skills targeting the SaaS product's core API surface
3. Authentication skill for the product's auth method (OAuth, API key, JWT)
4. Reference files with real API examples, not placeholders
5. A SKILL.md meeting gold standard documentation requirements

The 63 packs shipped in a single PR alongside the catalog update. Every one passed v5.0 validation. That's the point of rewriting the validator first — you build the gate before you flood the pipeline.

### B-Grade to A-Grade Upgrades

19 skills across 7 existing SaaS packs had B grades under the new rubric. Same pattern every time: adequate code, thin documentation. Each one got expanded methodology sections, real-world usage examples, and edge case docs. No code changes — the skills worked fine. They just needed to explain themselves better. That kind of targeted remediation is only possible when the grading system is transparent.

## Gold Standard Documentation

The validator rewrite exposed another gap. The 13 plugins I personally maintain — my own tools, built for my own workflows — had inconsistent documentation. Some had gold standard docs. Some had whatever I'd written at 2am the day I shipped the feature.

That inconsistency is worse when it's the marketplace author's own plugins. If the person running the platform can't be bothered to document their own tools properly, what signal does that send?

All 13 remaining Jeremy plugins got gold standard documentation suites. Each one now includes:

- **SKILL.md** — Full skill descriptions with invocation examples
- **PRD** — Product requirements document defining what the plugin does and why
- **ARD** — Architecture requirements document covering design decisions
- **References** — Working code examples for every major capability

The firebase, firestore, and vertex-agent-builder plugins got dedicated passes. These are the most-used and most complex Jeremy plugins — they touch production infrastructure and multi-agent orchestration. Their docs had fallen behind their implementations by multiple feature cycles.

The validator's source-of-truth documentation was updated too. Gold standard requirements — PRD, ARD, references — are now enforced in validation, not just described in a wiki page. Claim gold standard compliance and the validator checks for the actual files.

## The Compliance Pipeline

Here's where it all connects.

New validator. New grading rubric. 414 plugins. Run the validator against every single one. See what breaks.

The first pass was ugly. The stricter 14-field schema caught plugins that had passed the old validator for months. Missing `compatibleWith` fields. Tags that didn't match the taxonomy. Descriptions over 200 characters. Checksums that were never populated.

The compliance pipeline ran in two rounds:

**Round 1** — Automated fixes for deterministic violations. Missing fields with obvious defaults (license defaults to MIT for community plugins, checksum gets computed from the artifact). Tag normalization against the taxonomy list. Description truncation with manual review for anything that lost meaning.

**Round 2** — Manual fixes for judgment calls. Plugins with ambiguous types (is this an agent or a slash command?). Skills with documentation that technically existed but was too thin to pass the new minimum. Grade boundaries where a plugin sat at D+ and needed specific improvements to reach C.

After two rounds: zero D grades. Zero F grades. Every plugin in the 414-plugin catalog passes v5.0 validation. The grade distribution shifted hard toward A and B, with C being the floor.

```
Grade Distribution (414 plugins)
  A: 187  (45.2%)
  B: 156  (37.7%)
  C:  71  (17.1%)
  D:   0  (0.0%)
  F:   0  (0.0%)
```

That's the result of running strict validation and actually fixing what fails. Most compliance efforts stop at the report. This one ran until the report was clean.

## Mass Migration: Tags and Compatibility

The compliance pipeline found 1,412 skills missing `tags` and `compatibleWith` fields. Both exist in the Anthropic spec. Both are checked by v5.0. Neither existed in the skills.

A mass migration added both fields to all 1,412 skills. Tags pulled from each skill's category via keyword extraction. `compatibleWith` set to the current Claude Code semver range. Infrastructure work that nobody sees — until Claude Code ships a breaking change and the marketplace can filter by compatible version.

## Fluff Detection

The compliance rounds caught structural problems. They didn't catch content problems. A description that says "This powerful skill leverages advanced AI capabilities to supercharge your workflow" passes every structural check. It also says nothing.

The fluff detector scans prose fields for low-signal patterns: superlative stacking, circular definitions, passive hedging, template artifacts that survived generation. It flagged 89 skills. Each got its prose rewritten. The skill that "leverages advanced AI" now says "extracts named entities from unstructured text using few-shot prompting."

Fluff detection isn't validation. It's a linter for marketing damage. Runs as a warning, not an error. But it catches the content rot that makes a marketplace feel like a SEO farm.

## Pro Tier Launch

All of this quality infrastructure feeds the Pro tier, which also launched today. The Pro landing page and nav link went live with two features: a CLI performance benchmark suite (plugin load time, execution latency, memory footprint — published per plugin) and a freshie inventory system that surfaces recently-updated plugins in the marketplace.

The benchmarks matter most. Plugin performance has been a black box — install and hope it doesn't slow down startup. Now there's data. A plugin that adds 200ms to startup time shows that number on its marketplace page.

## The Day in Numbers

- 40+ commits to claude-code-plugins
- 1 validator rewritten from scratch (v5.0, Anthropic 14-field spec)
- 63 SaaS packs generated (105 total pack directories)
- 414 total plugins in the marketplace catalog
- 13 Jeremy plugins brought to gold standard documentation
- 1,412 skills migrated with tags and compatibility fields
- 19 skills upgraded from B to A grade
- 0 D/F grades remaining after compliance remediation
- 89 skills de-fluffed
- 3 legacy validator modules deleted

Outside claude-code-plugins: nixtla upgraded all 35 skills to A grade under the new rubric. cad-dxf-agent had minor doc fixes. But the story of March 21st is the plugin marketplace. Everything else was a footnote.

## Why One Day

This wasn't 40 independent decisions. It was one decision with 40 consequences.

The decision: rewrite the validator to match Anthropic's spec exactly. Everything else follows. If you have a new validator, you have to run it. If you run it, you have to fix what fails. If you're fixing things, you might as well fix everything. If you're fixing everything, you might as well generate the 63 packs you've been planning and validate them too.

The nuclear option works when you've been accumulating the knowledge of what needs to change. The [content quality war](/posts/content-quality-war-7-check-audit-across-340-plugins/) built the audit tooling. The [quality blitz](/posts/marketplace-quality-blitz-130-stubs-4300-warnings/) built the batch remediation pipeline. The [design tokens work](/posts/design-tokens-and-validator-parity-marketplace-foundations/) identified the spec drift. Today was execution day. All the infrastructure was already in place. The validator rewrite was the trigger. Everything else was the blast radius.

---

## Related Posts

- [Content Quality War: 7-Check Audit Across 340 Plugins](/posts/content-quality-war-7-check-audit-across-340-plugins/) — The audit tooling that made compliance remediation possible at scale
- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/posts/verified-plugins-program-quality-signal-for-the-marketplace/) — The rubric and badge tier system that the v5.0 validator now enforces
- [Design Tokens and Validator Parity: Marketplace Foundations](/posts/design-tokens-and-validator-parity-marketplace-foundations/) — The previous validator alignment work that revealed the need for a full rewrite
