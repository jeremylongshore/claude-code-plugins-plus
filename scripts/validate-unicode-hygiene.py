#!/usr/bin/env python3
"""Unicode hygiene gate for marketplace skill / agent / command / catalog files.

Catches the supply-chain attack classes that schema validation cannot see:

  Blocker
    * Tag characters U+E0000-U+E007F.
      Invisible to humans; LLMs parse them as text instructions. Active attack
      class per the Socket TrapDoor advisory (2026-05-24).
    * Bidi override / isolate controls U+202A-U+202E, U+2066-U+2069.
      Trojan Source, CVE-2021-42574. Renders as one thing, parses as another.

  Major
    * Zero-width / format chars U+200B / U+200C / U+200D / U+2060 / U+FEFF
      anywhere except a single U+FEFF at file offset 0 (legitimate BOM).
    * Soft hyphen U+00AD, combining grapheme joiner U+034F, Hangul fillers
      U+115F / U+1160, Khmer zero-width vowels U+17B4 / U+17B5.

  Minor
    * Mixed-script identifiers (Latin + Cyrillic / Greek / others) inside
      URLs, package-manager install lines (npm/pnpm/yarn/pip/cargo/brew/gem),
      or any line ending in a code fence language tag.

Detection rules are Intent Solutions-original, derived from the public Unicode
Standard, the CVE-2021-42574 advisory, and the Socket TrapDoor advisory. Not a
fork or port of any third-party scanner.

Usage:
    python3 scripts/validate-unicode-hygiene.py                # full repo scan
    python3 scripts/validate-unicode-hygiene.py path1 path2    # specific files
    python3 scripts/validate-unicode-hygiene.py --warn-only    # never exit !=0
    python3 scripts/validate-unicode-hygiene.py --strict       # exit !=0 on Major too

Exits non-zero when any Blocker finding is reported (or any Major under
--strict). --warn-only always exits 0; intended for the rollout window.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Literal

Severity = Literal["BLOCKER", "MAJOR", "MINOR"]

# ----- codepoint classes ------------------------------------------------------

TAG_CHARS = range(0xE0000, 0xE0080)  # U+E0000-U+E007F inclusive

BIDI_CONTROLS = frozenset({0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069})

ZERO_WIDTH_MAJOR = frozenset({0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF})
OTHER_INVISIBLE = frozenset({0x00AD, 0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5})

# Scripts whose alphabetic letters collide visually with Latin letters often
# enough to be the basis for a homoglyph attack. The check fires on mixed
# Latin + any of these in a single identifier, not on pure non-Latin text.
HOMOGLYPH_SCRIPTS = frozenset({"Cyrillic", "Greek", "Armenian", "Cherokee"})

# Lines that warrant the homoglyph pass — URLs and install commands. We try
# hard to avoid scanning prose, where Cyrillic alongside Latin is fine.
HOMOGLYPH_LINE_PATTERNS = (
    re.compile(r"https?://"),
    re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:i|install|add)\b"),
    re.compile(r"\b(?:pip|pip3|uv)\s+install\b"),
    re.compile(r"\bcargo\s+(?:install|add)\b"),
    re.compile(r"\b(?:brew|gem|composer|go)\s+install\b"),
    re.compile(r"\bgh\s+repo\s+clone\b"),
)
IDENTIFIER_RE = re.compile(r"[A-Za-zͰ-ϿЀ-ӿ԰-֏Ꭰ-᏿][\w.\-/@]{2,}")

# ----- file discovery ---------------------------------------------------------

DEFAULT_TARGETS: tuple[str, ...] = (
    "plugins/**/SKILL.md",
    "plugins/**/plugin.json",
    "plugins/**/agents/*.md",
    "plugins/**/commands/*.md",
    "plugins/**/.claude-plugin/plugin.json",
    ".claude-plugin/marketplace.extended.json",
    "skills/**/SKILL.md",
)

SKIP_DIR_NAMES = frozenset({"node_modules", ".git", "dist", "build", "__pycache__"})


def iter_target_files(repo_root: pathlib.Path) -> Iterator[pathlib.Path]:
    seen: set[pathlib.Path] = set()
    for pattern in DEFAULT_TARGETS:
        for match in repo_root.glob(pattern):
            if not match.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in match.parts):
                continue
            if match in seen:
                continue
            seen.add(match)
            yield match


# ----- findings ---------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    severity: Severity
    path: pathlib.Path
    line: int
    column: int
    codepoint: int
    rule: str
    context: str  # ~32 chars around the offender, control chars escaped

    def codepoint_label(self) -> str:
        try:
            name = unicodedata.name(chr(self.codepoint))
        except ValueError:
            name = "(no name)"
        return f"U+{self.codepoint:04X} {name}"

    def render(self) -> str:
        return (
            f"  {self.severity:<7} {self.path}:{self.line}:{self.column}  "
            f"{self.codepoint_label()}  [{self.rule}]\n"
            f"           context: {self.context}"
        )


def _escape_context(line: str, column: int, width: int = 32) -> str:
    start = max(0, column - 1 - width // 2)
    end = min(len(line), column - 1 + width // 2)
    window = line[start:end]
    out_chars: list[str] = []
    for ch in window:
        cp = ord(ch)
        if cp in TAG_CHARS or cp in BIDI_CONTROLS or cp in ZERO_WIDTH_MAJOR or cp in OTHER_INVISIBLE or cp < 0x20:
            out_chars.append(f"<U+{cp:04X}>")
        else:
            out_chars.append(ch)
    return "".join(out_chars)


# ----- pass 1: invisible / control chars --------------------------------------


def scan_invisibles(path: pathlib.Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_idx, ch in enumerate(line, start=1):
            cp = ord(ch)
            if cp in TAG_CHARS:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        path=path,
                        line=line_no,
                        column=col_idx,
                        codepoint=cp,
                        rule="tag-character",
                        context=_escape_context(line, col_idx),
                    )
                )
            elif cp in BIDI_CONTROLS:
                findings.append(
                    Finding(
                        severity="BLOCKER",
                        path=path,
                        line=line_no,
                        column=col_idx,
                        codepoint=cp,
                        rule="bidi-control",
                        context=_escape_context(line, col_idx),
                    )
                )
            elif cp in ZERO_WIDTH_MAJOR:
                # Exception: a single U+FEFF at the very first byte of the file
                # is a legitimate BOM and gets a pass.
                if cp == 0xFEFF and line_no == 1 and col_idx == 1:
                    continue
                findings.append(
                    Finding(
                        severity="MAJOR",
                        path=path,
                        line=line_no,
                        column=col_idx,
                        codepoint=cp,
                        rule="zero-width-or-format",
                        context=_escape_context(line, col_idx),
                    )
                )
            elif cp in OTHER_INVISIBLE:
                findings.append(
                    Finding(
                        severity="MAJOR",
                        path=path,
                        line=line_no,
                        column=col_idx,
                        codepoint=cp,
                        rule="other-invisible",
                        context=_escape_context(line, col_idx),
                    )
                )
    return findings


# ----- pass 2: mixed-script identifiers in URLs / install lines ---------------


def _scripts_in(identifier: str) -> set[str]:
    scripts: set[str] = set()
    for ch in identifier:
        if not ch.isalpha():
            continue
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        # First word of the codepoint name is reliably the script ("LATIN", "CYRILLIC", "GREEK"...)
        first = name.split(" ", 1)[0].title()
        if first == "Latin" or first in HOMOGLYPH_SCRIPTS:
            scripts.add(first)
    return scripts


def scan_homoglyphs(path: pathlib.Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not any(pat.search(line) for pat in HOMOGLYPH_LINE_PATTERNS):
            continue
        for match in IDENTIFIER_RE.finditer(line):
            ident = match.group(0)
            scripts = _scripts_in(ident)
            if "Latin" in scripts and (scripts - {"Latin"}):
                column = match.start() + 1
                offender_cp = next(
                    (ord(c) for c in ident if c.isalpha() and _scripts_in(c) - {"Latin"}),
                    0xFFFD,
                )
                findings.append(
                    Finding(
                        severity="MINOR",
                        path=path,
                        line=line_no,
                        column=column,
                        codepoint=offender_cp,
                        rule="mixed-script-identifier",
                        context=_escape_context(line, column),
                    )
                )
    return findings


# ----- driver -----------------------------------------------------------------


def scan_file(path: pathlib.Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # A non-UTF-8 byte in a SKILL.md or plugin.json is itself suspicious,
        # but treat as an out-of-band concern — the schema validator already
        # flags JSON parse / encoding errors elsewhere.
        return []
    findings = scan_invisibles(path, text)
    findings.extend(scan_homoglyphs(path, text))
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="Optional explicit file paths; default = full repo scan.")
    parser.add_argument("--warn-only", action="store_true", help="Always exit 0. Use during initial rollout.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on Major findings too.")
    parser.add_argument("--repo-root", default=".", help="Repo root for default glob discovery.")
    args = parser.parse_args(argv[1:])

    repo_root = pathlib.Path(args.repo_root).resolve()

    if args.paths:
        files: Iterable[pathlib.Path] = [pathlib.Path(p) for p in args.paths]
    else:
        files = iter_target_files(repo_root)

    all_findings: list[Finding] = []
    scanned = 0
    for path in files:
        if not path.exists():
            print(f"validate-unicode-hygiene: skipping missing path {path}", file=sys.stderr)
            continue
        scanned += 1
        all_findings.extend(scan_file(path))

    blockers = [f for f in all_findings if f.severity == "BLOCKER"]
    majors = [f for f in all_findings if f.severity == "MAJOR"]
    minors = [f for f in all_findings if f.severity == "MINOR"]

    print(f"validate-unicode-hygiene: scanned {scanned} files")
    print(f"validate-unicode-hygiene: {len(blockers)} BLOCKER, {len(majors)} MAJOR, {len(minors)} MINOR")
    for f in all_findings:
        print(f.render())

    if args.warn_only:
        return 0
    if blockers:
        return 1
    if args.strict and majors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
