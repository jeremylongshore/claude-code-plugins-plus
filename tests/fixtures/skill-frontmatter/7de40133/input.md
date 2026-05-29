---
name: sync-testing-harness
description: 'Bulk-check Intent Solutions repos for audit-harness version drift. Detects
  the latest

  published @intentsolutions/audit-harness version on npm, scans ~/000-projects/ for

  repos that depend on it (npm dep, vendored .audit-harness/, PyPI install, or crates

  install), and reports which are behind. Offers to bump node repos and prints the

  install command for vendored repos.

  Use when propagating a new harness release, auditing ecosystem harness coverage,

  or investigating test-enforcement drift.

  Trigger with "/sync-testing-harness", "sync harness", "check harness drift",

  "harness propagation".

  '
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
model: inherit
tags:
  - testing
  - audit-harness
  - drift
  - propagation
  - ecosystem
compatibility: Designed for Claude Code
---

# Sync Testing Harness v0.1

## Purpose

Keep the `@intentsolutions/audit-harness` install version consistent across every
Intent Solutions repo. New harness releases mean policy-enforcement changes; stale
installs silently miss new escape-grammar patterns or CRAP-scoring fixes.

This skill does one thing: **detect drift and produce an actionable report**. It
does not unilaterally open PRs — it offers, confirms, and executes.

## Prerequisites

- `~/000-projects/` as the scan root (configurable via `SCAN_ROOT` env var)
- `~/000-projects/intent-eval-platform/audit-harness/HARNESS-SYNC-REPORT.md` as the report output (configurable via `REPORT_PATH` env var) — **NOT** the same as scan root
- `gh`, `npm`, `git` on PATH
- Network access to `registry.npmjs.org` and `pypi.org`

---

## Instructions

Execute phases in order. **STOP and report** on any blocking error.

### Phase 0: Resolve latest upstream version

Fetch the latest published version for each ecosystem. npm is the canonical source;
PyPI and crates.io should track it.

```bash
# npm (canonical)
NPM_LATEST=$(npm view @intentsolutions/audit-harness version 2>/dev/null || echo "unknown")

# PyPI (optional — may 404 until first publish)
PYPI_LATEST=$(curl -s https://pypi.org/pypi/intent-audit-harness/json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["info"]["version"])' \
  2>/dev/null || echo "unpublished")

# crates.io (optional)
CRATES_LATEST=$(curl -s https://crates.io/api/v1/crates/intent-audit-harness \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["crate"]["newest_version"])' \
  2>/dev/null || echo "unpublished")

echo "upstream: npm=$NPM_LATEST pypi=$PYPI_LATEST crates=$CRATES_LATEST"
```

Record these. If `NPM_LATEST` is `unknown`, abort — this tool is useless without
at least the npm baseline.

### Phase 1: Enumerate repos

Default scan root is `~/000-projects/`. Honor a positional arg if given:
`/sync-testing-harness ~/some-other-root`.

```bash
ROOT="${1:-$HOME/000-projects}"
mapfile -t REPOS < <(find "$ROOT" -maxdepth 2 -type d -name ".git" | xargs -I{} dirname {})
```

Skip `99-archived/` and `99-forked/` by default.

### Phase 2: Classify each repo

For each repo, determine install method and current version. Four buckets:

| Bucket          | Detection                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------ |
| `NODE_DEP`      | `package.json` has `@intentsolutions/audit-harness` in `dependencies` or `devDependencies` |
| `VENDORED`      | `.audit-harness/VERSION` file exists                                                       |
| `PYTHON_DEP`    | `pyproject.toml` or `requirements.txt` references `intent-audit-harness`                   |
| `RUST_DEP`      | `Cargo.toml` has `intent-audit-harness` in `[dependencies]`                                |
| `NOT_INSTALLED` | none of the above                                                                          |

Extract the installed version string from whichever manifest applies. Store
`(repo_path, bucket, installed_version, drift_status)` rows in memory.

`drift_status` values:

- `CURRENT` — matches upstream
- `BEHIND` — installed < upstream (numeric compare by SemVer)
- `AHEAD` — installed > upstream (unusual; flag)
- `UNKNOWN` — version string unparseable

### Phase 3: Build report

