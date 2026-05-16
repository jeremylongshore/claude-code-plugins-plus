![hero](./assets/hero.svg)

# standup-gen

**Skip the "what did I do yesterday?" tax. Generate the answer from git.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 8 passing](https://img.shields.io/badge/tests-8%20passing-success.svg)](./tests)

> **TL;DR:** `/standup-gen` → markdown `Yesterday / Today / Blockers` block, pre-filled from your commits across every repo you care about.

## Why this exists

Standup writes itself if you only let it. Most engineers spend 5–10 minutes every morning scrolling commits to remember what they shipped — across two or three repos, across a long weekend, across timezones. `standup-gen` queries each repo's `git log` since the last business day, attributes commits to you (or the team), and hands you a clean draft. Claude fills in *Today (planned)* and *Blockers* if context allows.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-standup-gen ~/.claude/plugins/standup-gen
```

Restart Claude Code; the slash command `/standup-gen` appears.

## Quick start

```sh
/standup-gen
```

Or directly:

```sh
python3 scripts/standup.py --format md
python3 scripts/standup.py --repos /work/api,/work/web --format md
python3 scripts/standup.py --since 2026-05-13 --author all --format json
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--repos` | cwd | Comma-separated repo paths |
| `--since` | last business day | ISO date or `yesterday` |
| `--until` | today (00:00, exclusive) | ISO date upper-bound, or `none` to drop the bound |
| `--author` | `git config user.email` | Email filter, or `all` |
| `--format` | `json` | `json` or `md` |

The default `--until=today` is intentional — without it, "yesterday" silently leaks today's commits into the standup.

## Example output

```markdown
# Standup — 2026-05-16

## Yesterday
### api
- 2026-05-15 `4c3d39e` feat: add login throttle
- 2026-05-15 `8d424a0` test: cover replay path
### web
- 2026-05-15 `93a8826` fix: navbar overlap on small screens

## Today (planned)
- TODO

## Blockers
- TODO
```

## How it works

1. For each repo, runs `git log --since=<date> --until=<date>` with your email as `--author`.
2. Groups commits by date and renders the markdown skeleton.
3. Claude can then propose `Today (planned)` items from in-flight files, and flag obvious blockers from commit messages (`WIP:`, `revert`, etc.).

## Limitations

- Only counts authored commits — co-authored trailers aren't matched.
- "Yesterday" is calendar-day, not work-session-day. Burnouts who commit at 3am may want `--since=yesterday`.
- Multi-repo only — no GitHub PR/issue activity (yet).

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
