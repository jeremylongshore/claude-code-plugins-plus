# PRD: content-multiplier

**Author:** localplugins
**Date:** 2026-07-12
**Status:** Active

## Problem

Small teams produce one good idea — a blog post, a talk transcript, a launch note — and
then either drop it or spend hours hand-porting it into a LinkedIn post, an X thread, a
newsletter, a caption, and a few languages. Generic AI drafts sound off-brand and drift on
approved claims, so every output still needs a manual voice-and-compliance pass. The cost is
repurposing labor and inconsistent brand voice across channels and markets.

## Target users

| User | Context | Primary need |
| ---- | ------- | ------------ |
| Solo founder / creator | Has one source, wants a week of posts | One command that fans a source out on-brand |
| Small marketing team | Shared brand rules, several channels | Consistent voice + compliance without a human gate on every draft |
| Localization owner | Selling into multiple markets | Transcreation, not literal translation, honoring per-locale rules |

## Success criteria

1. From one source, `/multiply` produces ready-to-paste drafts for each requested channel, each within that channel's length limit.
2. Every generated asset is checked against the saved brand profile (voice, style, compliance) before delivery, with violations surfaced rather than silently shipped.
3. `/localize` adapts content per locale using the do-not-translate glossary and locale compliance rules, with an optional back-translation for sign-off.
4. The plugin runs with no accounts, API keys, or network access — instruction-driven over local files only.

## Functional requirements

- **FR-1:** Load a saved brand profile (`content/brand/` or a named brand, plus locale overrides) and apply it to all generated content.
- **FR-2:** Adapt one source into channel-native formats (LinkedIn, X thread, newsletter, Instagram, YouTube, short video, blog) that obey each channel's spec.
- **FR-3:** Transcreate content across locales, protecting glossary terms and re-checking compliance and channel limits.
- **FR-4:** Gate every draft through a brand-and-compliance reviewer that returns a pass/fix scorecard and a redline.
- **FR-5:** Write copy-paste / schedule-ready files; never auto-post and never access the network.

## Out of scope

- Publishing, scheduling, or posting to any real platform (the calendar is a plan the user executes).
- Fetching sources or reference material from the network.
- Machine translation as a substitute for transcreation.
- Analytics, performance tracking, or A/B testing of published content.