Write `$REPORT_PATH` (default: `~/000-projects/intent-eval-platform/audit-harness/HARNESS-SYNC-REPORT.md` — the harness repo root, beside the package being audited). Override with `REPORT_PATH` env var if needed. The audit-harness repo's `.gitignore` excludes this filename so the weekly-cron updates don't dirty the working tree.

**Path history:** previously written to `$ROOT/HARNESS-SYNC-REPORT.md` (which defaulted to `~/000-projects/` umbrella root). Updated 2026-05-28 — that umbrella is a meta-repo with whitelist .gitignore for project structure; the harness sync report is an operational artifact that belongs beside the package it audits ("enforcement travels with the code" per `~/.claude/CLAUDE.md` Core Principles).

```markdown
# Harness Sync Report — <timestamp>

## Upstream versions

- npm: <NPM_LATEST>
- PyPI: <PYPI_LATEST>
- crates: <CRATES_LATEST>

## Ecosystem summary

- Repos scanned: <N>
- Current: <X>
- Behind: <Y>
- Not installed: <Z>
- Ahead/unknown: <W>

## Behind

| Repo | Method   | Installed | Latest | Upgrade command                                                 |
| ---- | -------- | --------- | ------ | --------------------------------------------------------------- |
| ...  | NODE_DEP | 0.1.0     | 0.2.0  | `pnpm up @intentsolutions/audit-harness@^0.2.0`                 |
| ...  | VENDORED | v0.1.0    | v0.2.0 | `AUDIT_HARNESS_VERSION=v0.2.0 curl -sSL .../install.sh \| bash` |

## Not installed

| Repo | Language hint | Suggested install                  |
| ---- | ------------- | ---------------------------------- |
| ...  | Python        | `pip install intent-audit-harness` |

## Current (healthy)

<collapsed list>

## Ahead / unknown

<inspect manually>
```

### Phase 4: Offer propagation

After the report writes, ask via `AskUserQuestion`:

> "Found N repos behind. Would you like to:
> (1) Auto-PR bump for NODE_DEP repos (creates feature branch, updates package manifest, pushes, opens PR)
> (2) Print vendored upgrade commands only (copy/paste)
> (3) Both
> (4) Skip — I'll handle it"

For option (1) or (3), for each NODE_DEP repo:

```bash
cd "$repo"
git checkout -b chore/bump-audit-harness-$NPM_LATEST
# edit package.json version spec (preserve ^ / ~ style)
# run the package manager already in use (pnpm/npm/yarn) to update lockfile
git add package.json <lockfile>
git commit -m "$(cat <<EOF
chore(deps): bump @intentsolutions/audit-harness to $NPM_LATEST

Keeps test-enforcement policy current with the canonical harness release.
Auto-bumped by /sync-testing-harness.

Jeremy made me do it
-claude
EOF
)"
git push -u origin "chore/bump-audit-harness-$NPM_LATEST"
gh pr create --title "chore(deps): bump audit-harness to $NPM_LATEST" --body "$(cat <<EOF
Automated bump from /sync-testing-harness.

Upstream: https://www.npmjs.com/package/@intentsolutions/audit-harness
Changelog: https://github.com/jeremylongshore/audit-harness/blob/main/CHANGELOG.md

Jeremy made me do it
-claude
EOF
)"
```

**Never push to main/master directly.** Always use a feature branch + PR.

For vendored repos, just print the `AUDIT_HARNESS_VERSION=... curl ... | bash`
command and let the engineer run it inside the target repo.

### Phase 5: Final summary

Print:

- Report path
- PR URLs created (if any)
- Copy/paste command block for vendored upgrades
- Any errors encountered per-repo (non-fatal)

---

## Invariants

- Report file always writes, even on partial scan failure
- Never commit to main/master; always feature branch + PR
- Only touch dependency manifests — never touch harness config files (`.audit-harness/`,
  `.harness-hash`). Those are engineer-owned.
- SemVer comparison is numeric per-segment; pre-release tags (`-rc.1`) sort below release
- Soft-fail on individual repo errors; continue the sweep

## Exit codes

- 0 — report written, all requested actions succeeded (or nothing to do)
- 1 — report written, some per-repo actions failed (details in report)
- 2 — fatal pre-flight failure (no npm, no network, bad scan root)

## Notes

- This skill is ecosystem-wide infrastructure. Keep it under 300 lines.
- Do not reimplement harness logic here — this is purely a propagation tool.
- For the harness itself: <https://github.com/jeremylongshore/audit-harness>
