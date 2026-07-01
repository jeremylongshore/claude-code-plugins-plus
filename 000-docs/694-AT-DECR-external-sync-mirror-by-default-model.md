---
filing_code: AT-DECR-EXTERNAL-SYNC-MIRROR-BY-DEFAULT-MODEL-2026-06-30
date: 2026-06-30
acting_head_of_board: Jeremy Longshore
status: locked
scope: External-plugin sync pipeline — sources.yaml, scripts/sync-external.mjs, .github/workflows/sync-external.yml, scripts/validate-skills-schema.py (schema 3.15.0)
branch: feat/external-sync-mirror-model
trigger: A 4-agent deep-dive found the sync clobbering our own A-grade curation — a --force run reverted ~100 A-graded tonone agents (+ hyperflow) to 3-field upstream stubs, surfacing as an ~18.9k-line "deletion" no one had authored
inputs:
  - 000-docs/691-AT-AUDT-sync-external-pipeline-audit-and-hardening.md (prior pipeline audit + hardening)
  - 000-docs/693-AA-AACR-xquik-external-author-dogfood-and-tooling-fixes-2026-06-30.md (Xquik dogfood AAR)
  - PR #881 (the A-grade frontmatter uplift the sync reverted)
  - sources.yaml (source registry)
affects: 51 externally-synced plugins (of 454 total), the weekly + on-demand sync, the automated sync PR lifecycle, the marketplace/enterprise section-heading fairness check
---

# External-Plugin Sync — "Mirror by Default · Upstream Improvements · Never Clobber"

## Mission

