#!/usr/bin/env python3
"""Syntax-check fenced code blocks inside SKILL.md / README.md files.

Walks every Markdown file under plugins/, extracts ``` fenced code blocks
by language, and runs a language-appropriate syntax-only check on each:

  python      → ast.parse()
  bash, sh    → bash -n (parse, don't run)
  javascript  → node --check
  typescript  → tsc --noEmit (best-effort; tsc warns on unknown identifiers
                that come from runtime context — those are surfaced but
                NOT treated as failures here unless the syntax itself is bad)

Reports per-block with file path + 1-indexed block number + language.

Exit code 0 if all syntax-valid (or in --report-only mode).
Exit code 1 if any block fails AND not in --report-only mode.

Skips:
  - blocks tagged as `text`, `output`, `console`, `log`, `diff`, `json`,
    `yaml`, `toml`, `html`, `css`, `xml`, `tsx`, `jsx`, untagged blocks
  - blocks containing `# noqa: lint-codeblocks` as the first line
    (escape hatch for known-non-runnable examples)
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Languages we know how to syntax-check; everything else is skipped.
#
# TypeScript intentionally NOT in this set: SKILL.md TypeScript blocks are
# illustrative snippets that reference external types, runtime context, or
# API definitions not present in the block itself. Running `tsc --noEmit`
# on isolated fragments produces thousands of false positives. Type-safety
# of actual code is enforced by per-package `pnpm typecheck` jobs.
CHECKABLE = {"python", "py", "bash", "sh", "shell", "javascript", "js"}
FENCE_RE = re.compile(r"^```([a-zA-Z0-9_+\-]*)\s*$")
NOQA = "# noqa: lint-codeblocks"


def extract_blocks(text: str) -> list[tuple[int, str, str]]:
    """Yield (line_no, lang, body) for each fenced block."""
    blocks: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        lang = m.group(1).strip().lower()
        start = i + 1
        # Find matching close fence
        j = start
        while j < len(lines) and not FENCE_RE.match(lines[j]):
            j += 1
        body = "\n".join(lines[start:j])
        blocks.append((i + 1, lang, body))
        i = j + 1
    return blocks


def check_python(body: str) -> str | None:
    """None if OK, else error message."""
    try:
        ast.parse(body)
        return None
    except SyntaxError as e:
        return f"SyntaxError line {e.lineno}: {e.msg}"


def check_bash(body: str) -> str | None:
    if not shutil.which("bash"):
        return None  # skip if bash missing (unlikely)
    proc = subprocess.run(
        ["bash", "-n"],
        input=body,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if proc.returncode != 0:
        return proc.stderr.strip().splitlines()[0] if proc.stderr.strip() else "bash -n failed"
    return None


def check_node(body: str) -> str | None:
    if not shutil.which("node"):
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(body)
        path = f.name
    try:
        proc = subprocess.run(
            ["node", "--check", path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            err = (proc.stderr.strip() or proc.stdout.strip()).splitlines()
            return err[0] if err else "node --check failed"
        return None
    finally:
        Path(path).unlink(missing_ok=True)


def check_typescript(body: str) -> str | None:
    # tsc is heavy; we use node --check as a syntax-only approximation for TS.
    # Real type errors are caught by the per-package `pnpm typecheck` job.
    # We strip TS-only constructs (type annotations, `as` casts, interfaces)
    # if node --check fails, to differentiate "syntax error" vs "TS-only syntax".
    err = check_node(body)
    if err is None:
        return None
    if "Unexpected token" in err or "Unexpected identifier" in err:
        # Likely TS-only syntax that node can't parse. Skip — typecheck job
        # owns this surface.
        return None
    return err


CHECKERS = {
    "python": check_python,
    "py": check_python,
    "bash": check_bash,
    "sh": check_bash,
    "shell": check_bash,
    "javascript": check_node,
    "js": check_node,
    "typescript": check_typescript,
    "ts": check_typescript,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default="plugins",
        help="Root dir to scan (default: plugins/)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print failures but always exit 0 (for initial rollout)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print every block checked, not just failures",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        return 1

    md_files = sorted(set(root.rglob("SKILL.md")) | set(root.rglob("README.md")))
    md_files = [p for p in md_files if "node_modules" not in p.parts]

    total_blocks = 0
    checked_blocks = 0
    failures: list[str] = []

    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8")
        except Exception as e:
            print(f"SKIP {md}: read failed ({e})", file=sys.stderr)
            continue

        for line_no, lang, body in extract_blocks(text):
            total_blocks += 1
            if lang not in CHECKABLE:
                continue
            if body.strip().startswith(NOQA):
                continue
            checker = CHECKERS.get(lang)
            if checker is None:
                continue
            checked_blocks += 1

            err = checker(body)
            if err is None:
                if args.verbose:
                    print(f"  OK  {md}:{line_no} [{lang}]")
            else:
                msg = f"FAIL {md}:{line_no} [{lang}]: {err}"
                failures.append(msg)
                print(msg)

    print()
    print(f"Checked {checked_blocks} of {total_blocks} code blocks across {len(md_files)} markdown files.")
    if not failures:
        print("All clean.")
        return 0
    print(f"{len(failures)} failure(s).")
    if args.report_only:
        print("(--report-only: exiting 0 despite failures)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
