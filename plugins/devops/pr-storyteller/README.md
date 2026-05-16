![hero](./assets/hero.svg)

# pr-storyteller

**Stop writing PR descriptions from a blank cursor. Generate a real one in seconds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 6 passing](https://img.shields.io/badge/tests-6%20passing-success.svg)](./tests)

> **TL;DR:** `/pr-storyteller` → PR title + summary + test plan, drafted from your actual commits and diff.

## Why this exists

PR descriptions decay the moment they leave the author's keyboard. The reviewer skims, the author forgets to update later, and three months in nobody knows *why* the PR landed. `pr-storyteller` gives you a draft grounded in the commit history and the diff against your base branch — Claude then writes the prose, you tweak, you ship.

## Install (Claude Code)

```sh
git clone https://github.com/mturac/pluginpool-pr-storyteller ~/.claude/plugins/pr-storyteller
```

Restart Claude Code; the slash command `/pr-storyteller` appears.

## Quick start

```sh
/pr-storyteller
```

Or invoke the helper directly:

```sh
python3 scripts/story.py
python3 scripts/story.py --base develop
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--base` | `main` (falls back to `master`) | Base branch to diff against |

## Example output (JSON)

```json
{
  "commits": [
    {"hash": "abc1234", "subject": "feat(auth): rotate refresh tokens"},
    {"hash": "def5678", "subject": "test(auth): cover stale-token replay"}
  ],
  "files_changed": [
    {"path": "src/auth/refresh.py", "additions": 84, "deletions": 12},
    {"path": "tests/test_refresh.py", "additions": 41, "deletions": 0}
  ],
  "suggested_title": "feat(auth): rotate refresh tokens"
}
```

Claude turns that into:

```markdown
### Summary
- Rotate the refresh-token secret on every successful refresh
- Reject stale refresh tokens that have already been redeemed

### Changes
- `src/auth/refresh.py` — token rotation + replay rejection
- `tests/test_refresh.py` — coverage for the replay path

### Test plan
- [ ] Successful login → both access and refresh tokens issued
- [ ] Reuse a refresh token → 401 + token family invalidated
- [ ] Clock skew tolerance still passes
```

## How it works

1. Reads `git log <base>..HEAD` for commits (hash + subject).
2. Reads `git diff --stat <base>..HEAD` for changed files + additions/deletions.
3. Suggests a title from the latest commit subject.
4. Claude composes a real PR body from that scaffold.

## Limitations

- Doesn't fetch from the remote — make sure your local `<base>` is current.
- Handles empty diffs and non-git directories gracefully (returns empty JSON).
- Binary files surface via `git diff --numstat` and are reported with `-` for additions/deletions.

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
