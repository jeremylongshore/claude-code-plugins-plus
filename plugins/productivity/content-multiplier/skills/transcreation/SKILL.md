---
name: transcreation
description: |
  Transforms marketing content across languages and markets through
  transcreation — adapting message, tone, and cultural references instead of
  translating word for word — while honoring per-locale brand rules and a
  do-not-translate glossary. Use when localizing content or when a locale is set.
  Trigger with "transcreate", "localize", "adapt for a market", or "/localize".
allowed-tools: Read, Write, Glob
argument-hint: '--locales xx-XX,yy-YY [--brand <name>] [--back-translation]'
version: "0.2.1"
author: localplugins <localplugins@proton.me>
license: MIT
compatibility: Designed for Claude Code
tags:
  - localization
  - transcreation
  - marketing
  - content
  - internationalization
---

# Transcreation

## Overview

Transcreation adapts content into another language so it feels native, preserving intent, brand voice, and emotional impact rather than translating literally. The wording is reworked; the effect is kept.

Literal translation breaks marketing: idioms fall flat, humor is lost, and register goes wrong.
This skill loads the base brand profile and the target locale's overrides, reworks the copy for that market,
protects do-not-translate glossary terms, and re-checks compliance and channel limits for the new language.
It is instruction-driven and writes localized files, with no accounts, keys, or network access.

## Prerequisites

- Source content to localize and one or more target locales in `xx-XX` form (for example `de-DE`, `ja-JP`).
- The base brand profile plus any `content/brand/locales/<xx-XX>/` overrides. The skill uses Glob and Read to find and load them and Write to save each localized asset.
- The `style-guide.md` glossary section (Product and Trademark Names) for do-not-translate terms, and the locale's `compliance.md` for market-specific rules.

## Instructions

1. Read the base brand files, then read any `locales/<xx-XX>/` overrides. Locale rules win for that market.
2. Adapt, do not translate: rework idioms, humor, and references into locale equivalents, keeping the effect rather than the words.
3. Set the register: choose the correct formality and honorifics for the persona and locale (Sie or du, keigo, tu or usted).
4. Convert locale specifics: units, currency, date and number formats, names, and examples.
5. Protect the glossary: never translate product names, trademarks, or taglines unless the brand supplies a sanctioned translation.
6. Check the channel limit: text expands or contracts across languages, so re-fit each asset with the `channel-formats` spec.
7. Verify compliance against the locale's `compliance.md`: disclaimers and prohibited terms can differ by country.
8. Handle scripts: apply right-to-left rules for Arabic and Hebrew and correct spacing for CJK.
9. When asked, emit a back-translation plus a short note on adaptation choices so a non-native approver can sign off.

## Output

One localized file per asset per locale, mirroring the source filenames under a locale folder (for example `de-DE/linkedin.md`). Each asset is transcreated, glossary-safe, compliance-checked for that market, and re-fitted to its channel limit. When a back-translation is requested, each localized asset is paired with a literal back-translation and an adaptation note for approver sign-off.

## Error Handling

| Condition | Behavior |
|-----------|----------|
| No locale override found | Use the base brand rules; note that no market-specific overrides were applied |
| Glossary term has no sanctioned translation | Keep the source term verbatim; never invent a localized name |
| Compliance rules differ by market | Apply the locale's `compliance.md`; flag any claim that cannot cross the border |
| Text overflows the channel after adaptation | Re-fit with `channel-formats` before writing the file |
| Idiom or joke has no equivalent | Substitute a locally resonant alternative and record the choice in the adaptation note |

## Examples

**Example: localize into two markets**
> /localize post.md --locales de-DE,ja-JP

Loads each locale's overrides, transcreates the post for German and Japanese, protects glossary terms, and writes `de-DE/` and `ja-JP/` versions.

**Example: request a back-translation**
> /localize offer.md --locales fr-FR --back-translation

Produces the French asset plus a literal back-translation and an adaptation note for sign-off.

**Example: localized as part of multiply**
> /multiply brief.md --channels linkedin --locales es-ES

Drafts the LinkedIn asset, then transcreates it for Spanish and re-fits it to the channel limit.

## Related skills

See also the companion skills `brand-voice` (per-locale voice and compliance) and `channel-formats` (re-fit expanded or contracted text to each channel).

## Resources

- [references/transcreation-guide.md](references/transcreation-guide.md) — worked before/after transcreations, formality-by-locale guidance, glossary handling, unit, currency, and date conversion tables, right-to-left and CJK notes, and how to produce a back-translation.
- [references/locale-checklist.md](references/locale-checklist.md) — a step-by-step per-locale checklist and the common failure modes (literal idioms, broken glossary terms, compliance carried across a border, overflowed channel limits).
