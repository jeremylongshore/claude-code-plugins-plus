---
title: "Marketplace Quality Blitz: 130 Stub Files, 4300 Warnings, Zero Excuses"
description: "Replacing 130 empty SKILL.md stubs with real content, fixing 4300+ validator warnings, and shipping automated quality scoring for the plugin marketplace."
date: "2026-03-10"
tags: ["claude-code", "automation", "ci-cd", "web-development", "ai-agents"]
featured: false
---
130 plugins had SKILL.md files that said nothing.

Not bad documentation. Not incomplete documentation. Template stubs. Copy-pasted boilerplate with placeholder text where the actual content should be. A user opening one of these files learned exactly two things: that the file existed and that nobody had bothered to fill it in.

This week I replaced all 130 of them.

## The Stub Problem

When you scaffold a plugin, the generator creates a SKILL.md. That's good practice. But when you scaffold 340 plugins over several months, some of those files never graduate from template to documentation. They sit there with `[Describe your skill here]` blocks, passing existence checks while providing zero value.

The scale was worse than I expected. A quick audit showed 130 out of 340+ plugins had stub SKILL.md files. That's 38% of the marketplace shipping empty documentation. Every one of those plugins was discoverable, installable, and completely undocumented beyond its name.

## Replacing Stubs at Scale with Vertex AI

Manual replacement wasn't an option. Each SKILL.md needs to describe what the skill does, how to invoke it, what parameters it accepts, and what it's good at. Writing 130 of those by hand would take a week of mind-numbing work.

Instead, I used Vertex AI Gemini on the free tier — the same batch processing infrastructure I built for [enhancing 235 plugins](/blog/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) back in October. The pipeline reads each plugin's source code, configuration, and existing metadata, then generates a substantive SKILL.md tailored to that specific plugin.

PR #335 landed all 130 replacements in a single commit. Every file went from boilerplate stub to domain-specific content describing real functionality.

The key constraint: each generated file had to be accurate. A wrong SKILL.md is worse than an empty one because it looks authoritative. The generation prompt included the full plugin source as context, and I spot-checked 20% of the output before merging.

## 4300 Warnings Down to 258

While the stub replacement addressed documentation, the validator was screaming about everything else. 4300+ warnings across the marketplace. Missing metadata fields, incorrect schema versions, undocumented parameters, malformed YAML headers.

PR #337 tackled this systematically. The breakdown:

- **Missing metadata fields** — `author`, `license`, `version` missing from plugin manifests
- **Schema version mismatches** — Plugins referencing outdated config schemas
- **Undocumented parameters** — Functions accepting arguments with no description
- **Malformed headers** — YAML frontmatter with incorrect indentation or missing required keys

4300 warnings to 258. A 94% reduction. The remaining 258 are edge cases that need manual review — plugins with genuinely ambiguous parameter types or deprecated fields that require migration decisions.

This isn't glamorous work. It's the kind of cleanup that makes everything else possible. You can't build automated quality scoring on top of a codebase that throws 4300 warnings.

## The Verification Pipeline

Which brings us to PR #328: automated plugin quality scoring.

The verification pipeline evaluates every plugin against a structured rubric and assigns badge tiers. The [Verified Plugins Program](/blog/verified-plugins-program-quality-signal-for-the-marketplace/) established the rubric. This PR automates the evaluation.

The pipeline handles:

- **Badge scoring** — Automated point calculation across documentation, code quality, and maintenance criteria
- **Shortcut deduplication** — Several plugins had registered identical keyboard shortcuts, causing conflicts on install
- **Verification status tracking** — Each plugin gets a machine-readable verification record

Combined with the stub replacement and validator cleanup, the pipeline can now run against a marketplace where 94% of plugins pass baseline checks. Before this week, the pipeline would have drowned in noise.

## Doctor, Fix Thyself

PR #333 added `--fix` to the `ccpi doctor` command. Before this, `ccpi doctor` would diagnose problems and print a list of things for you to fix manually. Now:

```bash
ccpi doctor --fix
```

Auto-remediates common issues: missing required fields get populated with sensible defaults, malformed config files get reformatted, and deprecated schema references get updated. The flag is intentionally conservative — it only fixes problems with unambiguous solutions. Anything that requires a judgment call still gets flagged for manual intervention.

This is the pattern that makes maintenance scale. You don't ask 340 plugin authors to each fix their own metadata. You build a tool that fixes the 80% of issues that have obvious answers and surfaces the 20% that don't.

## Everything Else That Shipped

The quality blitz touched more than documentation and validation:

- **Light/dark theme toggle** across the marketplace UI. Reads system preference, persists user choice.
- **Automated weekly metrics** — A scheduled job that tracks plugin ecosystem health: total plugins, verified count, average badge score, warning trend.
- **Cross-platform skill headers** (PR #332) — Fixed YAML parser choking on multiline strings in skill definitions. This was breaking plugin installs on Windows.
- **Tutorial notebook overhaul** (PR #338) — All 5 skill tutorial notebooks rewritten to Intent Solutions standards. Consistent structure, working code examples, clear prerequisites.
- **Version bump** — 18 jeremy-owned plugins went from 1.0.0 to 2.0.0, reflecting the breaking changes in SKILL.md format and metadata requirements.

All of this shipped as v4.17.0.

## The Compound Effect

Any one of these changes is incremental. A theme toggle is a weekend project. Fixing validator warnings is janitorial. But stacked together, the marketplace went from a directory with quality problems to a platform with quality infrastructure.

Before this week: 38% of plugins had empty documentation, the validator was unusable due to noise, and quality scoring couldn't run reliably.

After: every plugin has substantive documentation, the validator is actionable, and automated quality scoring runs clean. That's the foundation everything else gets built on.

---

## Related Posts

- [Verified Plugins Program: Building a Quality Signal for the Marketplace](/blog/verified-plugins-program-quality-signal-for-the-marketplace/) — The rubric and badge tier system that this week's automation builds on
- [Scaling AI Batch Processing with Vertex AI Gemini](/blog/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) — The batch infrastructure used to replace 130 stub files
- [Production Release Engineering: Shipping v4.5.0](/blog/production-release-engineering-v450/) — Automated release workflows for the marketplace
