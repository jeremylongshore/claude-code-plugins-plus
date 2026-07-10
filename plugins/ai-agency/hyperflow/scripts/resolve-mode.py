#!/usr/bin/env python3
"""
resolve-mode.py — single source of truth for the active hyperflow mode.

Resolves the per-project mode from (in priority order):
  1. Explicit chain arg (e.g. argv flag `--lean` / `--thorough` / `--mode=lean`)
  2. .hyperflow/.mode file content
  3. Default: `default`

Usage:
  resolve-mode.py <project-root> [--from-args <args-string>]

Prints one word to stdout: `default` | `lean` | `thorough`
Exits 0 always (non-blocking). Errors go to stderr.

Skills that need to know the active mode call this script at chain start
and read the single word from stdout. Centralizes the lookup so every skill
follows the same priority chain.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

VALID_MODES = {"default", "lean", "thorough"}
FLAG_RE = re.compile(r"(?:^|\s)--(lean|thorough)(?:\s|$)")
KV_RE = re.compile(r"(?:^|\s)mode=(default|lean|thorough)(?:\s|$)")


def _from_args(args_string: str | None) -> str | None:
    if not args_string:
        return None
    kv = KV_RE.search(args_string)
    if kv:
        return kv.group(1)
    flag = FLAG_RE.search(args_string)
    if flag:
        return flag.group(1)
    return None


def _from_file(project_root: Path) -> str | None:
    path = project_root / ".hyperflow" / ".mode"
    try:
        value = path.read_text(encoding="utf-8").strip().lower()
        if value in VALID_MODES:
            return value
    except OSError:
        pass
    return None


def resolve(project_root: Path, args_string: str | None = None) -> str:
    """Apply the priority chain. Always returns a valid mode word."""
    return _from_args(args_string) or _from_file(project_root) or "default"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "resolve-mode: usage: resolve-mode.py <project-root> [--from-args <args>]",
            file=sys.stderr,
        )
        # Still emit a default so callers don't trip.
        print("default")
        return 0

    project_root = Path(argv[1])
    args_string: str | None = None
    if "--from-args" in argv[2:]:
        i = argv.index("--from-args")
        if i + 1 < len(argv):
            args_string = argv[i + 1]

    # Validate: lean and thorough are mutually exclusive.
    if args_string:
        flags = FLAG_RE.findall(args_string)
        if "lean" in flags and "thorough" in flags:
            print(
                "resolve-mode: --lean and --thorough are mutually exclusive — passing both is a doctrine violation",
                file=sys.stderr,
            )
            print("default")
            return 0

    print(resolve(project_root, args_string))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
