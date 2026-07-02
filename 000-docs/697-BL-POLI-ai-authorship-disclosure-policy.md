# AI-Authorship Disclosure Policy

**Filing:** 697-BL-POLI · **Effective:** 2026-07-02 · **Status:** Active
**Scope:** this repository (`claude-code-plugins-plus-skills`) and the plugins,
skills, agents, and documentation published from it.

## Purpose

This repository publishes a large catalog of Claude Code plugins and skills.
Users and contributors deserve a plain statement of how that content is
authored, who is accountable for it, and what gates it passes before it ships.
This document is that statement. It is factual disclosure, not marketing.

## 1. Intent Solutions-authored content is AI-assisted, human-directed

Plugins, skills, agents, and docs authored by Intent Solutions in this repo are
built **AI-assisted under human direction and review**. Concretely, that means:

- **A human decides what gets built and why.** AI tooling drafts and iterates;
  it does not choose the roadmap, the required-field standards, or what merges.
- **Deterministic validator gates.** Every skill and agent is checked by the
  in-repo validator (`scripts/validate-skills-schema.py`) at marketplace tier,
  where missing required fields are errors, not warnings.
- **CI checks on every pull request.** Plugin validation, markdown/shell/Python/
  TypeScript lint, secret scanning, CodeQL, actionlint, link checks, and test
  suites run in `.github/workflows/` and gate the merge.
- **Behavioral evals via j-rig.** Beyond static checks, skills can be exercised
  through the j-rig behavioral-eval harness before being graded
  production-ready; graded artifacts record their eval evidence.
- **Human merge decisions.** No AI-drafted change lands on `main` without a
  human owning the merge. Automated pipelines *propose* (e.g. sync PRs); a
  human *disposes*.

AI assistance is a production tool here, the same way a compiler or linter is.
Accountability for what ships stays with the human maintainer.

## 2. Mirrored external plugins keep their upstream authorship

A minority of the catalog is externally sourced and mirrored from the original
authors' repositories under the **mirror-by-default** model (decision record
`000-docs/694-AT-DECR-external-sync-mirror-by-default-model.md`):

- Mirrored plugins carry their **upstream authors' provenance**. We do not
  re-attribute, re-badge, or claim authorship of mirrored work.
- Whether an upstream author used AI in their own work is their disclosure to
  make, not ours. We disclose our pipeline; we do not speak for theirs.
- When we want a mirrored plugin raised to this repo's standard, the
  improvement is offered **upstream** to the original author rather than held
  as a silently divergent local copy.

## 3. Commit and pull-request attribution

- Commits and pull requests in this repository are signed by the **human
  repository owner**. The repo does not use AI-model co-author trailers
  (no `Co-Authored-By: <model>` lines) — the human signature is the
  accountability line, per this policy and the review gates above.
- Automated pipelines that open PRs (external-plugin sync, dependency and
  version bumps) are labeled as automation and still require human review
  before merge.

## 4. Where the quality bar lives

The standards that AI-assisted work must clear are written down and versioned:

- **`000-docs/SCHEMA_CHANGELOG.md`** — the validator's changelog, including the
  NON-NEGOTIABLES section: the required-field set, the errors-not-warnings
  marketplace tier, and the rule that architectural changes to those semantics
  need explicit human approval before landing.
- **Marketplace-tier validation** — the strictest validator tier, applied to
  content published to the marketplace; it sits intentionally above the
  permissive upstream floor.
- **CI as enforcement** — the gates travel with the repo, so a fork or fresh
  clone reproduces the same checks.

Changes to the quality bar itself are recorded in the schema changelog and are
never made silently by AI tooling.

## 5. Questions and contact

Questions about this policy, a specific plugin's provenance, or a suspected
attribution error: open an issue on this repository (see the README for the
issue tracker and community links; security-sensitive reports go through
`SECURITY.md`).

## Review

This policy is reviewed when the authoring pipeline materially changes (new
eval harness, new sync model, new attribution convention). Amendments are
committed as edits to this file with the change visible in git history.
