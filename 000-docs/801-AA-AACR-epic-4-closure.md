<!-- doc-class: record -->

# Epic 4 Closure — Safety Claims Backed by Enforced Boundaries — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 (§ 13), 14 blueprint beads E4.1–E4.14
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Epic bead:** `claude-or1m` (14 children, all closed)
- **Status:** Closure record; the parent bead closes after this filing merges, per the program's filing-then-close transaction

## Verdict

Epic 4 is complete: all 14 blueprint beads implemented across 14 children, executed in a
single day under the owner's "finish epic 4" authorization — 11 PRs (#1278–#1288, plus the
upstream dolt-mcp-vcs-plugin#10), AARs 791–800, every close carrying PR + merge-SHA evidence.
The `beads-warden` pre-closure audit examined all 15 records and returned **one record
defect** (dispositioned below), zero mislabeled closures, and full 1:1 bead-to-blueprint
coverage.

## Bead-to-evidence map

| Blueprint                              | Child            | Evidence                                                          |
| -------------------------------------- | ---------------- | ----------------------------------------------------------------- |
| E4.1 safety enforcement register       | `claude-or1m.1`  | PR #1279 → AAR 791; register = 000-docs/790 (canonical)           |
| E4.2 vocabulary gate                   | `claude-or1m.3`  | dispositioned SATISFIED-BY-EQUIVALENCE by E3.3 (#1268, AAR 780)   |
| E4.3 bare-Bash/tier-2 freeze           | `claude-or1m.9`  | PR #1285 (ratchet trio, disclosed coupling) → AAR 797             |
| E4.4 shell-substitution blocking       | `claude-or1m.10` | PR #1285 → AAR 797                                                |
| E4.5 gitleaks de-blanket               | `claude-or1m.4`  | PR #1280 → AAR 792                                                |
| E4.6 unverified-secret PR scan         | `claude-or1m.6`  | PR #1282 → AAR 794                                                |
| E4.7 push-to-main content scan         | `claude-or1m.5`  | PR #1281 → AAR 793                                                |
| E4.8 MCP-config fail-closed lane       | `claude-or1m.8`  | PR #1284 → AAR 796                                                |
| E4.9 dolt-mcp prove-or-withdraw        | `claude-or1m.7`  | PR #1283 + upstream dolt-mcp-vcs-plugin#10 → AAR 795              |
| E4.10 destructive-policy registry      | `claude-or1m.14` | PR #1288 → AAR 800                                                |
| E4.11 agents-lane ratchet              | `claude-or1m.11` | PR #1285 → AAR 797                                                |
| E4.12 compliance-rate arithmetic       | `claude-or1m.2`  | PR #1278 (no standalone AAR — see disposition 1)                  |
| E4.13 denylist fail-closed degradation | `claude-or1m.12` | PR #1286 → AAR 798                                                |
| E4.14 plaintext-cred refuse-to-start   | `claude-or1m.13` | PR #1287 → AAR 799 (rotation half owner-deferred — disposition 3) |

## Measurable outcomes vs the § 13 targets

- **Safety claims mapped to a named boundary 0 → 100%** — the register (790) is canonical,
  STANDARDS-linked, and self-maintaining (updated in the same PR as every boundary change,
  which this epic did seven times).
- **Tracked files invisible to gitleaks: ~67% → 0 blanket file-type allowlists** — measured
  171 findings on the de-blanketed tree, triaged to 0 with everything scanned; one real dead
  npm token found and redacted; shape ratchet forbids the blanket class forever.
- **Blocking PR scan for unverifiable secrets 0 → 1 in `ci-required`** — `secret-diff-scan`
  is the 22nd gate job; measured diff-scoped noise at landing: 0 findings over 30 commits.
- **Supply-chain scan coverage of `push: main`: none → full** — full grading, REFUSE
  unwaivable; residual (`enforce_admins:false`) stated: visible, not impossible.
- **MCP destructive policies 0/14 → 14/14 declared, every refuse claim backed or
  withdrawn** — the registry + executing gate; dolt's recommend-only claim PROVEN at the
  wire (guard proxy, upstream-first through the mirror engine); servicegraph's prose
  confirmation upgraded to a shipped ask-hook; three plugins honestly declared `permit`
  with blast radius named.
- **Unscoped-Bash and tier-2 findings frozen by a shrink-only ratchet** — triple-keyed
  (count · set-SHA · schema version), swap-fails-at-equal-count, no waiver path for
  shell-substitution.
- **The shell-substitution security errors blocking on changed files** — via the same
  ratchet: 7 first-party occurrences pinned (the blueprint's 10 counted mirror copies;
  mirrors are upstream-owned), any new occurrence fails.

## Warden dispositions

1. **E4.12's missing AAR (the audit's one defect):** the slice merged before the epic's AAR
   cadence began and no standalone AAR exists. Dispositioned as a record correction, not a
   reopen: a correcting note on `claude-or1m.2` points at the close-reason evidence
   (python 55/55, harness 24/24, `measure-epic-1 --check` OK) and at this filing, which is
   the durable record of that disposition.
2. **Dolt-history write-integrity leg not performed** (audit tooling had no Bash/Dolt
   access): mitigated as in the Epic 1–3 closures by direct `bd` CLI read-back against the
   live Dolt-backed store — all 14 children CLOSED at this filing — with the full
   Dolt-history re-audit available once a beads sql-server session is convenient. Every
   state change in this epic used the one-write-then-export flush pattern.
3. **E4.14's rotation half is owner-deferred** (Whop sidelined, § 18.7 asked-once — never
   re-asked). The refuse-to-start pre-flight is live (pre-commit + SessionStart); the
   encrypted posture already holds. Residual accepted by the owner until Whop resumes.

## Dependency resolutions recorded

- E4.3/E4.11's "Epic 6 ratchet machinery" dependency: resolved by building the machinery now
  on the E3.11 pattern (`check-safety-ratchet.mjs`); if Epic 6 ships a generalized substrate,
  this gate is its first migration customer.
- E4.5 → E4.6 strictly-serial edge honored (#1280 merged before #1282 opened).
- Prohibited-scope compliance: no branch-protection change, no credential rotated, no fourth
  required context; the one mirror-content slip (E4.9's first draft hand-edited the
  dolt-mcp-vcs mirror) was caught and corrected mid-slice — upstream-first via
  dolt-mcp-vcs-plugin#10, re-mirrored through `sync-external.mjs --relock`.

## Residual transfers

- First-week false-positive count for `secret-diff-scan` → record on `claude-or1m.6`.
- a2a-client's destructive-policy declaration → self-enforced by the E4.10 gate when
  PR #1170 merges.
- Full-schema `--strict` promotion for the MCP-config validator → DR-049 soak checklist;
  the advisory lane's `REPORT-ONLY-UNTIL: 2026-11-17` is policed by the deadline step.
- Whop key rotation → owner's call when Whop resumes (never re-ask).
- Dolt-history re-audit of this epic's bead writes → next beads sql-server session.
