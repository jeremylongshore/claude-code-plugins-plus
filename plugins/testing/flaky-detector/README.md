![hero](./assets/hero.svg)

# flaky-detector

**Run your test command N times. Find out which tests don't always agree with themselves.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 11 passing](https://img.shields.io/badge/tests-11%20passing-success.svg)](./tests)

> **TL;DR:** `/flaky-detector --cmd "pytest -v" --runs 10` → per-test flakiness %, sorted worst-first, ready to triage.

## Why this exists

A test that fails 1-in-20 wastes more team time than a test that never fails. CI flakes erode trust; everyone learns to "just re-run it". This tool runs your suite N times, parses pass/fail per test, and tells you exactly which tests are flaky and at what rate — so you can decide: rerun, isolate, mark `@pytest.mark.flaky`, or fix the underlying race.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-flaky-detector ~/.claude/plugins/flaky-detector
```

Restart Claude Code; the slash command `/flaky-detector` appears.

## Quick start

```sh
python3 scripts/flaky.py --cmd "pytest -v" --runs 10 --format md
python3 scripts/flaky.py --cmd "go test ./..." --runs 20 --parallel 4 --out report.json
python3 scripts/flaky.py --cmd "jest --ci" --parser jest --runs 5
```

> Tip: prefer `pytest -v` over `pytest -q` so every result lands on its own line.
> If you use `-q`, flaky-detector still picks up the tail `FAILED path::test` summary
> lines and exits non-zero with a warning rather than reporting a false green.

## Flags

| Flag | Default | Description |
|---|---|---|
| `--cmd` | required | The test command (single line, no shell wrapping) |
| `--runs` | `10` | How many times to invoke the command |
| `--parallel` | `1` | Concurrent runs (only safe for parallel-clean suites) |
| `--parser` | `auto` | `pytest`, `jest`, `gotest`, `tap`, or `auto` |
| `--out` | _none_ | Write JSON report to this path |
| `--format` | `json` | `json` or `md` |

## Supported parsers

| Parser | Matches |
|---|---|
| `pytest` | `tests/foo.py::test_bar PASSED|FAILED|ERROR|SKIPPED` plus the `-q` tail summary |
| `jest` / `vitest` | `✓ name`, `✗ name`, `PASS file`, `FAIL file` |
| `gotest` | `--- PASS:`, `--- FAIL:`, `--- SKIP:` |
| `tap` | `ok N - name`, `not ok N - name` |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No flakies, no always-failing |
| `1` | At least one test is flaky (`0 < flakiness_pct < 100`) |
| `2` | At least one test is always-failing |
| `3` | Zero tests parsed but the runner reported activity — re-run with `-v` |

## Example output (markdown)

```
# Flaky-detector report (10 runs)

- flaky: **2**  |  always-failing: **0**  |  always-passing: 47

| test | pass | fail | flakiness % |
|---|---|---|---|
| tests/test_payment.py::test_idempotency | 6 | 4 | 40.0 |
| tests/test_search.py::test_index_warmup | 8 | 2 | 20.0 |
```

## Limitations

- `--parallel > 1` only works for parallel-safe suites; otherwise concurrent runs share state and lie.
- Streaming stdout from very long suites is buffered — be patient on the first run.
- The parser is tuned for default reporters. Custom plugins (pytest-rich, etc.) may need a tweak.

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