The external-plugin sync is a **side-channel**, not the marketplace. Of 454 total plugins, only ~51 are externally-synced (48 third-party sources + 6 of Jeremy's own repos); the other ~403 (89%) are in-repo Intent Solutions work. External contributors are a curated **minority augment** — a respected one — but the machinery that mirrors their plugins had been allowed to overwrite work we curated locally. This record locks the policy so we never again reverse-engineer it from a 39k-line diff: how the sync treats a plugin it merely mirrors vs. a plugin we have hardened past upstream, how contributors are approached when we want their plugin at our standard, and what the code on `feat/external-sync-mirror-model` now does.

## Context / investigation

A 4-agent deep-dive into the sync produced a clear picture of how it behaved before this branch:

- **`--force` overwrites everything, every run.** `scripts/sync-external.mjs` re-clones each source and overwrites every mirrored file with the upstream copy on every run. Upstream is treated as the sole source of truth for the destination path — with no exception for files we had deliberately changed locally.
- **`verified:` was ignored by the sync.** The flag existed in `sources.yaml` but had no effect on what the sync wrote; it recorded maintainer trust, nothing more.
- **Each run opened a fresh per-run-branch PR with nothing closing the old ones.** The unique-per-run-branch model (adopted in `000-docs/691-AT-AUDT`, which fixed an earlier *shared*-branch clobber) is safe by design, but it produced a pileup — every run stacked another open `automation/sync-external-*` PR and nothing pruned the stack.
- **No auto-merge.** A human reviewed each sync PR; historically ~1 of every 10 merged. That review gate is correct and is preserved — the sync proposes, a human disposes.

This document exists precisely so the next reader does not have to rebuild the policy from a diff again.

## The core tension

We were doing **two incompatible things to the same external plugins at once**:

- **Mirroring them** — `--force`, upstream is truth, overwrite the destination every run.
- **Curating them** — landing A-grade local edits (least-privilege `tools`, Trigger-bearing descriptions, real `tags`) on those same mirrored files.

Every sync made the two fight. The scary artifact that started this — an ~18.9k-line "deletions" diff no human had authored — was **our own A-grade frontmatter being reverted to upstream stubs**: PR #881's uplift on `tonone` (~100 agents) plus `hyperflow`, silently rolled back to their 3-field upstream form by a `--force` run. The deletions were real; the author was the sync, clobbering us.

The resolution is to stop asking one mechanism to do both jobs on the same plugin.

## Decision — "mirror by default · upstream improvements · never clobber"

Three principles, applied per source:

1. **Mirror by default.** For most external plugins the contributor's own repo is the source of truth and we do **not** locally edit them. A source registered in `sources.yaml` is mirrored into `plugins/` by the sync (weekly Mondays 06:00 UTC + on-demand `workflow_dispatch`/`repository_dispatch`), which opens an automated PR a human reviews. This is the normal, respectful, low-friction path — we carry the contributor's work, credited, and let their repo drive it.

2. **Upstream improvements — don't fork them.** When we want a plugin at our A-grade bar, we **upstream the improvement**: a friendly issue, then a PR, on the **contributor's own repo** to bring **their** plugin to standard. Once merged upstream the mirror becomes A-grade naturally and the sync never has anything to revert. We do **not** hold a divergent, clobber-prone local copy as the mechanism for quality — quality lives upstream, where it belongs.

3. **Never silently overwrite local curation.** Until an improvement is upstreamed, a source we have hardened past upstream is protected by an interim guard: `curated: true` in `sources.yaml` **freezes** the source. The sync skips it entirely — no clone, no overwrite, no orphan-prune — keeping only its catalog entry current. A `--force` sync can no longer revert our edits. `tonone` and `hyperflow` carry `curated: true` today; upstreaming both is the planned path off the freeze.

### `verified:` and `curated:` are orthogonal — by design

- **`verified:`** = a maintainer vetted the source's quality/trust.
- **`curated:`** = we locally hardened the plugin past upstream, and the sync must not overwrite it.

They are independent axes. `tonone`/`hyperflow` are `curated: true` but `verified: false` — an honest state (we A-graded their agents but haven't run the trust-vetting), and exactly why the two flags stay separate rather than being collapsed into one.

## Mechanical fixes implemented on `feat/external-sync-mirror-model`

All landed and verified on this branch:

### 1. Curated freeze — `scripts/sync-external.mjs`

A source marked `curated: true` is honored: the sync logs `Curated — mirror frozen`, writes **no** files, and keeps its catalog entry current. **Verified:** a `--force` dry-run on `tonone` shows the freeze and **zero reverts** — previously the same `--force` reverted ~100 A-graded agents to 3-field upstream stubs (the ~18.9k-line deletion that started this).

### 2. Pileup auto-close — `.github/workflows/sync-external.yml`

A "Close superseded sync PRs" step runs **before** Create-PR and closes older open `automation/sync-external-*` PRs (with `--delete-branch`), keeping **at most one** open sync PR. The safe unique-per-run-branch model (from `000-docs/691-AT-AUDT`, which fixed an earlier shared-branch clobber) is preserved intact — this step only prunes the pileup that model produced, it does not reintroduce a shared branch.

### 3. `sources.yaml`

`tonone` + `hyperflow` now carry `curated: true` with inline docs explaining the freeze and the planned upstreaming.

### 4. Validator fairness (iel-62j) — `scripts/validate-skills-schema.py`, schema 3.15.0

Enterprise/marketplace section checks now credit **equivalent** non-Intent-Solutions heading names so external contributors aren't failed for standard-but-different wording:

| IS heading | Credited equivalents |
|---|---|
| `## Overview` | `## Summary`, `## Capabilities` |
| `## Instructions` | `## Usage` |
| `## Output` | `## Returns` |
| `## Error Handling` | `## Troubleshooting` |
| `## Resources` | `## References` |

**UNCHANGED (NON-NEGOTIABLE):** the 8-field `ALWAYS_REQUIRED` set, the tier model, error-vs-warning semantics, and the frontmatter `capabilities` field **ban** — only `## Capabilities` as a *heading* is credited; `capabilities` as a frontmatter *field* remains an error.

### 5. Two Xquik sources activated

Mirrored + catalogued from the Xquik dogfood (see `000-docs/693-AA-AACR`):

- `hermes-tweet` → `plugins/community/hermes-tweet`
- `x-twitter-scraper` → `plugins/api-development/x-twitter-scraper`

`mytradeledger-skills` stays **registered-but-inactive** by decision.

## Respectful-contributor protocol

Curated / long-time contributors are handled respectfully — peer-to-peer, credit-preserving, never extractive:

1. **A friendly issue first**, on the contributor's own repo — in the spirit of: *"we featured your plugin and hardened its frontmatter to our A-grade bar — would you be open to a PR upstreaming it?"* No surprise PRs.
2. **Then a PR they own and merge.** They decide; credit is preserved; the improvement lands in *their* repo, and the mirror inherits it.

**HARD RULE:** any contributor-facing post (issue text, PR body, comment) gets **Jeremy's wording sign-off before it is posted.** Tone toward contributors is the Xquik-dogfood posture — a peer contributing back, never an owner reclaiming.

## Decisions Jeremy made this session

- **Upstream `tonone` + `hyperflow`** (get them A-grade in their own repos, then lift the `curated: true` freeze).
- **Activate the 2 Xquik sources** (`hermes-tweet`, `x-twitter-scraper`); **hold `mytradeledger-skills`** inactive.
- **Implement iel-62j now** (heading-equivalence fairness, schema 3.15.0).

## What does NOT change

- **The human review gate stays.** The sync proposes an automated PR; a human still reviews and disposes (~1/10 historical merge rate). No auto-merge is introduced.
- **The unique-per-run-branch model stays** (per `000-docs/691-AT-AUDT`). The auto-close step prunes stale PRs; it does not revert to a shared branch.
- **The 8-field `ALWAYS_REQUIRED` set, tier model, error-vs-warning semantics, and the `capabilities`-field ban stay** — see `000-docs/SCHEMA_CHANGELOG.md` § NON-NEGOTIABLES.
- **External is still a minority augment.** ~403 of 454 plugins are in-repo IS work; the sync remains a side-channel, not the core marketplace.

## Status

**LOCKED 2026-06-30** on branch `feat/external-sync-mirror-model`. The curated freeze, pileup auto-close, iel-62j fairness, and the two activated Xquik sources are landed and verified. Off-ramp for `tonone`/`hyperflow`: upstream the A-grade improvement, then remove `curated: true`. Re-opening the policy requires a new AT-DECR.

## References

- Prior pipeline audit + hardening: `000-docs/691-AT-AUDT-sync-external-pipeline-audit-and-hardening.md`
- Xquik dogfood AAR: `000-docs/693-AA-AACR-xquik-external-author-dogfood-and-tooling-fixes-2026-06-30.md`
- Reverted uplift: PR #881
- Source registry: `sources.yaml`
- Schema non-negotiables: `000-docs/SCHEMA_CHANGELOG.md` § NON-NEGOTIABLES
