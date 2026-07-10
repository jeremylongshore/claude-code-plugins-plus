#!/usr/bin/env python3
"""Deterministic fixture checker for the content-consistency validator (GH issue #991).

Implements the MECHANICAL subset of the skill's 9 drift checks — string,
semver, link/path, and date comparisons only. NO LLM anywhere. Judged
(`determinism: llm-judged`) fact classes in the registry are skipped
entirely; per the design council, judged findings are advisory-only and
never block, so they have no place in this gate.

Authority model (council law):
  - Source of truth comes from the per-fact-class registry (sot-map YAML),
    declared as data. Never a global ranking, never auto-detected here.
  - A value conflict in a fact class WITHOUT a registry row is emitted as
    "unowned fact-class — human adjudication needed". The checker never
    guesses a winner.

Modes:
  scan <project_root> --sot-map PATH   Print findings JSON for one tree.
  gate --fixtures-dir DIR              Red/green gate: exit 0 iff clean/ has
                                       ZERO findings and drifted/ matches
                                       expected-findings.json EXACTLY
                                       (zero invented, zero missed).

Stdlib only. Deterministic: the fixture registry pins `as_of` so date math
never rots.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Restricted YAML subset parser (sot-map files only).
# Supports: two-space-indented mappings, "- " lists of scalars,
# "key: value" scalars, full-line and inline " #" comments.
# ---------------------------------------------------------------------------


def _scalar(token):
    token = token.strip()
    if token in ("null", "~", ""):
        return None
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    try:
        return int(token)
    except ValueError:
        return token


def _indent_of(line):
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines, i, indent):
    if lines[i].lstrip().startswith("- "):
        items = []
        while i < len(lines) and _indent_of(lines[i]) == indent and lines[i].lstrip().startswith("- "):
            items.append(_scalar(lines[i].lstrip()[2:]))
            i += 1
        return items, i
    mapping = {}
    while i < len(lines):
        line = lines[i]
        ind = _indent_of(line)
        if ind < indent:
            break
        if ind > indent:
            raise ValueError(f"sot-map: unexpected indent at: {line!r}")
        key, _, rest = line.strip().partition(":")
        rest = rest.strip()
        i += 1
        if rest:
            mapping[key] = _scalar(rest)
        elif i < len(lines) and _indent_of(lines[i]) > ind:
            mapping[key], i = _parse_block(lines, i, _indent_of(lines[i]))
        else:
            mapping[key] = None
    return mapping, i


def parse_sot_map(path: Path) -> dict:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if " #" in raw:
            raw = raw.split(" #", 1)[0].rstrip()
        if raw.strip():
            lines.append(raw)
    if not lines:
        return {}
    parsed, _ = _parse_block(lines, 0, 0)
    return parsed


# ---------------------------------------------------------------------------
# Shared extraction helpers.
# ---------------------------------------------------------------------------

# Backtick-quoted prose path: must contain at least one "/" and end in a
# known file extension. Bare tokens like `create` or `package.json` are
# deliberately NOT treated as path references. Root-relative by convention.
PATH_TOKEN_RE = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|js|json|ya?ml))`")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)\)")
FENCE_RE = re.compile(r"^```.*$")
STALE_PHRASES = ("no application code", "no code exists", "scaffold only", "placeholder")
SOURCE_EXTS = (".js", ".ts", ".py", ".rb", ".go")
CODE_DIRS = ("src", "lib", "app")


def read_text(root: Path, rel: str) -> str | None:
    p = root / rel
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8")


def strip_fences(text: str) -> str:
    """Drop fenced code blocks; commands in fences are not prose references."""
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def fenced_lines(text: str) -> list[str]:
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(line.strip())
    return [ln for ln in out if ln]


def code_commands(root: Path) -> set[str]:
    text = read_text(root, "src/cli.js") or ""
    return set(re.findall(r"registerCommand\(\s*['\"]([a-z][a-z0-9-]*)['\"]", text))


def source_files(root: Path) -> list[str]:
    found = []
    for d in CODE_DIRS:
        base = root / d
        if base.is_dir():
            for p in sorted(base.rglob("*")):
                if p.suffix in SOURCE_EXTS and p.is_file():
                    found.append(p.relative_to(root).as_posix())
    return found


def finding(check, fact_class, kind, surfaces, description, severity):
    return {
        "check": check,
        "fact_class": fact_class,
        "kind": kind,
        "surfaces": sorted(surfaces),
        "description": description,
        "severity": severity,
    }


class Registry:
    def __init__(self, sot: dict):
        self.as_of = sot.get("as_of")
        self.classes = sot.get("fact_classes") or {}

    def row(self, fact_class: str):
        row = self.classes.get(fact_class)
        if row and row.get("determinism") != "deterministic":
            return None  # judged classes are invisible to this gate
        return row

    def deterministic_rows(self):
        for name, row in self.classes.items():
            if row and row.get("determinism") == "deterministic":
                yield name, row


def conflict_findings(reg: Registry, fact_class, check, kind, owner_surface, owner_value, mirrors, severity):
    """Compare mirror values to the owner value; route unregistered conflicts
    to the unowned-fact-class lane instead of guessing an authority."""
    out = []
    row = reg.row(fact_class)
    for mirror_surface, mirror_value in mirrors:
        if mirror_value is None or mirror_value == owner_value:
            continue
        if row:
            out.append(
                finding(
                    check,
                    fact_class,
                    kind,
                    [owner_surface, mirror_surface],
                    f"{mirror_surface} says {mirror_value!r} but owner {owner_surface} says {owner_value!r}.",
                    severity,
                )
            )
        else:
            out.append(
                finding(
                    "unowned-fact-class",
                    fact_class,
                    "conflict-needs-adjudication",
                    [owner_surface, mirror_surface],
                    f"unowned fact-class — human adjudication needed: {fact_class} conflicts "
                    f"({mirror_surface}={mirror_value!r} vs {owner_surface}={owner_value!r}) "
                    "and has no sot-map registry row.",
                    "needs-adjudication",
                )
            )
    return out


# ---------------------------------------------------------------------------
# The mechanical checks (skill check number noted per function).
# ---------------------------------------------------------------------------


def check_version(root: Path, reg: Registry):  # skill check 3.2
    manifest = read_text(root, "package.json")
    if manifest is None:
        return []
    owner_value = json.loads(manifest).get("version")
    mirrors = []
    readme = read_text(root, "README.md")
    if readme:
        m = re.search(r"badge/version-(\d+\.\d+\.\d+)-", readme)
        mirrors.append(("README.md", m.group(1) if m else None))
    changelog = read_text(root, "CHANGELOG.md")
    if changelog:
        m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.MULTILINE)
        mirrors.append(("CHANGELOG.md", m.group(1) if m else None))
    return conflict_findings(
        reg, "product.version", "version-consistency", "version-mismatch", "package.json", owner_value, mirrors, "high"
    )


def check_license(root: Path, reg: Registry):  # skill check 3.7
    manifest = read_text(root, "package.json")
    if manifest is None:
        return []
    owner_value = json.loads(manifest).get("license")
    mirrors = []
    readme = read_text(root, "README.md")
    if readme:
        m = re.search(r"[Ll]icensed under the ([A-Za-z0-9.-]+) [Ll]icense", readme)
        mirrors.append(("README.md", m.group(1) if m else None))
    return conflict_findings(
        reg, "product.license", "cross-doc-facts", "value-mismatch", "package.json", owner_value, mirrors, "high"
    )


def check_commands(root: Path, reg: Registry):  # skill check 3.6 (mechanical subset)
    readme = read_text(root, "README.md")
    if readme is None:
        return []
    implemented = code_commands(root)
    claimed = []
    in_section = False
    for line in readme.splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## commands"
            continue
        if in_section:
            m = re.match(r"^\|\s*`([a-z0-9-]+)`\s*\|", line)
            if m:
                claimed.append(m.group(1))
    out = []
    row = reg.row("product.commands")
    for name in claimed:
        if name not in implemented:
            if row:
                out.append(
                    finding(
                        "command-claims-vs-code",
                        "product.commands",
                        "claimed-but-absent",
                        ["README.md", row.get("owner", "src/cli.js")],
                        f"README claims a {name!r} command that the owner surface never registers.",
                        "high",
                    )
                )
            else:
                out.append(
                    finding(
                        "unowned-fact-class",
                        "product.commands",
                        "conflict-needs-adjudication",
                        ["README.md", "src/cli.js"],
                        f"unowned fact-class — human adjudication needed: command claim {name!r} "
                        "conflicts with code and product.commands has no sot-map registry row.",
                        "needs-adjudication",
                    )
                )
    return out


def check_ci(root: Path, reg: Registry):  # skill check 3.3
    row = reg.row("ci.test-command")
    ci_path = (row or {}).get("owner", ".github/workflows/ci.yml")
    ci_text = read_text(root, ci_path)
    readme = read_text(root, "README.md")
    if ci_text is None or readme is None:
        return []
    ci_cmds = {m.group(1).strip() for m in re.finditer(r"^\s*(?:-\s*)?run:\s*(.+)$", ci_text, re.MULTILINE)}
    out = []
    for line in fenced_lines(readme):
        if re.match(r"^(?:npm|pnpm|yarn|make)\b.*\btest\b", line) and line not in ci_cmds:
            out.append(
                finding(
                    "readme-vs-ci",
                    "ci.test-command",
                    "test-command-mismatch",
                    ["README.md", ci_path],
                    f"README instructs {line!r} but no CI step runs that command (CI runs: {sorted(ci_cmds)}).",
                    "high",
                )
            )
    return out


def check_freshness(root: Path, reg: Registry):  # date-staleness (registry-driven)
    if not reg.as_of:
        return []
    as_of = datetime.date.fromisoformat(str(reg.as_of))
    out = []
    for fact_class, row in reg.deterministic_rows():
        bound = row.get("staleness_bound")
        if not isinstance(bound, int):
            continue
        owner = row.get("owner")
        text = read_text(root, owner) if owner else None
        if text is None:
            continue
        m = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", text)
        if not m:
            continue
        age = (as_of - datetime.date.fromisoformat(m.group(1))).days
        if age > bound:
            out.append(
                finding(
                    "staleness-bound",
                    fact_class,
                    "stale-beyond-bound",
                    [owner],
                    f"{owner} last updated {m.group(1)} — {age} days before {as_of}, beyond the {bound}-day bound.",
                    "medium",
                )
            )
    return out


def check_index(root: Path, _reg: Registry):  # skill check 3.1
    index_rel = "000-docs/000-INDEX.md"
    index_text = read_text(root, index_rel)
    if index_text is None:
        return []
    listed = set(re.findall(r"`([0-9A-Za-z-]+\.md)`", index_text))
    on_disk = {p.name for p in (root / "000-docs").glob("*.md")} - {"000-INDEX.md"}
    out = []
    for name in sorted(listed - on_disk):
        out.append(
            finding(
                "index-vs-filesystem",
                "docs.index",
                "listed-but-missing",
                [index_rel, f"000-docs/{name}"],
                f"{index_rel} lists {name} but the file is not on disk.",
                "medium",
            )
        )
    for name in sorted(on_disk - listed):
        out.append(
            finding(
                "index-vs-filesystem",
                "docs.index",
                "present-but-unlisted",
                [index_rel, f"000-docs/{name}"],
                f"000-docs/{name} exists on disk but is not listed in {index_rel}.",
                "medium",
            )
        )
    return out


def check_claude_paths(root: Path, _reg: Registry):  # skill check 3.4
    text = read_text(root, "CLAUDE.md")
    if text is None:
        return []
    out = []
    for rel in sorted(set(PATH_TOKEN_RE.findall(strip_fences(text)))):
        if not (root / rel).exists():
            out.append(
                finding(
                    "claude-md-paths",
                    "docs.claude-refs",
                    "dead-reference",
                    ["CLAUDE.md", rel],
                    f"CLAUDE.md references {rel}, which does not exist.",
                    "medium",
                )
            )
    return out


def check_broken_refs(root: Path, _reg: Registry):  # skill check 3.8
    out = []
    for md in sorted(root.rglob("*.md")):
        rel_md = md.relative_to(root).as_posix()
        if rel_md == "CLAUDE.md":
            continue  # owned by claude-md-paths
        text = strip_fences(md.read_text(encoding="utf-8"))
        # Markdown links resolve relative to the containing file.
        for target in MD_LINK_RE.findall(text):
            if re.match(r"^[a-z]+:", target):
                continue  # external scheme (https:, mailto:, ...)
            if not (md.parent / target).resolve().exists():
                out.append(
                    finding(
                        "broken-refs",
                        "docs.crossrefs",
                        "dead-reference",
                        [rel_md, target],
                        f"{rel_md} links to {target}, which does not exist.",
                        "medium",
                    )
                )
        # Backtick prose paths resolve against the project root.
        for target in sorted(set(PATH_TOKEN_RE.findall(text))):
            if not (root / target).exists():
                out.append(
                    finding(
                        "broken-refs",
                        "docs.crossrefs",
                        "dead-reference",
                        [rel_md, target],
                        f"{rel_md} references {target} in prose, but it does not exist.",
                        "medium",
                    )
                )
    return out


def check_stale_phase(root: Path, _reg: Registry):  # skill check 3.5
    sources = source_files(root)
    if not sources:
        return []
    out = []
    for rel in ("README.md", "CLAUDE.md"):
        text = read_text(root, rel)
        if text is None:
            continue
        hits = [p for p in STALE_PHRASES if p in text.lower()]
        if hits:
            out.append(
                finding(
                    "stale-phase-language",
                    "project.phase",
                    "stale-phase-claim",
                    [rel, sources[0]],
                    f"{rel} contains stale phase language {hits} while source files exist ({sources[0]}).",
                    "high",
                )
            )
    return out


def check_roadmap(root: Path, _reg: Registry):  # skill check 3.9 (mechanical subset)
    text = read_text(root, "planning/roadmap.md")
    if text is None:
        return []
    implemented = code_commands(root)
    out = []
    for m in re.finditer(r"^\|\s*`([a-z0-9-]+)`\s*\|\s*(\w+)\s*\|", text, re.MULTILINE):
        name, status = m.group(1), m.group(2).lower()
        if status == "planned" and name in implemented:
            out.append(
                finding(
                    "planning-vs-code",
                    "roadmap.status",
                    "planned-but-implemented",
                    ["planning/roadmap.md", "src/cli.js"],
                    f"Roadmap marks {name!r} as Planned but src/cli.js already registers it.",
                    "medium",
                )
            )
        elif status == "shipped" and name not in implemented:
            out.append(
                finding(
                    "planning-vs-code",
                    "roadmap.status",
                    "shipped-but-missing",
                    ["planning/roadmap.md", "src/cli.js"],
                    f"Roadmap marks {name!r} as Shipped but src/cli.js never registers it.",
                    "high",
                )
            )
    return out


def check_tagline(root: Path, reg: Registry):  # naming/messaging drift (unowned-class exercise)
    values = []
    for rel in ("README.md", "docs/index.md"):
        text = read_text(root, rel)
        if text is None:
            continue
        m = re.search(r"^>\s*(.+)$", text, re.MULTILINE)
        if m:
            values.append((rel, m.group(1).strip()))
    if len(values) < 2:
        return []
    owner_surface, owner_value = values[0]
    return conflict_findings(
        reg, "product.tagline", "cross-doc-facts", "value-mismatch", owner_surface, owner_value, values[1:], "medium"
    )


ALL_CHECKS = (
    check_version,
    check_license,
    check_commands,
    check_ci,
    check_freshness,
    check_index,
    check_claude_paths,
    check_broken_refs,
    check_stale_phase,
    check_roadmap,
    check_tagline,
)


def scan(root: Path, sot_map: Path) -> list[dict]:
    reg = Registry(parse_sot_map(sot_map))
    findings = []
    for chk in ALL_CHECKS:
        findings.extend(chk(root, reg))
    return findings


# ---------------------------------------------------------------------------
# Gate mode: red/green against the golden ledger.
# ---------------------------------------------------------------------------


def identity(f: dict) -> str:
    return "|".join([f["check"], f["fact_class"], f["kind"], ",".join(sorted(f["surfaces"]))])


def run_gate(fixtures_dir: Path) -> int:
    sot_map = fixtures_dir / "sot-map.example.yaml"
    expected_path = fixtures_dir / "expected-findings.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))["findings"]
    ok = True

    clean_findings = scan(fixtures_dir / "clean", sot_map)
    if clean_findings:
        ok = False
        print(f"RED  clean/: expected 0 findings, got {len(clean_findings)}:")
        for f in clean_findings:
            print(f"  invented: {identity(f)}")
    else:
        print("GREEN clean/: 0 findings (as expected)")

    drifted_findings = scan(fixtures_dir / "drifted", sot_map)
    expected_ids = {identity(f): f.get("id", "?") for f in expected}
    actual_ids = {identity(f) for f in drifted_findings}
    missed = sorted(set(expected_ids) - actual_ids)
    invented = sorted(actual_ids - set(expected_ids))
    if missed or invented:
        ok = False
        print(f"RED  drifted/: expected exactly {len(expected)} findings, got {len(drifted_findings)}")
        for key in missed:
            print(f"  missed  ({expected_ids[key]}): {key}")
        for key in invented:
            print(f"  invented: {key}")
    else:
        matched = ", ".join(sorted(expected_ids.values()))
        print(f"GREEN drifted/: exactly {len(expected)} seeded findings, zero invented ({matched})")

    print("GATE " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    p_scan = sub.add_parser("scan", help="print findings JSON for one project tree")
    p_scan.add_argument("root", type=Path)
    p_scan.add_argument("--sot-map", type=Path, required=True)
    p_gate = sub.add_parser("gate", help="red/green gate over clean/ + drifted/")
    p_gate.add_argument("--fixtures-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "scan":
        print(json.dumps(scan(args.root, args.sot_map), indent=2))
        return 0
    return run_gate(args.fixtures_dir)


if __name__ == "__main__":
    sys.exit(main())
