<!-- doc-class: record -->

# Epic 3 Portability-Claim Withdrawal — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 3 bead 3.11 (§ 5.4 rule 2)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.9`
- **Implementation PR:** [#1274](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1274)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.11 controls implemented; merge fields are recorded in Beads/Dolt after review

## The honest framing, stated first

An untested claim was **withdrawn, not a capability removed**. "Designed for Claude Code" —
backed by a working harness, a validated corpus, and a registered adapter — is a **stronger**
statement than 2,700 identical unverifiable sentences. The site loses nothing a user ever had.

## Measured surface (supersedes the blueprint's stale 1,454)

At activation, **2,700 first-party** SKILL.md files carried one of exactly **four** unbacked
claim strings: "…also compatible with Codex and OpenClaw" (2,604), "…with Codex" (90), "…with
Cursor" (4), "…with Cursor, Windsurf, Aider" (2). Twelve mirror-owned claims were enumerated and
left byte-identical — upstream-repair only, per the never-clobber rule.

## Outcome

1. **The sweep**: all 2,700 first-party occurrences rewritten to `Designed for Claude Code` by
   exact-string replacement (no regex over prose bodies; frontmatter untouched otherwise).
   Mirror subtrees skipped by `.source.json` ancestry.
2. **The ratchet**: `scripts/check-portability-claims.mjs`, wired as
   `validate:portability-claims` in `doc-governance` — any first-party `compatibility` naming a
   harness outside the registered adapter set fails, **in any phrasing** (nine harness-name
   patterns, red-run tested against fresh phrasings like "Copilot-ready"). The registered set is
   the E3.2 schema's `adapters` enum: `claude-code`, growing only with generated adapter
   artifacts. Mirror claims are reported with a count, never failed.
3. **Downstream regeneration**: curated mirror re-promoted (1,915 → 1,915, 0 dropped — a
   compatibility line is not a grade input), all four skill/catalog/search projections
   regenerated and check-verified, Epic 1 scorecard regenerated at parity.

## Release posture

Shipped with `[skip auto-bump]`: a truthfulness rewrite of one frontmatter line across 2,700
files is not a feature release, and auto-bumping ~400 plugin versions (with the npm republish
cascade) over it would be noise. Minor/major version moves stay deliberate human choices.

## Verification

- `pnpm run validate:portability-claims` — tests 4/4 (the four historical strings resolve to
  their unbacked sets; honest claims pass; fresh phrasings caught) and the live sweep reports
  **zero first-party unbacked claims; 12 mirror-owned reported**.
- `validate:generated-content` OK (468/3,069/80); curated re-promotion 1,915/0 dropped;
  `measure-epic-1 --check` OK; docs index unchanged; hosted CI final.

## Follow-up

- E3.12 renders the declared adapter state on the marketplace (free-text already has zero page
  consumers — verified).
- Upstreaming candidates for the 12 mirror-owned claims per the external-sync model.
