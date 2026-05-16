![hero](./assets/hero.svg)

# test-gap

**Surface the lines you just changed that have zero test coverage — before the PR review does.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 7 passing](https://img.shields.io/badge/tests-7%20passing-success.svg)](./tests)

> **TL;DR:** `/test-gap` → markdown table of files where your diff added lines that nothing tests yet.

## Why this exists

Repo-wide coverage percentages are useless on a PR — what matters is whether the *lines you just touched* are covered. CI rarely tells you that, and "100% line coverage" isn't the target anyway. `test-gap` intersects your branch's diff with an existing coverage report and shows you the gap, sorted worst-first.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-test-gap ~/.claude/plugins/test-gap
```

Restart Claude Code; the slash command `/test-gap` appears.

## Quick start

```sh
# After running your test suite with coverage:
python3 -m pytest --cov --cov-report=xml         # produces coverage.xml
/test-gap                                         # in Claude Code
```

Or directly:

```sh
python3 scripts/gap.py --format md
python3 scripts/gap.py --base develop --report build/lcov.info
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--base` | `main` (falls back to `master`) | Diff against this branch |
| `--report` | auto-detect | Path to `coverage.xml`, `lcov.info`, or `coverage.json` |
| `--format` | `json` | `json` or `md` |

## Supported coverage formats

| Format | Where it comes from |
|---|---|
| Cobertura `coverage.xml` | `pytest-cov`, `pytest --cov-report=xml`, `coverage xml` |
| `lcov.info` | `jest --coverage`, `c8`, Istanbul |
| `coverage.json` | `coverage json` |

## Example output (markdown)

```
| file | changed lines | uncovered | uncovered lines |
|---|---|---|---|
| src/auth/refresh.py | 42 | 11 | 81-83, 102, 117-122 |
| src/util/parse.py | 15 | 7 | 22-28 |
```

## How it works

1. Reads `git diff --unified=0 <base>..HEAD` and collects the added line numbers per file.
2. Parses the coverage report into a `{file: {covered_lines}}` map.
3. Intersects: any added line not in the covered set is reported as a gap.
4. Sorts the table by uncovered-count descending so the worst offenders surface first.

## Limitations

- Coverage is taken at face value — it doesn't know about branch coverage or test quality.
- Cobertura paths must match diff paths; configure your runner to emit project-relative paths.
- Empty diffs and no-test repos are handled gracefully (no output).

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
