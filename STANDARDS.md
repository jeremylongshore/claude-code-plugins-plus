# Standards

This page states which specifications this repository follows, where it deliberately
goes beyond them, and where the machine-readable source of truth lives. It links the
canonical documents instead of restating them — when this page and a linked document
disagree, the linked document wins.

## The floor: open specs we follow

Two upstream specifications define baseline validity for every skill in this repo:

1. [agentskills.io/specification](https://agentskills.io/specification) — the open
   Agent Skills standard that Claude Code follows. Requires only `name` and
   `description`; documents `license`, `compatibility`, `metadata`, and
   `allowed-tools` as optional.
2. [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) — Anthropic's
   Claude Code skills reference, the primary source for frontmatter field semantics.
   (API surface: [platform.claude.com Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).)

Both are intentionally permissive. Everything valid under this repo's rules is also
valid under both upstream specs — the overlay below is additive, never subtractive.

## The overlay: where we deliberately diverge

The Intent Solutions marketplace tier is intentionally stricter than the upstream
floor. The divergences, all documented in the
[schema changelog's NON-NEGOTIABLES](000-docs/SCHEMA_CHANGELOG.md) and the
[master spec](000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md):

- **8 required frontmatter fields**, not 2:
  `name`, `description`, `allowed-tools`, `version`, `author`, `license`,
  `compatibility`, `tags` (the `ALWAYS_REQUIRED` set). Upstream treats most of these
  as optional; the marketplace requires them for trust signals, downstream pinning,
  and legal clarity.
- **Missing required fields are ERRORS at marketplace tier**, not warnings. The gate
  is `scripts/validate-skills-schema.py`, run in CI by
  [`validate-plugins.yml`](.github/workflows/validate-plugins.yml).
- **`capabilities` as a frontmatter field is banned** (a `## Capabilities` _heading_
  is fine and is credited as an `## Overview` equivalent).
- **Heading-equivalence fairness for external contributors** — standard-but-different
  section names (`## Usage` for `## Instructions`, `## Troubleshooting` for
  `## Error Handling`, etc.) are credited, per the
  [mirror-by-default decision record](000-docs/694-AT-DECR-external-sync-mirror-by-default-model.md).

Changes to the required-field set, the tier model, or error-vs-warning semantics are
architectural and require explicit approval before landing — see the schema
changelog's "How we got here" section for why that rule exists.

## The direction: kernel single source of truth

The validator's hand-rolled field sets are converging on a machine-readable kernel:
the `authoring/v1` schema family in
[`@intentsolutions/core`](https://github.com/jeremylongshore/intent-eval-core)
(pinned exactly in `package.json`). The kernel's
[`schemas/authoring/v1/CHANGELOG.md`](https://github.com/jeremylongshore/intent-eval-core/blob/main/schemas/authoring/v1/CHANGELOG.md)
is canonical for authoring-contract semantics; this repo's schema changelog cites it
rather than duplicating rationale.

The conformance signal for that cutover is
[`kernel-shadow-validation.yml`](.github/workflows/kernel-shadow-validation.yml): it
runs the kernel's published JSON Schema over the same SKILL.md corpus the prose-spec
validator grades and reports the per-file AGREE/DISAGREE deviation rate. It is
**advisory by design** — report-only, not in the required-status set, and it never
blocks a merge. Promotion to a blocking gate is a separate, later cutover step.

## The catalog: two files, one source of truth

| File                                       | Role                                    | Hand-edit? |
| ------------------------------------------ | --------------------------------------- | ---------- |
| `.claude-plugin/marketplace.extended.json` | Source of truth for every catalog entry | Yes        |
| `.claude-plugin/marketplace.json`          | CLI-compatible catalog, auto-generated  | Never      |

`pnpm run sync-marketplace` regenerates `marketplace.json`, missing
`plugins/**/package.json` files, and the README AUTO-TOC block. The pre-commit hook
runs it automatically when the extended catalog is staged, and CI fails if any
derived file drifts. Authoring workflow: [CONTRIBUTING.md](CONTRIBUTING.md).

## External plugins: mirror by default

Externally-synced plugins (registered in `sources.yaml`, a small minority of the
catalog) follow **mirror by default · upstream improvements · never clobber**, per
the [decision record](000-docs/694-AT-DECR-external-sync-mirror-by-default-model.md):

- The contributor's own repo is the source of truth; the weekly sync mirrors it and
  opens a PR a human reviews. We do not locally edit a pure mirror.
- Quality improvements are **upstreamed** to the contributor's repo, not forked into
  a divergent local copy. A locally-hardened source is frozen with `curated: true`
  until the improvement lands upstream.
- Mirrored paths self-register their lint exclusions: the managed
  `sync-lint-ignores` block in `.markdownlint-cli2.jsonc` is generated from
  `sources.yaml` (via `scripts/sync-lint-ignores.mjs`), because upstream markdown
  style is the upstream maintainer's choice, not ours.

## Canonical documents

| Topic                                | Document                                                                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Required fields, tier model, history | [000-docs/SCHEMA_CHANGELOG.md](000-docs/SCHEMA_CHANGELOG.md)                                                                   |
| Full skills standard (master spec)   | [000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md](000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md)               |
| External-sync policy                 | [000-docs/694-AT-DECR-external-sync-mirror-by-default-model.md](000-docs/694-AT-DECR-external-sync-mirror-by-default-model.md) |
| Contribution requirements            | [CONTRIBUTING.md](CONTRIBUTING.md)                                                                                             |
| Security policy                      | [SECURITY.md](SECURITY.md)                                                                                                     |
