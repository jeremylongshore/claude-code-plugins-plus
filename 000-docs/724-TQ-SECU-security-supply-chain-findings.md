# 724-TQ-SECU — Security & Supply-Chain Findings (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3`. This is the public baseline record; operational
security matters in flight are tracked in local beads and intentionally not detailed here
until remediation completes.

## Findings

1. **Committed foreign-platform binary:** `kobiton` — Mach-O 64-bit x86_64, 11,790,440 B,
   tracked ×3 (35.4 M). Unauditable blob in a source repo; wrong platform for ubuntu CI;
   upstream licensing unverified. Removal is approval-gated (register row 3, doc 719).

2. **Full-history secret scan (gitleaks, this mission):** 1,595 commits / 329.4 MB scanned —
   **0 findings** for structured credentials (cloud keys, platform tokens, private keys).
   Defense-gap observation: gitleaks' rule set targets *structured* token shapes; it cannot
   detect free-prose credentials. Complementary content-level sweeps are part of this
   mission's method and are recommended as standing practice for docs directories.

3. **Tracked-tree secret posture:** `.gitleaks.toml` present; the `gitleaks` required check is
   green on main; prior audit's 83 content-*about*-secrets matches remain non-findings.

4. **Kernel pin staleness:** `@intentsolutions/core@0.9.0` vs published `0.10.0` — documented,
   advisory-only, lockstep-bump governed (doc 723). Not a vulnerability; recorded as
   supply-chain state.

5. **Pre-existing authorities referenced, not re-filed:** GH #1147 (CodeQL alert backlog),
   #1148 (dependency advisories), #796 (SAK v7 audit-remediation umbrella), #1166
   (scheduled-workflow failure reporting).

6. **Unicode hygiene:** default (blocking) mode PASS across the corpus; U+200B zero-width
   advisories exist in one community plugin (strict-mode-only finding) — cosmetic FIX bead.

## Method note

Diagnostics were read-only; exit codes recorded without suppression (full table: doc 721).
Secret-bearing surfaces were scanned with values never displayed, copied, or logged; scan
tooling wrote redacted reports only.
