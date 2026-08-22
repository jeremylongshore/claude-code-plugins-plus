<!-- doc-class: record -->

# Epic 3 Canonical Vendor-Literal Gate — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 3 bead 3.10 (§ 5.4 rule 3)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.8`
- **Implementation PR:** [#1273](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1273)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.10 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

Migration is now falsifiable: `scripts/check-canonical-vendor-literals.mjs` scans the canonical
layer — every `skill-card.yaml` plus any `canonical/` directory — and fails on five vendor-token
classes: **concrete model ids** (through THE shared classifier, so bead handles stay protected),
**`${CLAUDE_*}` variables** (canonical uses the portable family), **`mcp__` spellings**
(canonical declares `requires.services`), **`Builtin(...)` tool scoping** (canonical declares
abstract capabilities), and **denylist field spellings** (canonical carries
`constraints.forbid`). The translation layer is exempt by design: `scripts/adapters/` and the v0
contract documentation, where harness tokens are the subject matter.

This is deliberately a **go-forward** gate: the canonical layer holds zero files today, so the
corpus is trivially clean, and the blueprint's wording — "fails when a Claude-specific token
REAPPEARS in the harness-free core" — is enforced from the layer's birth. Red runs prove all
five refusal classes, and the clean-text test proves bead handles and portable variables pass.

## Operational rider, disclosed

The durable daily-stats fixes ride this PR (found when the first-ever self-triggered stats PR
#1272 hit CI): the workflow's commit/PR title moves to the registered
`chore(marketplace-site)` scope, and `fetch-npm-stats.mjs` pipes its spliced README through the
repo's Prettier config — the same contract the TOC generator honors — so tomorrow's 00:15 UTC
run produces a green PR with zero human touches. (#1272 itself was repaired in place and
merged: the BOT_PR_TOKEN loop is proven end to end.)

## Verification

- `node --test scripts/check-canonical-vendor-literals.test.mjs` — 4/4: layer scoping
  (adapters + v0 docs out, cards + canonical dirs in), all five red-run classes, clean-text
  pass with protected bead handle, prose-model-mention refusal inside canonical files.
- Live run: `OK (0 canonical-layer file(s) scanned; zero vendor literals)`.
- Wired as `validate:canonical-vendor-literals` in `doc-governance` (blocks via `ci-required`).
- The patched fetch script was smoke-run live (enumerates and fetches); hosted CI final.

## Follow-up

- E3.11's backfill populates the layer this gate polices; E3.12 renders the declared matrix;
  E3.13 proposes the contract to the kernel.
