# Pre-Commit Hooks

Local + CI hooks that block cassette secret leaks (P44), enforce prompt conventions, and catch lint regressions before they reach review. Both layers are required — local alone can be skipped with `-n`; CI alone is slow.

## `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: vcr-secret-scan
        name: VCR cassette secret scan (P44)
        entry: python scripts/scan_cassettes.py
        language: system
        files: "tests/integration/cassettes/.*\\.ya?ml$"
        pass_filenames: true

      - id: prompt-convention-lint
        name: prompt-convention lint
        entry: python scripts/lint_prompts.py
        language: system
        files: "prompts/.*\\.j2$|src/.*prompts?\\.py$"
        pass_filenames: true

      - id: dryrun-load-chains
        name: dryrun load chain modules
        entry: python scripts/dryrun_load_chains.py
        language: system
        pass_filenames: false
        files: "src/chains/.*\\.py$"

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
        exclude: "^tests/integration/cassettes/"
```

Note that `detect-secrets` excludes cassettes — our custom `scan_cassettes.py` is narrower and faster for that specific format. `detect-secrets` handles everything else.

## `scripts/scan_cassettes.py`

```python
"""Grep VCR YAML cassettes for provider credentials (P44).

Runs in: pre-commit (local), lint job (CI), integration job post-step (CI).
"""
import re
import sys
import pathlib

# Ordered roughly by how much pain they cause.
PATTERNS = [
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), "Anthropic API key"),
    (re.compile(r"sk-proj-[A-Za-z0-9_\-]{20,}"), "OpenAI project key"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI API key"),
    (re.compile(r"AIza[A-Za-z0-9_\-]{35}"), "Google API key"),
    (re.compile(r"xoxb-[A-Za-z0-9\-]{40,}"), "Slack bot token"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"), "Bearer token"),
    (re.compile(r"[Aa]uthorization:\s*[A-Za-z]+\s+[A-Za-z0-9._\-]{20,}"), "Authorization header"),
]


def scan(path: pathlib.Path) -> list[tuple[str, int, str]]:
    hits = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        print(f"::warning::could not read {path}: {e}", file=sys.stderr)
        return hits
    for lineno, line in enumerate(lines, 1):
        for pat, label in PATTERNS:
            if pat.search(line):
                hits.append((str(path), lineno, label))
                break
    return hits


def main(argv: list[str]) -> int:
    targets = []
    for a in argv[1:]:
        p = pathlib.Path(a)
        if p.is_dir():
            targets.extend(p.rglob("*.yaml"))
            targets.extend(p.rglob("*.yml"))
        elif p.is_file():
            targets.append(p)
    if not targets:
        return 0

    all_hits = []
    for t in targets:
        all_hits.extend(scan(t))

    if all_hits:
        print("::error::potential secret in VCR cassette (P44)")
        for path, lineno, label in all_hits:
            print(f"  {path}:{lineno}  ({label})")
        print("Fix: add header/param to `filter_headers` / `filter_post_data_parameters`")
        print("     in tests/integration/conftest.py, then re-record.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

## `scripts/lint_prompts.py`

Thin linter that enforces the prompt conventions from `claude-prompt-conventions`. Minimum rules:

```python
"""Lint prompt templates for convention violations.

Pairs with `claude-prompt-conventions`. Keep rules narrow — block obvious
mistakes, let review catch style preferences.
"""
import re
import sys
import pathlib

RULES = [
    # No f-strings with user-input variables (prompt-injection vector).
    (re.compile(r'f"[^"]*\{(?!"|\w+\s*[:!\.])\w+\}"'),
     "f-string with unquoted interpolation — consider prompt template"),
    # System message should appear at position 0 (P58 — Claude silently ignores otherwise).
    (re.compile(r'SystemMessage\([^)]*\)\s*,\s*HumanMessage.*SystemMessage',
                re.DOTALL),
     "multiple SystemMessages — Claude only honors the first (P58)"),
    # Prefer named variables over positional {0} {1}.
    (re.compile(r'\{[0-9]+\}'),
     "positional template var — use named {var} instead"),
]


def lint(path: pathlib.Path) -> list[tuple[str, int, str]]:
    hits = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        for pat, msg in RULES:
            if pat.search(line):
                hits.append((str(path), lineno, msg))
    return hits


def main(argv: list[str]) -> int:
    all_hits = []
    for a in argv[1:]:
        p = pathlib.Path(a)
        if p.is_file():
            all_hits.extend(lint(p))
    for path, lineno, msg in all_hits:
        print(f"::error file={path},line={lineno}::{msg}")
    return 1 if all_hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

## `detect-secrets` baseline rotation

`.secrets.baseline` records **expected** secret-like strings (test fixtures, sample keys in docs) so the hook does not flag them on every run. Rotate:

```bash
# After adding legitimate new test fixtures:
detect-secrets scan --baseline .secrets.baseline

# Audit the baseline (interactive):
detect-secrets audit .secrets.baseline
```

Commit the updated baseline. Never edit by hand — the hash chain breaks and the tool re-flags everything.

## Installation snippet for contributors

Add to `CONTRIBUTING.md`:

```bash
pip install pre-commit
pre-commit install                    # install git hooks
pre-commit run --all-files            # sanity check on first install
```

Optional but recommended: enable `pre-commit ci` (github.com/pre-commit-ci) as a redundant CI check so contributors who forgot `pre-commit install` still get blocked.

## Incident response after a P44 leak

If `sk-ant-...` or similar has hit `main`:

1. **Rotate the key first.** Every leaked credential must be considered live until rotated. Anthropic console → API Keys → revoke.
2. **Confirm blast radius.** `git log --all --oneline -- tests/integration/cassettes/ | head -20`. Grep every commit touching cassettes for the key pattern.
3. **Rewrite history.** Use `git-filter-repo --replace-text leaked-patterns.txt` to scrub the key from every commit that ever had it. This is destructive and forces a force-push — coordinate with the team.
4. **Force-push and instruct everyone** to re-clone (do not rebase — keys remain in the rebased history).
5. **Prevent recurrence.** Land the `scan_cassettes.py` hook and the `filter_headers` conftest fixture in the same PR.

## Cross-references

- VCR `filter_headers` fixture setup — [Integration Gating](integration-gating.md)
- Cassette recording workflow (local) — `langchain-local-dev-loop` (F23)
- Prompt convention details — `claude-prompt-conventions`
- `ruff` config — pair with `pyproject.toml` `[tool.ruff]` section (not owned by this skill)
