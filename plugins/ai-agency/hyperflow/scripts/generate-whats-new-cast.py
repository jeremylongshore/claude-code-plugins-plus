#!/usr/bin/env python3
"""Generate docs/assets/whats-new.cast from git log between two refs.

Produces a focused ~15-20s asciinema v2 cast showing only the NEW
features/fixes/changes since a given release tag.

Usage:
    python3 scripts/generate-whats-new-cast.py [options]

Options:
    --from <tag>        Start ref (default: most recent git tag)
    --to <ref>          End ref (default: HEAD)
    --version <X.Y.Z>   Version label (default: read from config/features.json)
    --output <path>     Output cast file (default: docs/assets/whats-new.cast)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def latest_tag() -> str | None:
    try:
        return git("describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None


def commits_between(frm: str | None, to: str) -> list[str]:
    if not frm:
        return git("log", to, "--pretty=format:%s").splitlines()
    return git("log", f"{frm}..{to}", "--pretty=format:%s").splitlines()


# ---------------------------------------------------------------------------
# Commit categorizer
# ---------------------------------------------------------------------------

def categorize(commits: list[str]) -> dict[str, list[str]]:
    added: list[str] = []
    fixed: list[str] = []
    changed: list[str] = []

    for c in commits:
        # Strip type prefix and scope: "feat(auth): add login" → "Add login"
        m = re.match(r'^(\w+)(\([^)]*\))?(!?):\s*(.+)$', c)
        if not m:
            continue
        kind, _scope, _bang, body = m.groups()
        body = body[0].upper() + body[1:] if body else body

        if kind == "feat":
            added.append(body)
        elif kind == "fix":
            fixed.append(body)
        elif kind in ("refactor", "perf", "docs", "chore", "style", "test"):
            # Skip release commits — they are noise
            if not c.startswith("chore(release)"):
                changed.append(body)

    return {"added": added, "fixed": fixed, "changed": changed}


# ---------------------------------------------------------------------------
# Cast DSL  (mirrors generate-demo-cast.py)
# ---------------------------------------------------------------------------

class Cast:
    """Minimal DSL for building an asciinema v2 event list."""

    def __init__(self) -> None:
        self.t: float = 0.0
        self.events: list = []

    def wait(self, seconds: float) -> "Cast":
        self.t += seconds
        return self

    def out(self, text: str, char_delay: float = 0.0) -> "Cast":
        if char_delay > 0:
            for ch in text:
                self.events.append([round(self.t, 4), "o", ch])
                self.t += char_delay
        else:
            self.events.append([round(self.t, 4), "o", text])
        return self

    def line(self, text: str) -> "Cast":
        self.events.append([round(self.t, 4), "o", text + "\r\n"])
        return self


# ---------------------------------------------------------------------------
# ANSI helpers  (matches generate-demo-cast.py exactly)
# ---------------------------------------------------------------------------

RESET   = "\x1b[0m"
BOLD    = "\x1b[1m"
MAGENTA = "\x1b[35m"
CYAN    = "\x1b[36m"
GREEN   = "\x1b[32m"
YELLOW  = "\x1b[33m"
GRAY    = "\x1b[90m"

def mg(s: str) -> str: return MAGENTA + s + RESET
def cy(s: str) -> str: return CYAN    + s + RESET
def gn(s: str) -> str: return GREEN   + s + RESET
def yl(s: str) -> str: return YELLOW  + s + RESET
def gr(s: str) -> str: return GRAY    + s + RESET
def bo(s: str) -> str: return BOLD    + s + RESET


# ---------------------------------------------------------------------------
# Cast builder
# ---------------------------------------------------------------------------

MAX_ITEMS = 6


def _bullet_list(c: Cast, items: list[str], delay: float = 0.25) -> None:
    shown = items[:MAX_ITEMS]
    for item in shown:
        c.line(gr("  • ") + item)
        c.wait(delay)
    overflow = len(items) - MAX_ITEMS
    if overflow > 0:
        c.line(gr(f"  … +{overflow} more"))
        c.wait(delay)


def build_cast(
    version: str,
    from_ref: str | None,
    categories: dict[str, list[str]],
    today: str,
) -> Cast:
    c = Cast()

    added   = categories["added"]
    fixed   = categories["fixed"]
    changed = categories["changed"]

    n_commits = len(added) + len(fixed) + len(changed)
    n_feat    = len(added)
    n_fix     = len(fixed)

    # -- Scene 1: Header (2-3s) -----------------------------------------------
    c.wait(0.3)
    c.line(mg(f"✨ What's New in v{version}"))
    c.wait(0.25)
    c.line(gr(today))
    c.wait(0.35)
    stats_parts = [f"{n_commits} commit{'s' if n_commits != 1 else ''}"]
    if n_feat:
        stats_parts.append(f"{n_feat} new feature{'s' if n_feat != 1 else ''}")
    if n_fix:
        stats_parts.append(f"{n_fix} fix{'es' if n_fix != 1 else ''}")
    c.line(gr("  " + " · ".join(stats_parts)))
    c.wait(0.8)

    # -- Scene 2: Added (5-7s) ------------------------------------------------
    if added:
        c.line(gr(""))
        c.line(gn("[Added]"))
        c.wait(0.3)
        _bullet_list(c, added, delay=0.28)
        c.wait(0.5)

    # -- Scene 3: Fixed (3-5s) ------------------------------------------------
    if fixed:
        c.line(gr(""))
        c.line(yl("[Fixed]"))
        c.wait(0.3)
        _bullet_list(c, fixed, delay=0.28)
        c.wait(0.5)

    # -- Scene 4: Changed (3-5s) ----------------------------------------------
    if changed:
        c.line(gr(""))
        c.line(cy("[Changed]"))
        c.wait(0.3)
        _bullet_list(c, changed, delay=0.28)
        c.wait(0.5)

    # -- Scene 5: Closing (1-2s) ----------------------------------------------
    c.line(gr(""))
    c.line(
        gr("▸ Full changelog: ") +
        "github.com/Mohammed-Abdelhady/hyperflow/blob/main/CHANGELOG.md"
    )
    c.wait(0.25)
    c.line(
        gr("▸ Install:  ") +
        cy("/plugin install hyperflow@hyperflow-marketplace")
    )
    c.wait(2.0)

    return c


def build_empty_cast(version: str | None, from_ref: str | None) -> Cast:
    """Minimal cast for a range with no conventional commits."""
    c = Cast()
    label = from_ref or version or "last release"
    c.wait(0.3)
    c.line(gr(f"No changes since v{label}"))
    c.wait(1.5)
    return c


# ---------------------------------------------------------------------------
# Writer  (matches generate-demo-cast.py)
# ---------------------------------------------------------------------------

HEADER = {
    "version": 2,
    "width": 100,
    "height": 30,
    "timestamp": 1715760000,
    "title": "Hyperflow — What's New",
    "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"},
}


def write_cast(cast: Cast, output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(HEADER, separators=(",", ":")) + "\n")
        for event in cast.events:
            fh.write(json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Version resolver
# ---------------------------------------------------------------------------

def resolve_version() -> str:
    features_path = ROOT / "config" / "features.json"
    if features_path.exists():
        try:
            return json.loads(features_path.read_text())["version"]
        except (KeyError, json.JSONDecodeError):
            pass
    return "0.0.0"


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate docs/assets/whats-new.cast from git log between two refs."
    )
    parser.add_argument(
        "--from",
        dest="from_ref",
        default=None,
        help="Start ref (default: most recent git tag)",
    )
    parser.add_argument(
        "--to",
        dest="to_ref",
        default="HEAD",
        help="End ref (default: HEAD)",
    )
    parser.add_argument(
        "--version",
        dest="version",
        default=None,
        help="Version label, e.g. 1.9.0 (default: read from config/features.json)",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "assets" / "whats-new.cast"),
        help="Output path for the .cast file (default: docs/assets/whats-new.cast)",
    )
    args = parser.parse_args()

    # Resolve refs
    from_ref: str | None = args.from_ref
    if from_ref is None:
        from_ref = latest_tag()  # may still be None (fresh repo)

    to_ref: str = args.to_ref

    # Resolve version label
    version: str = args.version or resolve_version()

    # Today's date — fixed epoch for determinism if TODAY_OVERRIDE env var set
    today_override = os.environ.get("HYPERFLOW_TODAY_OVERRIDE")
    if today_override:
        today = today_override
    else:
        today = datetime.now().strftime("%Y-%m-%d")

    # Collect and categorize commits
    raw_commits = commits_between(from_ref, to_ref)
    categories = categorize(raw_commits)

    n_total = sum(len(v) for v in categories.values())

    if n_total == 0:
        cast = build_empty_cast(version, from_ref)
    else:
        cast = build_cast(
            version=version,
            from_ref=from_ref,
            categories=categories,
            today=today,
        )

    write_cast(cast, args.output)

    duration = cast.t
    line_count = 1 + len(cast.events)

    print(f"Cast written to : {os.path.abspath(args.output)}")
    print(f"Total duration  : {duration:.2f}s")
    print(f"Total lines     : {line_count}")
    print(f"Range           : {from_ref or '(beginning)'}..{to_ref}")
    print(f"Commits parsed  : {len(raw_commits)} raw / {n_total} categorized")


if __name__ == "__main__":
    main()
