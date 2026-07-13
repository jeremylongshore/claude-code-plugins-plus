#!/usr/bin/env python3
"""Static-analysis scan for command-injection patterns.

References:
    CWE-78 Improper Neutralization of Special Elements used in an OS Command
    OWASP A03:2021 Injection
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "detecting-command-injection-patterns"


PY_PATTERNS = [
    (
        "Python subprocess with shell=True + f-string",
        Severity.CRITICAL,
        r"subprocess\.(?:run|call|check_output|check_call|Popen)\s*\(\s*f['\"]",
        "python",
    ),
    (
        "Python subprocess with shell=True + concat",
        Severity.CRITICAL,
        r"subprocess\.[a-z_]+\s*\(\s*['\"][^'\"]*['\"]\s*\+\s*\w[^,)]*,[^)]*shell\s*=\s*True",
        "python",
    ),
    (
        "Python subprocess shell=True (any form, needs review)",
        Severity.HIGH,
        r"subprocess\.[a-z_]+\s*\([^)]*shell\s*=\s*True",
        "python",
    ),
    (
        "Python os.system with f-string / concat",
        Severity.CRITICAL,
        r"os\.system\s*\(\s*(?:f['\"]|['\"][^'\"]*['\"]\s*\+)",
        "python",
    ),
    (
        "Python os.popen with interpolation",
        Severity.CRITICAL,
        r"os\.popen\s*\(\s*(?:f['\"]|['\"][^'\"]*['\"]\s*\+)",
        "python",
    ),
    (
        "Python commands.getoutput / getstatusoutput (legacy)",
        Severity.HIGH,
        r"commands\.(?:getoutput|getstatusoutput)\s*\(",
        "python",
    ),
]

JS_PATTERNS = [
    (
        "Node child_process.exec with template literal",
        Severity.CRITICAL,
        r"(?:child_process|require\(['\"]child_process['\"]\))\.exec(?:Sync)?\s*\(\s*`[^`]*\$\{",
        "javascript",
    ),
    ("Node exec with concat", Severity.CRITICAL, r"\.exec(?:Sync)?\s*\(\s*['\"][^'\"]*['\"]\s*\+\s*\w", "javascript"),
    (
        "Node execFile with shell wrapper",
        Severity.HIGH,
        r"\.execFile(?:Sync)?\s*\(\s*['\"](?:sh|bash|/bin/sh)['\"]",
        "javascript",
    ),
    (
        "Node spawn with shell:true option",
        Severity.HIGH,
        r"\.spawn(?:Sync)?\s*\([^)]*\{[^}]*shell\s*:\s*true",
        "javascript",
    ),
]

RUBY_PATTERNS = [
    ("Ruby backticks with interpolation", Severity.CRITICAL, r"`[^`]*#\{[^}]+\}[^`]*`", "ruby"),
    ("Ruby Kernel#system with interpolation", Severity.CRITICAL, r"\bsystem\s*\(\s*['\"][^'\"]*#\{", "ruby"),
    ("Ruby Kernel#exec with interpolation", Severity.CRITICAL, r"\bexec\s*\(\s*['\"][^'\"]*#\{", "ruby"),
    (
        "Ruby Open3 with shell wrapper interpolation",
        Severity.HIGH,
        r"Open3\.(?:popen|capture)[a-z0-9_]*\s*\(\s*['\"][^'\"]*#\{",
        "ruby",
    ),
]

GO_PATTERNS = [
    (
        "Go exec.Command with sh -c + concat",
        Severity.HIGH,
        r"""exec\.Command\s*\(\s*["'](?:sh|bash|/bin/sh|/bin/bash)["']\s*,\s*["']-c["']\s*,\s*[^,)]*\+""",
        "go",
    ),
    ("Go exec.Command with fmt.Sprintf", Severity.HIGH, r"exec\.Command(?:Context)?\s*\([^)]*fmt\.Sprintf", "go"),
]

PHP_PATTERNS = [
    (
        "PHP system() / exec() with $-interpolation",
        Severity.CRITICAL,
        r"\b(?:system|exec|passthru|shell_exec|popen|proc_open)\s*\(\s*['\"][^'\"]*\$",
        "php",
    ),
    ("PHP backticks with $-interpolation", Severity.CRITICAL, r"`[^`]*\$[a-z_][^`]*`", "php"),
    (
        "PHP escapeshellarg missing on user input",
        Severity.MEDIUM,
        r"\b(?:system|exec|passthru|shell_exec)\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)",
        "php",
    ),
]

