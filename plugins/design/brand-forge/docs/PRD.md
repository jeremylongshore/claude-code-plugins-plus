# PRD: brand-forge

**Author:** localplugins
**Date:** 2026-07-12
**Status:** Active

## Problem

Small teams and solo builders need on-brand assets — a logo, a launch post, a
letterhead, an occasional hero image — but rarely have a designer on call. The usual
alternatives fail them: SaaS design tools require accounts, uploads, and monthly fees;
raw AI image generators drift off-palette and cannot render text reliably; and copying
a past asset by hand quietly corrupts the brand (a wrong hex, a substituted font).
brand-forge fixes this by generating assets deterministically from a saved brand
profile, keeping the everyday cases (logos, social, docs) fully local and vector, and
isolating the one costly, network-bound case (AI imagery) behind an explicit opt-in.

## Target users

| User | Context | Primary need |
| --- | --- | --- |
| Solo founder | Shipping a launch with no designer | Fast, on-brand logo and social posts without a subscription |
| Small marketing team | Producing recurring campaign assets | Consistent palette and fonts across every export |
| Agency operator | Managing several client brands in one repo | Switch active brand and generate per-brand assets safely |
| Developer / automation | Generating assets in CI or a script | Vector output with no keys or network for the common path |

## Success criteria

1. Every generated vector asset uses only colors declared in `color-system.json` and the fonts in `typography.json`, verified by the `visual-guardian` review pass.
2. The logo, social, and document skills produce a valid SVG with zero network calls and zero required credentials.
3. AI imagery never runs unless both opt-in signals (`BRAND_FORGE_RASTER=1` and a provider key) are present; otherwise the skill offers a vector alternative.
4. All four skills pass the marketplace validator at A-grade (score ≥ 90) with zero errors.

## Functional requirements

- **FR-1:** Generate wordmark, monogram, and favicon SVGs from the active brand profile (generate-logo).
- **FR-2:** Generate platform-sized social templates with editable headline, subhead, and call-to-action zones (generate-social).
- **FR-3:** Generate letterhead, slide, and one-pager document templates with editable title, subtitle, and body zones (generate-doc-template).
- **FR-4:** Generate an AI marketing graphic behind a double opt-in, optionally compositing a vector logo and caption over the raster (generate-graphic).
- **FR-5:** Route every asset through the `visual-guardian` review pass before delivery, and never auto-post or upload output.

## Out of scope

- Hosting, scheduling, or publishing assets to any platform.
- Editing raster pixels — text and logos are always added as vector overlays.
- Designing a brand from taste; the skills execute a profile a human authored.
- Managing font licensing; unavailable fonts fall back to a declared substitute, flagged to the user.
