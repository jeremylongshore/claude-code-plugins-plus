#!/usr/bin/env python3
"""generate-portable-doctrine.py — build the portable doctrine template from DOCTRINE.md.

`templates/claude-md-doctrine.md` is the condensed "portable subset" of the
doctrine that `scripts/auto-bridge.py` stamps into a project's CLAUDE.md. It used
to be hand-maintained, which let it drift from the canonical
`skills/hyperflow/DOCTRINE.md` (three rules were silently lost that way). This
generator removes that failure class: the condensed short-form of each rule is
authored inline in DOCTRINE.md inside `<!-- portable:section ... -->` markers, and
this script collects those sections, orders them, and wraps them in the fixed
header/footer boilerplate to produce the template verbatim.

Determinism is a correctness requirement: the same DOCTRINE.md must always yield a
byte-identical template. No clock reads, no unstable iteration order — sections are
sorted by their explicit `order=` attribute with a stable sort.

The generated template keeps the literal `__HYPERFLOW_VERSION__` /
`__GENERATED_AT__` placeholders and the exact doctrine start/end markers so the
auto-bridge contract (scripts/auto-bridge.py) is preserved.

Usage:
    generate-portable-doctrine.py           # write templates/claude-md-doctrine.md
    generate-portable-doctrine.py --check    # verify the committed file is current
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCTRINE_PATH = ROOT / "skills" / "hyperflow" / "DOCTRINE.md"
TEMPLATE_PATH = ROOT / "templates" / "claude-md-doctrine.md"
TEMPLATE_REL = "templates/claude-md-doctrine.md"

REMEDIATION = (
    f"{TEMPLATE_REL} is stale — run python3 scripts/generate-portable-doctrine.py "
    "and commit the result"
)

# The start marker MUST match scripts/auto-bridge.py START_MARKER_RE and keep the
# __HYPERFLOW_VERSION__ / __GENERATED_AT__ placeholders untouched; auto-bridge
# substitutes them and appends body-sha at render time. The end marker must match
# auto-bridge END_MARKER exactly.
HEADER = (
    "<!-- hyperflow:doctrine:start version=__HYPERFLOW_VERSION__ "
    "generated=__GENERATED_AT__ "
    "source=https://github.com/Mohammed-Abdelhady/hyperflow -->\n"
    "\n"
    "# Hyperflow Doctrine (Portable Subset)\n"
    "\n"
    "Behavioral rules for surfaces that don't load the CLI plugin (Desktop, "
    "claude.ai web, IDE extensions). The full doctrine lives in the terminal CLI "
    "plugin; this is the portable behavioral floor.\n"
)

FOOTER = (
    "---\n"
    "\n"
    "> **Not in this block** (need the terminal CLI): `/hyperflow:*` slash "
    "commands, plugin skill files, session-strategy Step-0 question (one/two "
    "sessions + cross-environment handoff), operational pre-elections, background "
    "agents, sticky mode, status skill, cache skill, handoff skill, adaptive flow "
    "profiles. Run hyperflow in the terminal CLI for the full chain.\n"
    "\n"
    "<!-- hyperflow:doctrine:end -->\n"
)

# A portable section is authored in DOCTRINE.md as a single HTML comment so the
# whole block renders invisibly there (the opening line carries no `-->`, so the
# comment runs until the closing `/portable:section -->`):
#
#     <!-- portable:section id=autonomy order=1 title="Autonomy"
#
#     ## Autonomy
#     ...condensed markdown...
#
#     <!-- /portable:section -->
SECTION_RE = re.compile(
    r"<!--[ \t]*portable:section[ \t]+"
    r"id=(?P<id>[^\s]+)[ \t]+"
    r"order=(?P<order>\d+)[ \t]+"
    r"title=\"(?P<title>[^\"]*)\"[ \t]*\n"
    r"(?P<content>.*?)"
    r"\n[ \t]*<!--[ \t]*/portable:section[ \t]*-->",
    re.DOTALL,
)

# Permissive marker probes. SECTION_RE only matches *well-formed* blocks, so a
# typo'd `order=` or a missing closer would drop one section silently — and since
# --check compares the generator against the committed template, both sides would
# agree on the truncated content and CI would stay green while a doctrine rule
# disappeared. Counting raw markers and demanding they equal the parsed count turns
# that silent loss into a loud failure.
OPENER_RE = re.compile(r"<!--[ \t]*portable:section\b")
CLOSER_RE = re.compile(r"<!--[ \t]*/portable:section[ \t]*-->")

# A section body must not contain these. The comment delimiters would terminate or
# nest the HTML comment wrapping the block, making the condensed markdown render
# visibly in DOCTRINE.md. The bare marker tokens would smuggle a second doctrine
# boundary into every downstream CLAUDE.md the template is stamped into.
FORBIDDEN_IN_BODY = (
    "-->",
    "<!--",
    "hyperflow:doctrine:start",
    "hyperflow:doctrine:end",
)


def render(doctrine_text: str) -> str:
    """Produce the portable template bytes from DOCTRINE.md text.

    Pure and deterministic: parses the portable:section markers, sorts them by
    their integer `order`, and concatenates header + sections + footer.
    """
    sections: list[tuple[int, str, str]] = []
    seen_orders: dict[int, str] = {}
    seen_ids: set[str] = set()
    for match in SECTION_RE.finditer(doctrine_text):
        order = int(match.group("order"))
        section_id = match.group("id")
        content = match.group("content").strip()
        if not content:
            raise ValueError(f"portable:section id={section_id} has empty content")
        for token in FORBIDDEN_IN_BODY:
            if token in content:
                raise ValueError(
                    f"portable:section id={section_id} contains the literal "
                    f"'{token}' in its body — that would close or nest the wrapping "
                    "HTML comment, or smuggle a doctrine marker into every downstream "
                    "CLAUDE.md the template is stamped into"
                )
        if section_id in seen_ids:
            raise ValueError(f"portable:section id={section_id} is declared twice")
        if order in seen_orders:
            raise ValueError(
                f"portable:section order={order} is used by both "
                f"'{seen_orders[order]}' and '{section_id}' — orders must be unique"
            )
        seen_ids.add(section_id)
        seen_orders[order] = section_id
        sections.append((order, section_id, content))

    opener_count = len(OPENER_RE.findall(doctrine_text))
    closer_count = len(CLOSER_RE.findall(doctrine_text))
    if opener_count != len(sections) or closer_count != len(sections):
        raise ValueError(
            f"malformed portable:section markers — found {opener_count} opener(s) and "
            f"{closer_count} closer(s) but parsed {len(sections)} complete section(s). "
            'Every block needs a well-formed opener (id=<id> order=<int> title="<t>") '
            "and a matching <!-- /portable:section --> closer"
        )

    if not sections:
        raise ValueError(
            "no portable:section markers found in "
            "skills/hyperflow/DOCTRINE.md — cannot generate the template"
        )

    # Stable sort on the explicit order attribute — never document position.
    sections.sort(key=lambda s: s[0])
    body = "\n\n".join(content for _, _, content in sections)
    return HEADER + "\n" + body + "\n\n" + FOOTER


def generate(root: Path = ROOT) -> str:
    doctrine_path = root / "skills" / "hyperflow" / "DOCTRINE.md"
    return render(doctrine_path.read_text(encoding="utf-8"))


def check(root: Path = ROOT) -> list[str]:
    """Return a list of error strings (empty when the committed template is current)."""
    template_path = root / "templates" / "claude-md-doctrine.md"
    try:
        expected = generate(root)
    except (OSError, ValueError) as exc:
        return [f"portable doctrine generation failed: {exc}"]
    try:
        actual = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{TEMPLATE_REL} could not be read: {exc}"]
    if actual != expected:
        return [REMEDIATION]
    return []


def _diff(expected: str, actual: str) -> str:
    return "".join(
        difflib.unified_diff(
            actual.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=f"{TEMPLATE_REL} (committed)",
            tofile=f"{TEMPLATE_REL} (generated)",
        )
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate templates/claude-md-doctrine.md from DOCTRINE.md."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed template matches the generator; write nothing",
    )
    args = parser.parse_args(argv[1:])

    try:
        expected = generate(ROOT)
    except (OSError, ValueError) as exc:
        print(f"generate-portable-doctrine: {exc}", file=sys.stderr)
        return 1

    if args.check:
        try:
            actual = TEMPLATE_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"generate-portable-doctrine: {exc}", file=sys.stderr)
            return 1
        if actual != expected:
            print(REMEDIATION, file=sys.stderr)
            print(_diff(expected, actual), file=sys.stderr, end="")
            return 1
        print(f"{TEMPLATE_REL} is current.")
        return 0

    TEMPLATE_PATH.write_text(expected, encoding="utf-8")
    print(f"wrote {TEMPLATE_REL}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
