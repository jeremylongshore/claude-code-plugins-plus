#!/usr/bin/env python3
"""Parse a 6767-h prose spec markdown file and emit a JSON section index.

Usage:
    python scripts/parse-prose-anchors.py [--doc PATH] [--out PATH]

Section ID rules:
  1. Heading text beginning with a numeric prefix like "1)", "4.2.1.", etc.
     uses that prefix as the section ID.
  2. Heading text beginning with "Appendix A:" uses the letter as the ID.
  3. All other headings are auto-numbered.  Headings that appear before the
     first explicit numeric heading at their level get a "0.x" preamble ID
     to avoid colliding with the explicit numbering that follows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_NUMERIC_PREFIX = re.compile(r"^(\d+(?:\.\d+)*)[\)\.\s]+(.*)")
_APPENDIX_PREFIX = re.compile(r"^Appendix\s+([A-Z])[\.\:\-\s]+(.*)", re.IGNORECASE)
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*)")
_INLINE_MD = re.compile(r"[`*_]{1,3}([^`*_]*)[`*_]{1,3}")


def _clean(text: str) -> str:
    return _INLINE_MD.sub(r"\1", text).strip()


def _dotted(counters: list[int], depth: int) -> str:
    return ".".join(str(c) for c in counters[:depth])


def parse_sections(text: str) -> list[dict]:
    counters: list[int] = [0] * 6
    explicit_seen: list[bool] = [False] * 6
    preamble_cnt: list[int] = [0] * 6
    sections: list[dict] = []
    in_fence = False

    for lineno, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
        if in_fence:
            continue

        hm = _HEADING_LINE.match(raw)
        if not hm:
            continue

        level = len(hm.group(1))
        title = _clean(hm.group(2).strip())

        nm = _NUMERIC_PREFIX.match(title)
        am = _APPENDIX_PREFIX.match(title)

        if nm:
            raw_id, rest = nm.group(1), nm.group(2).strip()
            parts = [int(x) for x in raw_id.split(".")]
            for i, v in enumerate(parts):
                if i < 6:
                    counters[i] = v
                    explicit_seen[i] = True
            for i in range(len(parts), 6):
                counters[i] = 0
            section_id = raw_id
            display = rest or title
        elif am:
            section_id = am.group(1).upper()
            display = am.group(2).strip() or title
        else:
            if not explicit_seen[level - 1]:
                preamble_cnt[level - 1] += 1
                parent = _dotted(counters, level - 1)
                n = preamble_cnt[level - 1]
                section_id = f"{parent}.0.{n}" if parent else f"0.{n}"
            else:
                counters[level - 1] += 1
                for i in range(level, 6):
                    counters[i] = 0
                section_id = _dotted(counters, level)
            display = title

        sections.append({"id": section_id, "title": display, "level": level, "line": lineno})

    return sections


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_rel(path: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=str(path.parent),
        )
        if r.returncode == 0:
            return str(path.resolve().relative_to(Path(r.stdout.strip())))
    except Exception:
        pass
    return str(path)


def main(argv: list[str] | None = None) -> int:
    default = Path(__file__).parent.parent / "000-docs" / "6767-h-SPEC-DR-STND-claude-code-extensions-master.md"
    ap = argparse.ArgumentParser(description="Parse 6767-h spec into a section index.")
    ap.add_argument("--doc", type=Path, default=default)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    doc = args.doc.resolve()
    if not doc.is_file():
        print(f"ERROR: not found: {doc}", file=sys.stderr)
        return 1

    sections = parse_sections(doc.read_text(encoding="utf-8"))
    output = {
        "doc_path": _repo_rel(doc),
        "doc_sha256": _sha256(doc),
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
    }
    serialized = json.dumps(output, indent=2)

    if args.out:
        args.out.write_text(serialized, encoding="utf-8")
        print(f"Wrote {len(sections)} sections to {args.out}", file=sys.stderr)
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    sys.exit(main())
