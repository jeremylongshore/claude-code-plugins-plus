---
filing_code: DR-GUID-SKILL-SUBMISSION-STANDARD-2026-07-07
date: 2026-07-07
status: active
scope: The tiered submission-documents standard + issue-before-PR intake for every plugin/source submission — external and Intent Solutions' own
related:
  - templates/skill-docs/ (the four fill-in templates + tier matrix)
  - 000-docs/698-TQ-SECU-external-sync-threat-model.md (threat model for synced sources)
  - 000-docs/699-DR-GUID-external-source-vetting-playbook.md (source vetting procedure)
  - STANDARDS.md (8-field marketplace frontmatter rubric)
  - "GitHub issue #984 — marketplace quality pipeline umbrella"
---

# Skill Submission Standard (tiered documents + issue-before-PR)

## Purpose

The marketplace already gates *validity* (validators, security scan, 8-field frontmatter).
This standard gates *value*: every submission arrives with just enough written proof that
the problem is real, the design was deliberate, and the claim matches the tier. The
documents are a filter that helps contributors sharpen a submission — not a wall that
rejects them.

## 1. Issue-before-PR (required)

Every plugin/source submission **starts as a GitHub issue** using the
[plugin-submission template](../.github/ISSUE_TEMPLATE/plugin-submission.yml), which
captures the PRD-level answers (problem, target users, success criteria, top functional
requirements) up front. The PR must link that issue (`Closes #N` / `Refs #N`).

A PR that arrives without a linked submission issue is not rejected — it gets a comment
asking for one, and review pauses until it exists. (Decision: Jeremy, 2026-07-07.)

## 2. Tier → required documents

Templates: [`templates/skill-docs/`](../templates/skill-docs/). Docs live in the plugin
directory as `docs/PRD.md`, `docs/ADR.md`, etc. The same matrix applies to Intent
Solutions' own skills.

| Tier | What it covers | Required docs |
|------|----------------|---------------|
| **Micro-skill** | a single command or skill, no scripts | `PRD.md` (short form OK) |
| **Standard plugin** | skills plus scripts/commands | `PRD.md` + `ADR.md` |
| **Pack / flagship / featured / paid-tier** | multi-skill packs, featured picks, anything sold | `PRD.md` + `ADR.md` + `ONE-PAGER.md` (+ `CFO-ONE-PAGER.md` where money is the pitch) |

