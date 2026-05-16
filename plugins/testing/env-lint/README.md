![hero](./assets/hero.svg)

# env-lint

**Catch missing/extra env-var keys before they bite you in prod. Never prints values.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 7 passing](https://img.shields.io/badge/tests-7%20passing-success.svg)](./tests)

> **TL;DR:** `/env-lint` → "you're missing `STRIPE_WEBHOOK_SECRET` in `.env.local` (referenced in `.env.example`)" — without ever logging the secret value.

## Why this exists

Every team has the same outage: someone adds a new env var to `.env.example`, forgets to mention it in the PR, and a teammate's local server quietly 500s on a code path that needs it. Or worse, prod is missing a key. `env-lint` diffs your live env file against `.env.example` and tells you which keys are missing or extra — and *only* the keys, never the values. Safe to paste in chat, safe to log to CI.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-env-lint ~/.claude/plugins/env-lint
```

Restart Claude Code; the slash command `/env-lint` appears.

## Quick start

```sh
/env-lint
```

Or directly:

```sh
python3 scripts/envlint.py --format md
python3 scripts/envlint.py --example .env.example --env .env.production
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--example` | auto-detect | Path to template (`.env.example`) |
| `--env` | auto-detect | Path to actual env file |
| `--format` | `json` | `json` or `md` |

When run without `--example/--env`, it scans the cwd for known pairs: `(.env, .env.example)`, `(.env.local, .env.example)`, `(.env.production, .env.example)`.

## Example output

```
# env-lint report

## .env.example ↔ .env.local
- **missing in env**: STRIPE_WEBHOOK_SECRET, SENTRY_DSN
- **extra in env**: LEGACY_API_KEY
- **empty values for**: REDIS_URL
```

## Safety guarantee

A test in the suite (`test_never_emits_values_in_json_or_markdown`) writes a fake value `SUPERSECRETVALUE123` into a temp `.env` and asserts that string never appears in either the JSON output or the markdown report. The CI badge above represents that invariant.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All required keys present (extras are warnings, not errors) |
| `1` | At least one required key is missing |

## How it works

1. Parses each `.env` file as `KEY=VALUE` (comments and blank lines skipped).
2. Computes the key-set difference both ways.
3. Reports missing keys (template has them, env doesn't), extra keys (env has them, template doesn't), and empty values.

## Limitations

- Doesn't expand `${VAR}` references — it only checks key presence.
- Quoted values are detected as "present" even if the quoted content is empty (`KEY=""` is *empty*, not missing).
- Custom env-file naming conventions need explicit `--example/--env`.

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
