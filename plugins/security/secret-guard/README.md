![hero](./assets/hero.svg)

# secret-guard

**Block leaked API keys before they hit `origin`. Pattern + entropy. Redacted output.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-7c3aed.svg)](https://docs.claude.com/en/docs/claude-code/overview)
[![Tests: 10 passing](https://img.shields.io/badge/tests-10%20passing-success.svg)](./tests)

> **TL;DR:** `/secret-guard` → scans your staged diff for AWS / GitHub / Slack / Stripe / Google API keys, JWTs, private keys, and high-entropy base64 strings. Blocks the commit before the secret leaves your machine.

## Why this exists

Most "secret scanners" run in CI — *after* the leak is already in git history. By then, rotating the key is the only fix, because git history is forever. `secret-guard` runs in your pre-commit hook (or via Claude Code on demand) and catches the leak *before* the commit object exists. And the output is redacted by design: you can paste a finding in chat, in a PR, in Slack, without leaking the very thing you're trying to protect.

## Install (Claude Code + pre-commit)

```sh
git clone https://github.com/mturac/pluginpool-secret-guard ~/.claude/plugins/secret-guard
```

To wire as a pre-commit hook:

```sh
cp ~/.claude/plugins/secret-guard/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Quick start

```sh
/secret-guard                                            # scan staged diff
python3 scripts/guard.py                                 # same, directly
python3 scripts/guard.py --files src/config.py .env      # scan specific files
python3 scripts/guard.py --allowlist .secretignore       # suppress known false positives
```

## Flags

| Flag | Default | Description |
|---|---|---|
| `--files F…` | _staged diff_ | Scan specific files instead of the staged diff |
| `--allowlist PATH` | _none_ | Regexes (one per line) that suppress matching findings |
| `--format` | `json` | `json` or `md` |

## Detected patterns

| Rule | Match |
|---|---|
| AWS Access Key ID | `AKIA[0-9A-Z]{16}` |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| Slack token | `xox[abpr]-[A-Za-z0-9-]{10,}` |
| Stripe key | `sk_(live|test)_[A-Za-z0-9]{24,}` |
| Google API key | `AIza[0-9A-Za-z_-]{35}` |
| JWT | `eyJ…\.eyJ…\.…` |
| Private key | `-----BEGIN … PRIVATE KEY-----` |
| Generic high-entropy | base64-ish ≥32 chars, Shannon entropy ≥ 4.5 |

## Example output (markdown)

```
# secret-guard report

| file | line | rule | snippet |
|---|---|---|---|
| src/config.py | 12 | aws-access-key | AKIA… |
| .env | 4 | stripe-key | sk_l… |
```

Note: snippets are always `rule + first 4 chars + …` — never the full secret.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Clean — no secrets found |
| `1` | At least one finding (commit is blocked when used as a hook) |

## Safety guarantees

- `test_redaction_contains_only_rule_and_first_four` asserts the raw secret never appears in JSON or markdown output.
- `test_files_mode_does_not_crash_on_non_utf8` ensures non-UTF-8 / binary files are skipped, not crashed on.

## Limitations

- Pattern lists drift; submit PRs for new providers.
- Entropy heuristic produces some false positives on minified bundles — use `--allowlist` to suppress.
- Doesn't scan repo history; pair with `git-secrets` or `trufflehog` for that.

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
