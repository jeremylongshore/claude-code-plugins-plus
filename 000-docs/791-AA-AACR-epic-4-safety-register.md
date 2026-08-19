<!-- doc-class: record -->

# Epic 4 Safety Enforcement Register — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.1
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.1`
- **Implementation PR:** [#1279](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1279)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.1 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

`000-docs/790-DR-STND-safety-enforcement-register.md` is published, AUTHORITATIVE, and
STANDARDS-linked (the canonical table grows to 13 links; the authority test re-pinned with three
effective claimants). Every claimed safety property found by a full-surface sweep — 15 MCP
plugins, root governing docs, the marketplace site, skill/agent denylist posture, the scanner
suite, contributor templates — has a row naming its enforcing artifact or the literal words
PROSE ONLY. The register carries a maintenance rule: a PR touching a safety claim or boundary
updates the register in the same PR, and `claim-verifier` treats an unregistered claim as a
failing finding.

## Headline findings (feeding the remaining Epic 4 beads)

1. **dolt-mcp-vcs's recommend-only mutation gate is PROSE ONLY at the MCP boundary** — the
   classifier lives on the ancillary python-client path while destructive verbs are live
   callable MCP tools. E4.9 proves or withdraws; no third option.
2. **The gitleaks blanket allowlist excludes ~67% of tracked files** (measured over the current
   index; the blueprint's 61.1% was an earlier snapshot) — including every SKILL.md — and
   allowlists the exact `tests/fixtures/` location other docs recommend for test secrets. E4.5.
3. **No verified-credential scan ever gates a PR** (trufflehog is schedule-only with
   `--only-verified`) — the union gap. E4.6.
4. **The deterministic supply-chain scan covers `plugins/**`on PRs only** — nothing scans`push: main`. E4.7.
5. **The skill-side denylist class is essentially unexercised** (52 of 5,591 skills, 0.93%)
   while agents sit at 73.8%; denylist enforcement is harness-runtime-only. E4.13 owns
   fail-closed degradation.
6. **The tier-2 tool-safety justification is a prose-heading presence test** and the validator
   self-declares a false-negative-preferring posture. E4.3's ratchet freezes the debt.

## Claims corrected at the source in this PR (the claim, not the control, was wrong)

- `.github/SECURITY.md`: the phantom "Weekly security audit workflow" → the real weekly
  trufflehog full-history scan.
- `000-docs/700`: the curated-copy "periodic reconcile pulls upstream security fixes" promise
  contradicted the curated freeze (the sync writes no files to curated sources) → corrected to
  the deliberate human-reviewed re-baseline path, with a dated correction note.
- `marketplace compare page`: "Every plugin passes CI validation: … secret scanning, and
  dangerous pattern detection" → accurate wording pointing at the register.
- `CrossProperty` component: "Every plugin here was built shipping real systems" → first-party
  vs mirrored provenance stated honestly.
- `REVIEW.md`: the merge gate corrected from two required contexts to three (the drift the E2.7
  assertion polices on CLAUDE.md/GOVERNANCE.md but which had a third copy here).

## Verification

- `check-doc-authority` OK — 3 effective claimants, 13 canonical-table links, test suite 8/8
  after re-pin.
- The register's artifact citations were compiled from a live sweep with code-level verification
  on the load-bearing rows (REFUSE-unwaivable verified in scanner source; dolt gate bypass
  verified against `.mcp.json` and the live tool surface; gitleaks allowlist measured at ~67%
  over `git ls-files`). Hosted CI final.

## Follow-up

Every ⚠️/📝 row resolves through its named Epic 4 bead; the register is the epic's working map.
