![hero](./assets/hero.svg)

# commit-narrator

**Write commit messages that say *why*, not just *what*.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 6 passing](https://img.shields.io/badge/tests-6%20passing-success.svg)](./tests)

> **TL;DR:** `git add -p && /commit-narrator` → a conventional-commit message with a real rationale, not "fix stuff".

## Why this exists

Most "AI commit message" tools paraphrase the diff back at you. That's noise. A good commit message answers *why* the change was made, grounded in what the diff actually proves. This plugin runs a deterministic Python helper to classify the change and assemble the skeleton, and then leaves Claude to fill in the rationale from the diff itself — no LLM guesses about your repo's intent.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-commit-narrator ~/.claude/plugins/commit-narrator
```

Restart Claude Code; the slash command `/commit-narrator` appears.

## Quick start

```sh
git add -p
/commit-narrator
```

Or invoke the helper directly:

```sh
git diff --staged | python3 scripts/narrate.py --diff -
python3 scripts/narrate.py --format json
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--diff PATH` / `-` | `git diff --cached` | Read diff from path or stdin |
| `--format` | `text` | `text` or `json` |

## Example output

```text
feat(api): add login throttle

Changed files:
- src/api/auth.py
- tests/test_auth.py

Throttle prevents brute-force enumeration on the /login endpoint by
rate-limiting on (ip, email) — the abuse pattern surfaced in the
2026-Q2 incident review.
```

## How it works

1. Reads the staged diff (or a path you give it).
2. Classifies the change type — `feat / fix / refactor / docs / test / chore / perf` — using path patterns and patch-hunk heuristics.
3. Derives a scope from the most-touched top-level directory.
4. Emits a conventional-commit subject plus a body listing changed files and a placeholder `WHY` line.
5. Claude reads the helper's output and the diff, then replaces the placeholder with rationale that the diff actually supports.

## Limitations

- Heuristics are intentionally conservative. You'll get `chore` for messy mixed diffs — that's a signal to split the commit, not a bug.
- The helper itself never calls a network service; only the slash command's Claude pass adds language.

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
