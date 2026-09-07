"""Every auto-generated PR title must satisfy the repo's own commit-scope gate.

THE BUG THIS PINS

`commit-scope-check` became a required check on 2026-07-16 (#1076). It lints the
PULL REQUEST TITLE against .github/.commit-rules.json. Three workflows create
PRs automatically, and all three generated titles that the gate rejects:

    sync-external.yml     "🔄 Sync external plugins"
    promote-curated.yml   "🏅 Refresh curated skills mirror ($COUNT A/B skills)"
    update-npm-stats.yml  "📦 Daily npm download stats refresh"

So every automated PR opened after 2026-07-16 was born unmergeable — it could
only land via an admin override. PR #1149 (npm stats) sat open from 2026-07-30,
and the recovered external-plugin sync PR #1167 hit the same wall the moment it
was finally able to open at all.

WHY A TEST RATHER THAN JUST FIXING THE THREE STRINGS

The failure was invisible from either side. The workflow author never sees the
gate (it runs on the PR, not the workflow), and the gate author never sees the
generated titles (they live in unrelated YAML). Fixing the strings without
pinning them leaves the next automated workflow free to reintroduce it, and the
symptom — a stuck bot PR nobody is watching — is one people learn to ignore.

Deliberately NOT checked: hand-written PR titles (the live gate covers those)
and `gh release create --title`, which is a release name and never passes
through commit-scope-check.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
RULES = json.loads((REPO_ROOT / ".github" / ".commit-rules.json").read_text(encoding="utf-8"))

# Mirrors the validator inlined in validate-plugins.yml's commit-scope-check job.
RE_CONVENTIONAL = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?:!)?: (?P<subject>[^\r\n]+)$"
)
RE_TITLE_FLAG = re.compile(r'--title\s+"([^"]+)"')

# How far back to look for the command that owns a --title flag. The flag is
# usually a continuation line a few lines below `gh pr create`.
_LOOKBACK = 8


def _iter_pr_titles():
    """Yield (workflow_name, line_number, title) for every `gh pr create --title`."""
    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            match = RE_TITLE_FLAG.search(line)
            if not match:
                continue
            window = "\n".join(lines[max(0, idx - _LOOKBACK) : idx + 1])
            # `gh release create` also takes --title but is not gated.
            if "gh pr create" not in window:
                continue
            yield path.name, idx + 1, match.group(1)


def test_at_least_one_generated_pr_title_is_discovered() -> None:
    """Guard against the discovery loop silently matching nothing.

    If a refactor changes how these workflows invoke `gh pr create`, every
    assertion below would vacuously pass — the same "gate that gates nothing"
    failure this file exists to prevent.
    """
    found = list(_iter_pr_titles())
    assert len(found) >= 3, (
        "Expected to discover the automated PR titles in sync-external.yml, "
        f"promote-curated.yml and update-npm-stats.yml; found {len(found)}: {found}. "
        "If a workflow changed how it opens PRs, update this discovery logic."
    )


def test_generated_pr_titles_are_conventional_commits() -> None:
    offenders = []
    for name, lineno, title in _iter_pr_titles():
        # Shell interpolation is fine INSIDE the subject; only the type(scope):
        # prefix must be literal, since that is all the gate parses.
        if not RE_CONVENTIONAL.match(title):
            offenders.append(f"{name}:{lineno} -> {title!r}")

    assert not offenders, (
        "These workflows generate PR titles that the required `commit-scope-check` "
        "job rejects, so the PRs they open can never merge without an admin "
        "override:\n  " + "\n  ".join(offenders) + "\n\n"
        "Use `type(scope): subject` with a scope registered in "
        ".github/.commit-rules.json."
    )


def test_generated_pr_title_types_and_scopes_are_registered() -> None:
    allowed_types = set(RULES["allowedTypes"])
    allowed_scopes = set(RULES["allowedScopes"])
    patterns = [re.compile(p) for p in RULES.get("allowedScopePatterns", [])]

    offenders = []
    for name, lineno, title in _iter_pr_titles():
        m = RE_CONVENTIONAL.match(title)
        if not m:
            continue  # reported by the test above
        if m.group("type") not in allowed_types:
            offenders.append(f"{name}:{lineno} type {m.group('type')!r} not registered")
        scope = m.group("scope")
        if scope and scope not in allowed_scopes and not any(p.match(scope) for p in patterns):
            offenders.append(f"{name}:{lineno} scope {scope!r} not registered")

    assert not offenders, (
        "Generated PR titles use a type or scope that .github/.commit-rules.json "
        "does not register, which `commit-scope-check` rejects:\n  "
        + "\n  ".join(offenders)
        + "\n\nEither use a registered value or add it to the registry deliberately."
    )
