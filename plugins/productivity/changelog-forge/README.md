![hero](./assets/hero.svg)

# changelog-forge

**Turn your conventional commits into a real CHANGELOG entry. Plus a semver bump suggestion.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 13 passing](https://img.shields.io/badge/tests-13%20passing-success.svg)](./tests)

> **TL;DR:** `/changelog-forge` → grouped CHANGELOG section + suggested `major | minor | patch`, derived from your commit history since the last tag.

## Why this exists

CHANGELOGs that are written *during* a release are always wrong. The person writing them has forgotten half the work, and the half they remember they describe inaccurately. `changelog-forge` reads the commits since the last tag, groups them by conventional-commit type, surfaces every `BREAKING CHANGE`, and suggests the right semver bump — so the changelog tracks ground truth.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-changelog-forge ~/.claude/plugins/changelog-forge
```

Restart Claude Code; the slash command `/changelog-forge` appears.

## Quick start

```sh
/changelog-forge
```

Or directly:

```sh
python3 scripts/forge.py --format md
python3 scripts/forge.py --from v1.2.0 --to HEAD --format json
python3 scripts/forge.py --write                  # prepend (idempotently) to CHANGELOG.md
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--cwd` | cwd | Repo path |
| `--from` | last tag | Base ref/tag |
| `--to` | `HEAD` | End ref |
| `--format` | `md` | `md` or `json` |
| `--write` | off | Prepend (idempotently) to `CHANGELOG.md`; correctly inserts AFTER any leading `# Changelog` title |
| `--changelog` | `CHANGELOG.md` | Target file |

## Conventional-commit reference

Headers parsed as `<type>(<scope>)!: <subject>`. Recognised types:

`feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `revert`.

Anything else falls into an `other` bucket.

Breaking changes are detected when:

- the header has `!` before `:` (e.g. `feat!: drop /v0`), or
- the body contains `BREAKING CHANGE: …`.

## Semver bump heuristic

| Trigger | Bump |
|---|---|
| any breaking | `major` |
| any `feat` | `minor` |
| any `fix` / `perf` | `patch` |
| everything else | `patch` (effectively a no-op) |

When a base tag is present (e.g. `v0.4.2`), the JSON output also returns `suggested_version`.

## Example output (markdown)

```
## [Unreleased] - 2026-05-16

### Features
- **api**: paginate search endpoint (a1b2c3d)

### Bug Fixes
- handle null user in cookie middleware (e4f5g6h)

### Performance
- cache token-bucket counters (12ab34c)

_Suggested bump: **minor**_
_Suggested version: **0.5.0**_
```

## Idempotency

Running `--write` twice with the same input produces the same file — both the diff and the SHA are stable. There's a dedicated test (`test_write_changelog_idempotent`) that runs the writer twice and asserts byte-for-byte equality.

## Limitations

- Flat conventional-commit grammar — multi-paragraph footers (`Refs:` blocks etc.) aren't merged.
- `--write` only manages the `## [Unreleased]` block. Promoting it to a versioned section at release time is a manual step.

## Examples

Step-by-step walkthroughs with real input fixtures and the helper's actual output live in [`examples/`](./examples/README.md). Three or four scenarios per plugin — from the happy path to the edge cases the test suite guards.

## Part of the pluginpool family

Ten focused Claude Code plugins for everyday productivity:
[commit-narrator](https://github.com/mturac/pluginpool-commit-narrator) ·
[pr-storyteller](https://github.com/mturac/pluginpool-pr-storyteller) ·
[test-gap](https://github.com/mturac/pluginpool-test-gap) ·
[deps-doctor](https://github.com/mturac/pluginpool-deps-doctor) ·
[env-lint](https://github.com/mturac/pluginpool-env-lint) ·
[secret-guard](https://github.com/mturac/pluginpool-secret-guard) ·
[standup-gen](https://github.com/mturac/pluginpool-standup-gen) ·
[todo-harvest](https://github.com/mturac/pluginpool-todo-harvest) ·
[flaky-detector](https://github.com/mturac/pluginpool-flaky-detector) ·
[changelog-forge](https://github.com/mturac/pluginpool-changelog-forge)

## License

MIT — see [`LICENSE`](./LICENSE). Contributions welcome.
