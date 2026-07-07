# PRD: 000-jeremy-content-consistency-validator

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-07
**Status:** Active

> This PRD describes the product contract — problem, users, success criteria — and holds
> across the multi-agent rebuild scoped in issue #991. Implementation decisions (and their
> planned supersession) live in [`docs/ADR.md`](ADR.md).

## Problem

Messaging drifts apart across the surfaces a project publishes to. The website gets
updated first; GitHub READMEs and internal documentation lag behind — so the public site
says v1.2.1 while the README still says v1.2.0, the site claims "236 plugins" while the
docs say "230+", contact info goes stale in training materials, and the same product is
called a "plugin" on one surface and an "extension" on another. The cost is mixed public
messaging, customer confusion, and internal materials (SOPs, training, sales collateral)
that quietly contradict what the website promises. Finding this drift by hand means
manually diffing dozens of files across three surfaces every time anything changes.

## Target users

| User                                  | Context                                                                      | Primary need                                                           |
| ------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Content manager / marketing owner     | Website is updated first; internal paperwork lags behind                     | Know exactly what to update in the docs to match the live site         |
| Documentation team / technical writer | Pre-release and post-rebrand audits across README, docs site, and changelog  | Version and terminology consistency, with file-and-line fix locations  |
| Open-source maintainer                | README / CONTRIBUTING / docs drift from the published site between releases  | One report listing every file that needs updating, ordered by severity |
| Trainer / internal-ops owner          | Training materials must match current public pricing, features, and contacts | Pre-update validation so materials are revised against current truth   |

## Success criteria

1. Every reported finding carries its source, file path, and line number — no finding
   requires the reader to re-search for where the fix goes.
2. Every discrepancy is severity-classified against the documented classes: Critical
   (conflicting versions, contradictory feature lists, mismatched contact info, broken
   cross-references), Warning (inconsistent terminology, missing information, outdated
   dates), Informational (stylistic and platform-specific variation).
3. A run mutates nothing: no Write, no Edit, no git operations. The only artifact is the
   timestamped Markdown report saved to `consistency-reports/YYYY-MM-DD-HH-MM-SS.md`.
4. Extraction is verified before comparison — at least 3 data points per source — and
   every source pair (website↔GitHub, website↔docs, GitHub↔docs) appears in the
   comparison matrix.

## Functional requirements

- **FR-1:** Auto-discover content sources across three surfaces: any HTML-based website
  (static HTML, Hugo, Astro, Jekyll, WordPress, Next.js/React, Vue/Nuxt, Gatsby,
  11ty/Eleventy, Docusaurus), GitHub repository docs (README, CONTRIBUTING, `docs/`), and
  local documentation directories (`docs/`, `claudes-docs/`, `000-docs/`, `internal/`).
- **FR-2:** Extract structured messaging from each source: version numbers, feature
  claims, product names and taglines, contact information, URLs, technical requirements,
  and terminology.
- **FR-3:** Build a pairwise comparison matrix across all sources and classify each
  discrepancy as Critical, Warning, or Informational.
- **FR-4:** Apply the trust hierarchy — website (most authoritative) > GitHub
  (developer-facing) > local docs (internal) — when recommending which side changes, with
  the update flow website → GitHub → local docs.
- **FR-5:** Generate a timestamped read-only Markdown report: executive summary,
  per-pair comparison tables, terminology consistency matrix, and prioritized action
  items with file paths and line numbers.

## Out of scope

- **Fixing anything.** The validator never modifies files and never auto-remediates; it
  reports, the human decides.
- **Deciding content.** It flags differences against the trust hierarchy; it does not
  author or arbitrate copy.
- **Continuous enforcement.** It is an on-demand audit, not a CI gate or a scheduled
  monitor.
- **Non-HTML surfaces.** App-store listings, social profiles, and ad copy are not
  scanned — the surfaces are HTML-based websites, GitHub repositories, and local docs.