Enforced in CI: the `check-submission-docs` gate (`scripts/check-submission-docs.mjs`,
blocking via `ci-required`) fails a PR that adds a new plugin directory without its
tier's documents; external mirrors (`.source.json`) are exempt — their docs live
upstream. `CFO-ONE-PAGER.md` stays review-enforced (the gate cannot judge "money is
the pitch" deterministically).

## 3. Eligibility: listing vs featuring

- **Listing** (in the catalog): a valid plugin, an honestly declared tier with the
  matching docs, and — for synced sources — the source vetted per the
  [external-source vetting playbook (699)](699-DR-GUID-external-source-vetting-playbook.md).
- **Featuring** (spotlight, homepage, Hall of Fame): A-grade at marketplace tier
  (8-field frontmatter per [STANDARDS.md](../STANDARDS.md)) **plus** the full doc set
  for the pack/flagship tier **plus** an editorial pick. Featuring is earned, and we
  help authors earn it (see the rubric below).

## 4. Sync-model rubric (case-by-case, the curation doctrine)

How an external plugin's quality improvements flow is decided per source, not by one
global policy:

| Situation | Model |
|-----------|-------|
| Responsive maintainer + thin consumer | **Upstream PR** they own and merge; mirror stays SHA-pinned via `sources.lock.json` |
| We're featuring it / our name is on its quality / maintainer slow-or-unknown | **Mirror + `curated: true`** — we harden our copy, frozen from sync, author credited |
| Full adoption (we take over maintenance) | **Vendor** into this repo |

The upstream PR is **always a courtesy, never a blocker** — a stalled or silent upstream
never delays listing or featuring. Curated copies join a periodic reconcile that pulls
upstream **security fixes** into the frozen copy so hardening never means falling behind
on safety.

## 5. Canonical sources (cited, not restated)

- [698 — external-sync threat model](698-TQ-SECU-external-sync-threat-model.md): what the
  machine layers can and cannot prove about synced content.
- [699 — external-source vetting playbook](699-DR-GUID-external-source-vetting-playbook.md):
  the human procedure for listing, reviewing, and suspending sources.
- [STANDARDS.md](../STANDARDS.md): the 8-field marketplace frontmatter rubric and where
  the machine-readable source of truth lives.

## 6. Common reviewer findings (read before pushing)

These are the issues that have blocked otherwise-mergeable PRs in the 2026-07 review
pass. Each one is a five-minute fix; together they account for the majority of review
comments. Treat this as a pre-flight checklist.

### 6.1 Branch off `origin/main` — the catalog will pollute otherwise

The most common P0 across external submissions: the branch was forked from a stale
commit, and GitHub computes the diff as *deleting almost the entire repo*. Symptom:
`marketplace.extended.json` shows a diff of hundreds of lines, most of which are
unrelated `version` bumps and `maintainer` fields on other plugins.

**Fix before pushing:**

```bash
git fetch origin
git checkout -b feat/your-plugin origin/main
# ... add your plugin ...
git diff --stat origin/main...HEAD -- .claude-plugin/marketplace.extended.json
# ↑ should be < 50 lines for a single new plugin entry
```

Reference: the [#1080](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1080)
closure note about stale-branch pollution.

### 6.2 Anchor `sources.yaml` `include` patterns with a leading `/`

The source-intake check rejects unanchored patterns outright. The sync matcher
also matches unanchored patterns at any depth (because the matcher auto-prefixes
`**/` to any pattern that doesn't start with `/` or `**`); this can admit nested
files from inside a plugin's sparse-checkout subtree. See
`scripts/sync-lint-ignores.mjs` and the `--check-source-anchoring` mode for the
exact behavior in this version.

**Wrong:**

```yaml
include:
  - 'SKILL.md'
  - 'README.md'
  - 'LICENSE'
```

**Right:**

```yaml
include:
  - '/SKILL.md'
  - '/README.md'
  - '/LICENSE'
```

For globs the same applies:

```yaml
include:
  - '/skills/**'           # not 'skills/**'
  - '/.claude-plugin/**'
```

Reference: review notes on #1083 and #1103.

### 6.3 `allowed-tools` scoping and accuracy

The marketplace-tier validator checks both directions of the `allowed-tools` field:

- **Don't over-declare.** Every tool declared in `allowed-tools` must actually
  appear in the body. Declaring tools the skill never uses flags the
  `allowed-tools-accuracy` tier-2 check as a warning.
- **Don't under-declare.** If the body uses `curl` or `Bash`, the frontmatter
  must declare it; bare `Bash` in the body with `allowed-tools: Read, WebFetch`
  in the frontmatter will trip the validator.
- **Pure-reasoning skills still need the field.** Confirm with
  `validate-skills-schema.py --marketplace` which empty/short form is accepted
  (the project's exact empty-string semantics in this field are validator-specific
  and may change; do not codify them in your head and skip the validator).

Run the validator locally and treat its output as the source of truth.

### 6.4 SKILL.md body sections for marketplace tier

The marketplace-tier validator checks that the SKILL.md body contains a set of
top-level sections that a Claude Code reader can navigate.

**Snapshot — confirm each row against the validator version you run; the
validator is the source of truth.** The canonical names vary by validator
version; the table below is the synonym list a contributor should recognize.
**The structural rule is: use these as top-level `##` headings so the
validator's section-name matcher can find them in order.** A "Phase 0 / Phase 1
/ ..." workflow is valid content but the *outer* headings should be recognized
names with the phase breakdown nested underneath.

| Required heading | Accepted synonyms (verify against the validator you run) |
|------------------|----------------------------------------------------------|
| `## Overview` | `## Summary`, `## About`, `## What it does`, `## Introduction`, `## Purpose`, `## Capabilities` |
| `## Prerequisites` | `## Requirements`, `## Setup`, `## Dependencies`, `## Installation` |
| `## Instructions` | `## Usage`, `## How to use`, `## How it works`, `## Steps`, `## Workflow`, `## Guide`, `## Getting started` |
| `## Output` | `## Outputs`, `## Returns`, `## Results`, `## Output format`, `## Response` |
| `## Error Handling` | `## Errors`, `## Troubleshooting`, `## Failure modes`, `## Edge cases`, `## Limitations` |
| `## Examples` | `## Example`, `## Sample`, `## Samples`, `## Usage examples`, `## Example usage` |
| `## Resources` | `## References`, `## See also`, `## Links`, `## Further reading`, `## Related`, `## Additional resources` |

If the synonym list drifts, the validator output is the source of truth.
Reference: D-grade pre-screen on #1070 demonstrated what the section-name
mismatch costs.

### 6.5 Don't hand-edit generated catalog artifacts

`marketplace.json`, generated per-plugin `package.json` files, and the README TOC are
*derived* from `marketplace.extended.json` via `pnpm run sync-marketplace`. Hand-edits
will be overwritten by the next sync and will be flagged on the next review.

Two exceptions:
- External contributors should typically submit via the normal intake; if a direct
  edit to `marketplace.extended.json` is acceptable for your submission, the
  maintainer will run `sync-marketplace` after merge.
- `sources.yaml` is itself a source-of-truth file (Path B). Edit it directly.

### 6.6 External mirrors: register both files, not one

Path B mirrors use **two files** that work together. Do not collapse them into one:

- **`sources.yaml`** is the catalog-level registry. It tells the sync engine
  *which* upstream repos to clone, *where* in `plugins/` to mirror them, and
  governs the per-source metadata (category, verified, curated, license).
  Omitting this means the sync engine will never pick up your mirror.
- **`.source.json`** is the per-plugin marker that the supply-chain guardrail
  keys on. It tells the next maintainer (and the audit pipeline) that *this
  directory* is a mirror of an external repo, records the upstream path/branch,
  and is what triggers the orphan-prune + ownership semantics in
  `[698] external-sync threat model`. Omitting this means future edits land
  without the "this is a mirror" warning, and the engine can no longer
  distinguish locally-hardened code from upstream code.

If you want your plugin to be auto-synced from upstream, **add both**: a
`sources.yaml` entry that drives the sync, plus the `.source.json` marker that
marks the mirror. If you only want the marker (no auto-sync), keep the
`.source.json` so the supply-chain guardrail still works. The review process
treats them as separate concerns; see
`[709] reviewing external PRs` for the lane definitions.

### 6.7 `entry` field in `plugin.json`

**Snapshot of the field list as of this PR; open the schema your validator runs
against before relying on this list.** The `plugin.json` schema is enforced by
the marketplace validator and the plugin loader. A top-level `entry: "src/index.js"`
is not a recognized field under the schema versions this doc has been verified
against; consumers will ignore it. If the entry point matters for a plugin you
ship, the supported locations are:

- For an MCP server: `mcpServers.<name>.args` (relative or absolute path).
- For a CLI runner: `commands[].path` or a `package.json` `bin` entry that
  `npx -y <package>` resolves.

### 6.8 Don't bump versions you didn't change

When adding a new skill to a pack, the existing skills' `version:` fields should
stay where they are unless the skill's content actually changed. A pure metadata
bump on every file in a pack (e.g. `1.5.0 → 1.6.0` across 16 SKILL.md files when
only 2 new files were added) is a misleading signal to anyone pinning to a
specific skill version. Bump only the files that changed.

### 6.9 Nested arbitrary flags in `parseArguments`

When a runner needs to read flags before a positional path argument, use a
`for (let i = 0; i < args.length; i++)` loop that skips `--flag` and `--flag value`
with `continue`, rather than `process.argv[2]` direct-access. The direct-access
pattern silently aliases the flag to the input path when the flag is placed first.

### 6.10 Don't claim a grade you didn't earn

The PR description should be a true reflection of what the local validator
outputs. Don't write "A (99/100)" if `validate-skills-schema.py --marketplace`
returns "A (95/100)". Reviewers will run the validator; rounding up by 4 points
is a small thing but it costs trust quickly.
