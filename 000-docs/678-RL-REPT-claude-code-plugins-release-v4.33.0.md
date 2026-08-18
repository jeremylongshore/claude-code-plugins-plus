<!-- doc-class: record -->

# Release Report: claude-code-plugins v4.33.0

## Executive Summary

- **Version:** 4.33.0 (MINOR bump from 4.32.0)
- **Release Date:** 2026-05-25 / 2026-05-26 UTC
- **Release Type:** minor — 4 new features, 1 user-visible fix, 1 CVE patch
- **Approved By:** Jeremy Longshore (SHA `dca19f00f`)
- **Release Commit:** `783a609f7`
- **Tag:** `v4.33.0` (annotated)
- **GitHub Release:** <https://github.com/jeremylongshore/claude-code-plugins-plus-skills/releases/tag/v4.33.0>
- **Ceremony Duration:** ~5 hours wall-clock (293 min). Most of that was waiting for required CI on two intermediate PRs (`#780` cowork pipeline; `#781` cowork content fix + gitleaks allowlist). Pure /release ceremony work was ~30 min.

## Headline

The cowork download pipeline is now a deterministic function of the catalog from disk through deploy, with a CI gate that fails the build if anyone regresses the contract. Plus the agency-os plugin lands, a new Unicode hygiene CI gate hardens contributor PRs against [Trojan Source](https://trojansource.codes/) attacks (CVE-2021-42574), and the `/cowork/` page itself gets the prereq banner + setup-guide rewrite that users have been missing.

## Pre-Release State

### Pull Requests merged into this release

| PR                                                                                  | Title                                                                                            | Type    |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------- |
| [#709](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/709) | feat: add agency-os plugin (AI agency + Notion board)                                            | Added   |
| [#775](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/775) | docs(aar): 2026-05-22→24 CI hardening campaign session log                                       | Changed |
| [#777](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/777) | feat(ci): Unicode hygiene gate / Trojan Source defense                                           | Added   |
| [#780](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/780) | feat(cowork): idempotent build + drift gate + auto-cowork contract                               | Added   |
| [#781](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/781) | fix(cowork): prereq banner + setup-guide rewrite + official-resources block + gitleaks allowlist | Fixed   |

Plus two non-PR blog commits (`2cb8b4289`, `8e1e78013`) for tonsofskills.com posts.

### Pre-release blockers cleared during ceremony

| Blocker                                                                                                                                   | Resolution                                                                                                                                                                                                                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Open PR #780 (this session's cowork pipeline work) — REVIEW_REQUIRED                                                                      | Verified Gemini Code Assist is intentionally disabled in `.gemini/config.yaml`; required CI checks all green; admin-merged per autonomous CTO policy.                                                                                                                                                               |
| 5 modified files in working dir (prior cowork content fix, uncommitted)                                                                   | Branched `feat/cowork-prereq-banner-content-fix`, committed, opened PR #781, fixed gitleaks false-positive on `marketplace/public/data/skills-catalog.json` (Supabase local-dev demo JWTs in bundled SKILL.md content — extended existing `src/data/*.json` allowlist scope to `public/data/*.json`), admin-merged. |
| Critical CVE: simple-git@3.30.0 in `plugins/mcp/project-health-auditor` (GHSA-r275-fr43-pm7q — RCE via case-insensitive `protocol.allow`) | Inline `pnpm update simple-git --latest` against the plugin's workspace; bumped to 3.32.3+. Audit moved from 1 critical → 0 critical (also 41 high → 39 high).                                                                                                                                                      |

### Branch state

- Local feature branches cleaned up: `feat/cowork-idempotent-pipeline-claude-s43v`, `feat/cowork-prereq-banner-content-fix`, `feat/unicode-hygiene-ci-gate-nmug`.
- Remote-tracking refs pruned.
- 6 third-party contributor PRs still open and awaiting review (`#778, #761, #758, #737, #728, #726`) — not blocking; they're in the normal review queue.

### Security

| Item                                                                                                 | Outcome                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Secrets scan on release-touched files (`CHANGELOG.md`, `README.md`, `VERSION`)                       | Clean.                                                                                                                                                 |
| Pre-existing `.gitleaks.toml` allowlist for `marketplace/src/data/*.json` (bundled SKILL.md content) | Extended to `marketplace/public/data/*.json` runtime mirror — same trust scope, eliminates a recurring false positive.                                 |
| `pnpm audit --audit-level=critical`                                                                  | 1 critical (simple-git RCE) — fixed in-release. Final count: 0 critical, 39 high, 51 moderate, 9 low.                                                  |
| Branch protection                                                                                    | `main` requires 1 review + 10 status checks. Admin bypass available (`enforce_admins: false`) and used for two intermediate merges + the release push. |

## Changes Included

### Added

- **agency-os plugin** (`productivity/agency-os/`) — first AI agency + Notion board orchestrator in the catalog (#709).
- **Unicode hygiene CI gate** — `scripts/validate-unicode-hygiene.py` + `.github/workflows/validate-unicode-hygiene.yml`. Blocks bidi-override + tag-character abuse in `SKILL.md`, `plugin.json`, agent, and command files. Defends against [Trojan Source](https://trojansource.codes/) (CVE-2021-42574). Regression suite at `tests/test_validate_unicode_hygiene.py` (#777).
- **Idempotent cowork build pipeline** — `scripts/build-cowork-zips.mjs` now wipes `marketplace/public/downloads/{plugins,bundles}` before each run. Output state is exactly what `marketplace.extended.json` declares — no more, no less (#780).
- **Cowork drift gate** — `scripts/validate-cowork-manifest.mjs`. Seven catalog ↔ manifest ↔ disk alignment checks including orphan-zip detection. Wired into both `marketplace/scripts/build.mjs` and `.github/workflows/validate-plugins.yml` (#780).
- **CLAUDE.md § Auto-cowork contract** — documents the author flow, pipeline determinism, deploy propagation via `rsync --delete`, and the deliberate decision NOT to wire `cowork:zips` into `sync-marketplace` (#780).

### Fixed

- **`/cowork/` page content gap** — amber prereq banner above hero, setup-guide rewrite, official-resources block linking to upstream Anthropic Cowork docs (#781).
- **`.gitleaks.toml`** — extends `src/data/*.json` allowlist scope to `public/data/*.json` (runtime mirror). Eliminates recurring false positive on bundled Supabase local-dev demo JWTs (#781 co-fix).
- **Critical CVE GHSA-r275-fr43-pm7q** — bump `simple-git` in `plugins/mcp/project-health-auditor` from `^3.30.0` to patched range. RCE via case-insensitive `protocol.allow` config key.

### Changed

- Repo-side records of the 2026-05-22 → 2026-05-24 CI hardening campaign (#775).
- Two tonsofskills.com blog posts on self-expiring report-only CI gates and Unicode hygiene as same-day trapdoor defense.

### Documentation updates applied this release

- `CHANGELOG.md` — `[4.33.0]` section per Keep-a-Changelog 1.1.0 + SemVer 2.0.0.
- `README.md` — release badge `v4.30.0 → v4.33.0`; plugins count `425 → 431`; skills count `2,810 → 2,754`; footer `Version: 4.20.0 → 4.33.0`, `Last Updated: March 2026 → 2026-05-25`.
- `CLAUDE.md` § Auto-cowork contract (landed via #780).
- `intentsolutions-vps-runbook/docs/onboard-new-repo-deploy.md` § Atomic deploy convention (landed via runbook #26).

## Metrics

| Metric                | Value                                 |
| --------------------- | ------------------------------------- |
| Commits since v4.32.0 | 7                                     |
| Files changed         | 45 (release commit alone: 6)          |
| Lines added           | +4,708                                |
| Lines removed         | −2,029                                |
| Contributors          | 2 (Jeremy Longshore, Artyom Rabzonov) |
| Days since v4.32.0    | 1                                     |

## External Artifacts

| Artifact                                    | Status                                                                                                                                             | Details                                                                                   |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| GitHub Release                              | Created                                                                                                                                            | <https://github.com/jeremylongshore/claude-code-plugins-plus-skills/releases/tag/v4.33.0> |
| Git tag                                     | Pushed (annotated)                                                                                                                                 | `v4.33.0`                                                                                 |
| One-pager + operator audit + changelog gist | Updated (was STALE at v4.31.0, 17 days behind)                                                                                                     | <https://gist.github.com/a61dcd78f4a28bc32bed07997d9de3fb>                                |
| Gist updated_at                             | 2026-05-26T02:10:32Z                                                                                                                               | —                                                                                         |
| npm publish                                 | Pending (driven by `publish-changed-packages.yml` on next workspace dep change; root package `claude-code-plugins-marketplace` not auto-published) | —                                                                                         |

## Quality Gates

| Gate                                      | Status                           | Evidence                                                                                   |
| ----------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------ |
| Phase 2.6 — SemVer 2.0.0 regex            | ✓                                | `4.33.0` matches the spec regex.                                                           |
| Phase 2.6 — Monotonic bump                | ✓                                | `v4.32.0` → `v4.33.0`.                                                                     |
| Phase 2.6 — Keep-a-Changelog dated header | ✓                                | `## [4.33.0] - 2026-05-25` present.                                                        |
| Phase 2.6 — Section subheaders            | ✓                                | `### Added`, `### Fixed`, `### Changed`.                                                   |
| Phase 2.6 — Bullet items present          | ✓                                | All three sections populated.                                                              |
| Phase 3.1 — Secrets scan on release docs  | ✓                                | No matches in `CHANGELOG.md`, `README.md`, `VERSION`.                                      |
| Phase 3.2 — Critical CVE count            | ✓                                | 0 critical after simple-git bump.                                                          |
| Phase 3.3 — Branch protection respected   | ✓ (used admin bypass per policy) | Admin bypass restored automatically; no protection-disable left behind.                    |
| Phase 3.4 — License                       | ✓                                | MIT (LICENSE file + package.json).                                                         |
| Cowork drift gate self-test               | ✓                                | Released gate passes against the released catalog (421 non-MCP plugins ↔ manifest ↔ disk). |
| Unicode hygiene self-test                 | ✓                                | New + modified release docs scanned: 0 BLOCKER / 0 MAJOR / 0 MINOR.                        |

## Beads ↔ GitHub ↔ Plane (this release)

| Bead                 | Title                                                                                 | GH                                                              | Plane    | State  |
| -------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------- | ------ |
| `claude-s43v` (epic) | Make the cowork download pipeline self-healing and auto-cowork-ready for every plugin | `#779`                                                          | `CCP-29` | CLOSED |
| `claude-2hlo`        | Wipe downloads dirs in build-cowork-zips.mjs                                          | `#779` umbrella                                                 | —        | CLOSED |
| `claude-q39n`        | Add validate-cowork-manifest.mjs drift gate                                           | `#779` umbrella                                                 | —        | CLOSED |
| `claude-522d`        | Document auto-cowork contract in CLAUDE.md                                            | `#779` umbrella                                                 | —        | CLOSED |
| `claude-hg0y`        | Verify VPS deploy `rsync --delete` + record in runbook                                | `intentsolutions-vps-runbook#25` → PR `#26` (squash `66615e8c`) | —        | CLOSED |

## Rollback Procedure

```bash
# Local + remote tag rollback
git push origin --delete v4.33.0
git tag -d v4.33.0
gh release delete v4.33.0 --repo jeremylongshore/claude-code-plugins-plus-skills --yes

# Revert the release commit (783a609f7)
git checkout main
git revert 783a609f7 --no-edit
git push origin main

# Rollback inflight commits (if needed)
# - PR #780 (cowork pipeline)    : git revert 2326cfb25
# - PR #781 (cowork content fix) : git revert dca19f00f

# Restore previous catalog state (downloads/ is gitignored — rebuild via:)
cd marketplace && npm run build
```

The cowork drift gate added in this release **does not** require the cowork pipeline to remain idempotent — reverting #780 means the wipe disappears but the catalog/manifest/disk relationship is unaffected at the validator level. However, reverting #780 without also reverting the validator addition would mean local dev orphans return.

## Post-Release Checklist

- [x] Tag pushed, GitHub Release created
- [x] Gist updated (was 17 days stale)
- [x] All session beads closed with evidence
- [x] Local feature branches deleted
- [x] Remote-tracking refs pruned
- [x] Runbook PR (`intentsolutions-vps-runbook#26`) merged
- [x] AAR filed (this document)
- [ ] Monitor `validate-plugins.yml` first post-release run for cowork drift gate behavior
- [ ] Watch for downstream npm `auto-bump-on-pr` interactions (none expected — release was direct-to-main, not via PR)
- [ ] Address remaining 39 high-severity audit findings in a follow-up patch release if any affect prod paths (most are dev-only)

## Lessons Learned

1. **Gemini Code Assist is disabled here** — `.gemini/config.yaml` sets `code_review.disable: true` because Gemini was duplicating the local pr-prescreen workflow. The global CLAUDE.md "wait for Gemini" loop does not apply in this repo. Future ceremonies should check for `.gemini/config.yaml` before polling.
2. **`marketplace/public/data/*.json` was missing from `.gitleaks.toml`** — the `src/data/` copy was allowlisted, but the runtime mirror produced by `marketplace/scripts/build.mjs` wasn't. Any regen turns gitleaks red until the next allowlist push. Now fixed for all future cowork content updates.
3. **Inline CVE fix vs follow-up release** — picked inline because the simple-git bump was a one-line `pnpm update` against a leaf workspace. Net diff: 28 lines of `pnpm-lock.yaml` + 1 line of `package.json`. The cost of waiting was a known-RCE shipping under our name for another day; the cost of folding in was negligible. Right call.
4. **The cowork content fix had been sitting uncommitted for hours** — the prereq banner work (filesystem mtime 2026-05-25 11:15) was authored, tested, never committed. /release Phase 0 caught it as a working-dir blocker. Without the ceremony, that work might have shipped on someone else's commit later without attribution.

— Jeremy Longshore
intentsolutions.io
