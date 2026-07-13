---
name: brand-voice
description: |
  Applies the team's saved brand profile — voice, messaging, style guide, and
  compliance rules — to marketing copy so every asset reads on-brand instead of
  generic. Use when drafting, editing, or auditing content and a brand profile
  may exist. Trigger with "brand voice", "apply the brand", "stay on-brand", or "/review".
allowed-tools: Read, Write, Glob
argument-hint: '[--brand <name>] [--locale <xx-XX>]'
version: "0.2.1"
author: localplugins <localplugins@proton.me>
license: MIT
compatibility: Designed for Claude Code
tags:
  - branding
  - voice
  - marketing
  - content
  - compliance
---

# Brand Voice

## Overview

Brand Voice loads the team's saved brand profile and applies it so every asset sounds like the team, not like generic AI. It governs voice, messaging, style, and compliance for all content the plugin produces.

The profile is a set of Markdown files the team owns in its own repository.
Four files define the brand: `brand-voice.md` (personality, tone, signature phrases, words to avoid),
`messaging.md` (positioning, value props, personas, boilerplate),
`style-guide.md` (formatting, glossary, product and trademark casing, banned words, inclusive language),
and `compliance.md` (approved claims, prohibited terms, required disclaimers).
This skill is instruction-driven: it reads those files and writes on-brand copy, with no accounts, keys, or network access.

## Prerequisites

- A brand profile in `content/brand/` (default) or `content/brands/<name>/` when a brand is named, optionally with `content/brand/locales/<xx-XX>/` overrides. Create one with `/brand-setup`.
- Read access to the profile files. The skill uses Glob to locate them, Read to load them, and Write to save finished copy.
- No external services. All judgment comes from the profile files, never general opinion.

## Instructions

1. Check for an active brand profile: Glob `content/brand/`, or `content/brands/<name>/` when a brand is named, plus any matching `locales/<xx-XX>/` directory.
2. Read all four profile files. Locale files override the base file of the same name field-by-field.
3. Set the working voice from `brand-voice.md`: personality adjectives, tone, do and don't rules, signature phrases, and the words-to-avoid list.
4. Apply messaging from `messaging.md`: pick the persona and the key message the asset reinforces, and reuse approved value props and boilerplate.
5. Configure the style layer while drafting: formatting rules, glossary terms, exact product and trademark casing, banned words, and inclusive-language rules.
6. Verify compliance against `compliance.md`: use only approved claims, include every required disclaimer, and remove any prohibited term.
7. Run the self-check before returning: confirm no word-to-avoid, no banned word, correct casing, and required disclaimers present. Revise until clean.
8. When no profile is found, tell the user to run `/brand-setup` and offer to proceed with sensible defaults for this run only.

## Output

On-brand text ready to hand to the next step: a channel adapter, a localizer, or the user. When invoked by `/review`, the output is instead a scorecard marking Voice, Style, and Compliance as pass or fix per asset, with a redline that shows the original text, the rule it breaks, and the corrected version.

## Error Handling

| Condition | Behavior |
|-----------|----------|
| No brand profile found | Recommend `/brand-setup`; offer sensible defaults for this run only, clearly labeled |
| Partial profile (some files empty) | Apply what exists; note which dimensions could not be checked rather than guessing |
| Base and locale files conflict | The locale file wins for that market; note the override |
| Source copy conflicts with a brand rule | Follow the rule; flag the conflict for the user instead of silently rewriting meaning |
| A claim cannot be verified against `compliance.md` | Flag it for human review; never invent approval |

## Examples

**Example: apply the brand while drafting**
> /multiply blog-post.md --channels linkedin

The `/multiply` command uses this skill to load the profile, then writes a LinkedIn post that obeys the tone, glossary, and approved claims.

**Example: audit a teammate's draft**
> /review draft.md

Loads the profile and returns a pass/fix scorecard plus a redline for every violation.

**Example: default-mode fallback**
> Write a launch tweet for us

With no profile present, the skill recommends `/brand-setup`, then offers to draft using neutral defaults for this run only.

## Related skills

See also the companion skills `channel-formats` (adapt on-brand copy to each platform) and `transcreation` (adapt it across languages). Brand voice is the content; those skills are the container and the market fit.

## Resources

- [references/applying-the-profile.md](references/applying-the-profile.md) — how to load the files, precedence rules, how each profile field maps to a writing decision, a worked before/after rewrite, and the pre-return self-check.
- [references/edge-cases.md](references/edge-cases.md) — missing or partial profiles, conflicts between files, locale overrides, multi-brand setups, and what to do when a rule and the source collide.
- Profile templates ship in the plugin at `templates/brand/` and are copied into the repo by `/brand-setup`.
