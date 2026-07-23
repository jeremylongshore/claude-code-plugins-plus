# PRD: intent-labs-pack

**Author:** Jeremy Longshore
**Date:** 2026-07-23
**Status:** Active

## Problem

The Intent Eval Platform's nightly skill-eval roster must check out skills from a public git pin. Two load-bearing labs skills — `audit-tests` and `validate-skillmd` — lived only under `~/.claude/skills` on founder machines, so CI could not evaluate them and the signed dogfood loop never graded the tools we use on our own marketplace.

## Target users

| User | Context | Primary need |
| --- | --- | --- |
| Nightly j-rig roster | GitHub Actions on MiniMax/DeepSeek | Stable public path + eval-spec for each skill |
| Marketplace installers | Claude Code plugin install | Discoverable pack with honest docs |
| Intent Solutions engineers | Dogfooding audit-tests / validate-skillmd | Same skill content as founder `~/.claude` installs |

## Success criteria

1. Both skills are installable from `intent-labs-pack` via the marketplace catalog.
2. j-rig can pin paths under this pack and run stub + live evals.
3. Marketplace validation grades each skill without ERROR-level body/frontmatter failures.

## Functional requirements

- **FR-1:** Ship `audit-tests` with references, shared-refs, scripts, and j-rig `eval-spec.yaml`.
- **FR-2:** Ship `validate-skillmd` with j-rig `eval-spec.yaml`.
- **FR-3:** Register the pack in `.claude-plugin/marketplace.json`.
- **FR-4:** Do not duplicate `skill-creator` (already under `plugins/skill-enhancers/skill-creator`).

## Non-goals

- Replacing founder `~/.claude/skills` copies (those remain the edit surface until a sync story exists).
- Auto-promoting into `skills/.curated/` (that mirror is grade-driven via freshie).
