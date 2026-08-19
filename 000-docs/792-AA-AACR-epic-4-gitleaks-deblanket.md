<!-- doc-class: record -->

# Epic 4 Gitleaks De-Blanket — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.5
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.4`
- **Implementation PR:** [#1280](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1280)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.5 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

`.gitleaks.toml` no longer contains a single file-type blanket. The pre-E4.5 allowlist excluded
~67% of tracked files — every `SKILL.md`, `README.md`, `CHANGELOG.md`, `references/*.md`,
`000-docs/*.md`, `tests/`, `__tests__/`, `fixtures/`, and all of `freshie/` — including the
exact `tests/fixtures/` location 709 recommends for test secrets. All of those surfaces are now
scanned. What survives is 10 documented path exceptions (self-referential pattern libraries,
generated projections whose sources are scanned, compiled `dist/`, the history-only deleted
`backups/` tree), each carrying a written `reason:` + `expiry:`; teaching examples pass by
VALUE (stopwords + regexes), so the file holding an example stays scanned and a real credential
beside one still fires.

## Measurement (the honest number, not the hoped one)

- Baseline full-tree scan under the OLD config: **0 findings** (the blankets at work — 825 MB
  scanned, most of it excluded from judgment).
- Same tree with blankets stripped, before value rules: **171 findings**.
- Triage: 170 were placeholder/teaching shapes (`abc123` walks, `YOUR_*`, ellipsis-truncated,
  jwt.io and Supabase's publicly documented demo JWTs, base64 of "api-key-here", public
  ERC-20 contract addresses, leak-canary fixtures). **One was a real-shaped historical npm
  token** in the v1.3.2 release draft (000-docs/143) — verified dead (differs from the live
  publish token; registry `whoami` returns 401) — redacted at the source and its exact value
  allowlisted so the redaction diff and full-history scans don't re-fire on a credential that
  no longer exists.
- Final full-tree scan under the NEW config: **0 findings with everything scanned**.

## The ratchet

`scripts/check-gitleaks-config.mjs` (+ 7 tests) fails any reintroduced type blanket (nine
banned fragments covering the historical blanket set) and any path exception lacking a
governed `reason:`/`expiry:` comment block. Wired as `validate:gitleaks-config` inside
`doc-governance`, blocking via `ci-required`.

## Register maintenance

Both `E4.5 target` rows in the Safety Enforcement Register (790 § 2) flipped to
`✅ … E4.5 closed` in this same PR, per the register's own rule.

## Verification

- Gate tests 7/7; live config passes (10 documented exceptions).
- Full-tree scans quoted above ran locally with the repo's gitleaks binary; hosted CI's
  `gitleaks` context re-proves the PR-scoped path.

## Follow-up

E4.6 (diff-scoped unverified-secret PR scan) starts only after this merges — strictly serial,
so the two changes' finding sets stay attributable.
