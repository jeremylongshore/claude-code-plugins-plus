#!/usr/bin/env python3
"""Static-analysis scan for eval / exec / dynamic-code-execution APIs.

References:
    CWE-95 Improper Neutralization of Directives in Dynamically Evaluated Code
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

SKILL_ID = "detecting-eval-exec-usage"

PY_PATTERNS = [
    ("Python eval()", Severity.CRITICAL, r"\beval\s*\(\s*(?!['\"])", "python"),
    ("Python exec()", Severity.CRITICAL, r"\bexec\s*\(\s*(?!['\"])", "python"),
    ("Python compile() with non-literal", Severity.HIGH, r"\bcompile\s*\(\s*(?!['\"])", "python"),
    ("Python __import__ with variable", Severity.HIGH, r"__import__\s*\(\s*(?!['\"])", "python"),
    (
        "Python pickle.loads (eval-class deserialization)",
        Severity.HIGH,
        r"\bpickle\.loads?\s*\(",
        "python",
    ),  # cross-listed; #14 covers in depth
]
JS_PATTERNS = [
    ("JavaScript eval()", Severity.CRITICAL, r"\beval\s*\(", "javascript"),
    (
        "JavaScript new Function() with non-literal",
        Severity.CRITICAL,
        r"new\s+Function\s*\(\s*(?!['\"`])",
        "javascript",
    ),
    ("JavaScript setTimeout with string arg", Severity.HIGH, r"setTimeout\s*\(\s*['\"`]", "javascript"),
    ("JavaScript setInterval with string arg", Severity.HIGH, r"setInterval\s*\(\s*['\"`]", "javascript"),
]
RUBY_PATTERNS = [
    ("Ruby eval()", Severity.CRITICAL, r"\beval\s*\(", "ruby"),
    (
        "Ruby instance_eval / class_eval with non-block",
        Severity.HIGH,
        r"\b(?:instance_eval|class_eval|module_eval)\s*\(\s*['\"]",
        "ruby",
    ),
]
PHP_PATTERNS = [
    ("PHP eval()", Severity.CRITICAL, r"\beval\s*\(", "php"),
    ("PHP assert() with string (legacy eval form)", Severity.CRITICAL, r"\bassert\s*\(\s*['\"$]", "php"),
    ("PHP create_function (deprecated, eval-equivalent)", Severity.CRITICAL, r"\bcreate_function\s*\(", "php"),
]
JAVA_PATTERNS = [
    ("Java ScriptEngine.eval", Severity.HIGH, r"\bScriptEngine[A-Za-z]*\b.*\.eval\s*\(", "java"),
    ("Java GroovyShell.evaluate", Severity.HIGH, r"\bGroovyShell\b.*\.evaluate\s*\(", "java"),
]
CSHARP_PATTERNS = [
    (
        "C# Activator.CreateInstance(Type.GetType(str))",
        Severity.HIGH,
        r"Activator\.CreateInstance\s*\(\s*Type\.GetType\s*\(",
        "csharp",
    ),
    ("C# Reflection.Emit", Severity.MEDIUM, r"\bReflection\.Emit\b", "csharp"),
]

LANG_EXT_MAP = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
    "ruby": {".rb"},
    "php": {".php"},
    "java": {".java", ".kt", ".scala"},
    "csharp": {".cs"},
}
LANG_PATTERNS = {
    "python": PY_PATTERNS,
    "javascript": JS_PATTERNS,
    "ruby": RUBY_PATTERNS,
    "php": PHP_PATTERNS,
    "java": JAVA_PATTERNS,
    "csharp": CSHARP_PATTERNS,
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
        for m in re.finditer(pattern, text, re.MULTILINE):
            line_no = text[: m.start()].count("\n") + 1
            snippet = text.splitlines()[line_no - 1].strip()[:160]
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"{title} at {rel}:{line_no}",
                    severity=sev,
                    target=f"{rel}:{line_no}",
                    detail=(
                        f"File {rel} line {line_no} uses {title}: `{snippet}`. "
                        "If the evaluated string is user-reachable, this is "
                        "an arbitrary-code-execution vector."
                    ),
                    remediation=(
                        "Replace dynamic code execution with explicit logic "
                        "(lookup table, switch statement) or a sandboxed "
                        "expression library. Python: simpleeval / ast.literal_eval. "
                        "JS: expr-eval / mathjs. Ruby: Dentaku. See "
                        "references/PLAYBOOK.md."
                    ),
                    cwe_id="CWE-95",
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
    parser = argparse.ArgumentParser(description="eval / exec usage scanner")
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