JAVA_PATTERNS = [
    (
        "Java Runtime.exec(String) with concat",
        Severity.HIGH,
        r"Runtime\.getRuntime\(\)\.exec\s*\(\s*['\"][^'\"]*['\"]\s*\+",
        "java",
    ),
    (
        "Java ProcessBuilder(String) single-string form",
        Severity.MEDIUM,
        r"new ProcessBuilder\s*\(\s*[a-z_]+(?:\s*\+\s*[a-z_]+)+\s*\)",
        "java",
    ),
]


LANG_EXT_MAP = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
    "ruby": {".rb"},
    "go": {".go"},
    "java": {".java", ".kt", ".scala"},
    "php": {".php"},
}
LANG_PATTERNS = {
    "python": PY_PATTERNS,
    "javascript": JS_PATTERNS,
    "ruby": RUBY_PATTERNS,
    "go": GO_PATTERNS,
    "java": JAVA_PATTERNS,
    "php": PHP_PATTERNS,
}
SKIP_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "target",
    ".cache",
    ".pnpm-store",
    ".venv",
    "venv",
    "__pycache__",
    ".astro",
    ".next",
    ".nuxt",
    "vendor",
}
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def should_skip_path(path: Path, include_tests: bool) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    if not include_tests and parts & TEST_DIRS:
        return True
    return False


def detect_language(path: Path, langs: set[str]) -> str | None:
    suf = path.suffix.lower()
    for lang in langs:
        if suf in LANG_EXT_MAP[lang]:
            return lang
    return None


def scan_file(file_path: Path, repo_root: Path, langs: set[str]) -> list[Finding]:
    findings = []
    lang = detect_language(file_path, langs)
    if lang is None:
        return findings
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return findings
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        return findings
    try:
        rel = str(file_path.relative_to(repo_root))
    except ValueError:
        rel = str(file_path)

    for title, sev, pattern, _lang in LANG_PATTERNS[lang]:
        for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            line_no = text[: m.start()].count("\n") + 1
            snippet = text.splitlines()[line_no - 1].strip()[:160]
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"{title} at {rel}:{line_no}",
                    severity=sev,
                    target=f"{rel}:{line_no}",
                    detail=(
                        f"File {rel} line {line_no} matches the {title} "
                        f"pattern: `{snippet}`. If the interpolated value "
                        "is user-reachable, this is a command-injection vector."
                    ),
                    remediation=(
                        "Replace the shell-string call with the argument-vector "
                        "form. Python: subprocess.run([cmd, arg], shell=False). "
                        "Node: spawn(cmd, [arg], {shell: false}). Ruby: "
                        "Open3.capture3(cmd, arg). Go: exec.Command(cmd, arg). "
                        "Java: new ProcessBuilder(Arrays.asList(cmd, arg)). "
                        "See references/PLAYBOOK.md."
                    ),
                    cwe_id="CWE-78",
                    affected_control="OWASP A03:2021",
                    evidence=(("file", rel), ("line", line_no), ("language", lang), ("snippet", snippet)),
                )
            )
    return findings


def walk_repo(root: Path, include_tests: bool, langs: set[str]) -> list[Path]:
    out = []
    valid_exts = set()
    for lang in langs:
        valid_exts |= LANG_EXT_MAP[lang]
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if should_skip_path(p, include_tests):
            continue
        if p.suffix.lower() not in valid_exts:
            continue
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Command-injection pattern scanner")
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--languages", default="all")
    args = parser.parse_args(argv)

    if args.languages == "all":
        langs = set(LANG_PATTERNS.keys())
    else:
        langs = {lang.strip() for lang in args.languages.split(",") if lang.strip() in LANG_PATTERNS}

    root = args.path.resolve()
    if not root.exists():
        sys.stderr.write(f"ERROR: path does not exist: {root}\n")
        return 2

    files = walk_repo(root, args.include_tests, langs)
    findings: list[Finding] = []
    for f in files:
        findings.extend(scan_file(f, root, langs))

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, str(root))
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
