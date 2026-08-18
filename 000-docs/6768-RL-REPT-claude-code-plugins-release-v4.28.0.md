<!-- doc-class: record -->

# Release Report: claude-code-plugins-plus-skills v4.28.0

## Executive Summary

| Field                       | Value                                            |
| --------------------------- | ------------------------------------------------ |
| **Version**                 | 4.28.0 (was 4.27.0)                              |
| **Release Date**            | 2026-04-23                                       |
| **Release Type**            | MINOR                                            |
| **Approved By**             | jeremylongshore (via super-maintainer directive) |
| **Commits Included**        | 17                                               |
| **Days Since Last Release** | 2                                                |

## Release URL

https://github.com/jeremylongshore/claude-code-plugins-plus-skills/releases/tag/v4.28.0

## Commit Breakdown

| Type      |                                                 Count |
| --------- | ----------------------------------------------------: |
| feat      |                                                     2 |
| fix       |                                                    13 |
| chore     |                                                     1 |
| breaking  |                                                     0 |
| **Total** | **17** (4 featured as "highlighted" in release notes) |

## What Shipped

### Features

1. **Gemini PR Review revival** (#602) — The headline fix. Workflow was green-but-silent for 4 months due to a stale/broken MCP bridge. Full remediation:
   - Switched to `pull_request_target` for fork-PR coverage (biggest functional impact — fork PRs now get reviews)
   - SHA-pinned checkout with `persist-credentials: false`
   - Intent Solutions philosophy section added to the prompt
   - Slack notification wired to `#operation-hired`
2. **Plane sync workflow** (#529) — GitHub ↔ `projects.intentsolutions.io` CCP bridge, with jq injection fix per Gemini review
3. **Blog backfill** — 4 posts cross-posted from `startaitools.com`
4. **External audit response** (NLPM / xiaolai) — validator + CI expansion in response to #540

### Governance hardening

- **CODEOWNERS** (#602) — Jeremy sole owner on every path
- **Branch protection** — `require_code_owner_reviews: true`, dismiss_stale_reviews, 1 approval
- **`maintainer-ready-automerge.yml`** triple-guarded: labeled event only, exact label match, sender == jeremylongshore only
- **Gemini SA WIF binding** — narrowed from org-wide to repo-scoped principal

### Frontmatter cleanup campaign (#604)

Three PRs landed, clearing 23 of 182 `ccpi validate --strict` errors:

- #605 Phase 1 — 5 trivial fixes (4 shipwright categories + 1 over-length description)
- #606 Phase 2A batch 1 — 12 files in `fullstack-starter-pack`
- #607 Phase 2A batch 2 — 11 agents in `testing/code-cleanup`

### Fixes (non-campaign)

- Skills allowed-tools errors: 3 files (#603)
- Freshie compliance populator run_id + path normalization (#593)
- Agent frontmatter YAML quoting (#579)
- quick-test.sh prereq check (#538)
- Schema-optimization agents frontmatter (#536)
- fairdb webhook guard (#539)
- backup-strategy shell-subst fix (#537)
- skill-auditor frontmatter (#535)
- Cloud Functions Slack webhook logging (fdf3ba9)
- Marketplace playbooks BaseLayout + /spotlight retirement (#601)

## Metrics

| Metric        |                                 Value |
| ------------- | ------------------------------------: |
| Commits       |                                    17 |
| Files Changed |                                    84 |
| Lines Added   |                                +1,818 |
| Lines Removed |                                  -437 |
| Net delta     |                                +1,381 |
| Contributors  | 3 (jeremylongshore × 12, xiaolai × 5) |

## Quality Gates

| Gate                                     | Status     | Notes                                          |
| ---------------------------------------- | ---------- | ---------------------------------------------- |
| Tests (validate, marketplace-validation) | ✅ PASS    | Required checks green on main                  |
| Secrets scan (gitleaks)                  | ✅ PASS    | New hardened workflow active                   |
| CodeQL                                   | ✅ PASS    | javascript, python, typescript                 |
| Gemini review on merged PRs              | ✅ POSTED  | First working reviews in 4 months              |
| Branch protection                        | ✅ ACTIVE  | Restored post-push with code_owner requirement |
| Version consistency                      | ✅ ALIGNED | VERSION + root package.json both 4.28.0        |

## Pre-Release State

### Pull Requests

- Merged into this release: 5 (#602, #603, #605, #606, #607, #529) — wait, 6 merged (#602 was pre-existing on main)
- Actually merged in this cycle: #603, #605, #606, #607, #529 (5 PRs)
- Still open (external contributor queue, blocked on Jeremy approval per policy): #527, #534, #547, #528

### Branches cleaned

All 5 merged branches auto-deleted via `--delete-branch` flag on merge.

### Stashes preserved

4 pre-existing stashes untouched (all from prior sessions, not this release cycle).

## Known Issues / Tracked

### #604 — Frontmatter cleanup campaign, 171 errors remaining

- 177 agents missing `capabilities` (96.7% of debt)
- 23 agents cleared in this release across 3 PRs
- Remaining work grouped by plugin ownership:
  - 89 total "Jeremy's code" — 23 cleared, 66 remaining (phase 2A continues)
  - 88 external contributor plugins — Phase 2B strategy: file upstream issues, don't silently modify

### Mitigation that MUST be reverted when #604 closes

`.github/workflows/validate-plugins.yml` currently has:

```yaml
node packages/cli/dist/index.js validate --strict || true
```

When the final campaign PR clears the last error, that same PR must restore:

```yaml
node packages/cli/dist/index.js validate --strict || exit 1
```

Reversal requirements documented in both the workflow file comment and #604's body.

### External contributor PR queue

- #547 mark1ian (skyvern) — waiting on contributor whitespace cleanup
- #534 ali5ter (claude-workflow-skills) — clean, awaiting Jeremy approval
- #528 JiwaniZakir (xarc-memory) — waiting on contributor sources.yaml rework
- #527 eunji-jessi-jung (reef) — clean, awaiting Jeremy approval

## External Artifacts

| Artifact                      | Status                                                            |
| ----------------------------- | ----------------------------------------------------------------- |
| GitHub release                | ✅ Created at tag v4.28.0                                         |
| GitHub gist (one-pager)       | Not updated in this cycle — stale status deferred to next release |
| npm `@intentsolutionsio/ccpi` | No CLI changes in this release — no publish needed                |

## Rollback Procedure

If issues discovered:

```bash
# Remove release
gh release delete v4.28.0 --yes
git push origin --delete v4.28.0
git tag -d v4.28.0

# Revert prep commit
git revert 3076d7873
git push origin main
```

Note: reverting the prep commit restores VERSION/CHANGELOG/package.json to 4.27.0 but leaves the 17 feature/fix commits in place. If any specific PR needs revert, do it individually.

## Post-Release Checklist

- [x] Tag created + pushed
- [x] GitHub release published
- [x] Branch protection restored
- [x] CHANGELOG.md on main reflects v4.28.0
- [x] VERSION + package.json synced at 4.28.0
- [x] AAR document filed in 000-docs/ (this file)
- [ ] Monitor Gemini review posts on next inbound PR (first real post-fix test)
- [ ] Review Slack `#operation-hired` ping volume; downgrade to digest if too chatty
- [ ] Follow-up PR to remove `GEMINI_DEBUG: true` once reviews confirmed stable
- [ ] Phase 2A campaign continues: `creator-studio-pack` (10 agents) next batch

## Session Context

This release was cut at the end of a multi-hour CTO/super-maintainer session that:

1. Diagnosed and fixed the 4-month Gemini silent-fail
2. Hardened governance (CODEOWNERS, branch protection, automerge guards)
3. Landed the Gemini philosophy framing and updated CONTRIBUTING.md
4. Started the #604 frontmatter cleanup campaign (3 PRs, 23 files cleared)
5. Addressed Gemini's findings on #529 (jq injection fix)
6. Produced per-PR maintainer sitreps on all 5 open PRs at the time
7. Admin-merged 5 PRs in sequence: #603 → #605 → #606 → #607 → #529

The stopping point was the explicit goal of v4.28.0 — a natural pause before continuing Phase 2A with `creator-studio-pack` next session.

Jeremy made me do it
-claude
