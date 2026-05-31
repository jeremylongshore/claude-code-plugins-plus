#!/usr/bin/env python3
"""Static-analysis scan for SQL-injection vulnerable patterns.

References:
    CWE-89 Improper Neutralization of Special Elements used in an SQL Command
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

SKILL_ID = "detecting-sql-injection-patterns"

# Build the SQL-keyword detector once
SQL_KEYWORDS = r"(?:SELECT|INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|REPLACE\s+INTO|MERGE\s+INTO|UPSERT|DROP\s+\w|TRUNCATE|ALTER\s+\w|CREATE\s+\w|FROM\s+\w|WHERE|JOIN|GROUP\s+BY|ORDER\s+BY)"


def py_patterns():
    """Python SQL-injection patterns."""
    return [
        (
            "Python f-string with SQL keywords",
            Severity.CRITICAL,
            rf"""f["']\s*{SQL_KEYWORDS}\s+[^"']*\{{[^}}]+\}}""",
            "python",
        ),
        (
            "Python cursor.execute with f-string argument",
            Severity.CRITICAL,
            r"""\b(?:cursor|conn|db)\s*\.\s*execute(?:many)?\s*\(\s*f["']""",
            "python",
        ),
        (
            "Python string concat into SQL keyword string",
            Severity.CRITICAL,
            rf"""["']\s*{SQL_KEYWORDS}[^"']*["']\s*\+\s*\w""",
            "python",
        ),
        (
            "Python %-format on SQL string",
            Severity.HIGH,
            rf"""["']\s*{SQL_KEYWORDS}[^"']*%\s*[sdif]?["']\s*%\s*""",
            "python",
        ),
        (
            "Python .format() on SQL string",
            Severity.HIGH,
            rf"""["']\s*{SQL_KEYWORDS}[^"']*\{{[^}}]*\}}[^"']*["']\s*\.\s*format\b""",
            "python",
        ),
        ("Django .extra() with raw SQL", Severity.MEDIUM, r"\.\s*extra\s*\(\s*(?:where|select|tables)\s*=", "python"),
    ]


def js_patterns():
    """JavaScript / TypeScript SQL-injection patterns."""
    return [
        (
            "JS template literal with SQL keywords + interpolation",
            Severity.CRITICAL,
            rf"""`\s*{SQL_KEYWORDS}[^`]*\$\{{[^}}]+\}}""",
            "javascript",
        ),
        (
            "JS sequelize.query with template literal interpolation",
            Severity.HIGH,
            r"""sequelize\s*\.\s*query\s*\(\s*`[^`]*\$\{""",
            "javascript",
        ),
        (
            "JS knex.raw with template literal interpolation",
            Severity.HIGH,
            r"""(?:knex|db)\s*\.\s*raw\s*\(\s*`[^`]*\$\{""",
            "javascript",
        ),
        (
            "JS knex.raw with string concat",
            Severity.HIGH,
            r"""(?:knex|db)\s*\.\s*raw\s*\(\s*['"][^'"]*['"]\s*\+\s*\w""",
            "javascript",
        ),
        (
            "JS mysql/pg .query with concat",
            Severity.HIGH,
            rf"""\.\s*query\s*\(\s*["']\s*{SQL_KEYWORDS}[^"']*["']\s*\+\s*\w""",
            "javascript",
        ),
    ]


def ruby_patterns():
    """Ruby SQL-injection patterns."""
    return [
        ("Rails .where with string interpolation", Severity.HIGH, r"""\.\s*where\s*\(\s*["'][^"']*\#\{""", "ruby"),
        (
            "Rails find_by_sql with string interpolation",
            Severity.HIGH,
            r"""\.\s*find_by_sql\s*\(\s*["'][^"']*\#\{""",
            "ruby",
        ),
        (
            "Rails connection.execute with interpolation",
            Severity.CRITICAL,
            r"""ActiveRecord::Base\.connection\s*\.\s*execute\s*\(\s*["'][^"']*\#\{""",
            "ruby",
        ),
    ]


def go_patterns():
    """Go SQL-injection patterns."""
    return [
        (
            "Go fmt.Sprintf into db.Query/QueryRow/Exec",
            Severity.HIGH,
            r"""(?:Query|QueryRow|Exec)(?:Context)?\s*\(\s*fmt\.Sprintf\s*\(""",
            "go",
        ),
        (
            "Go string concat into db.Query",
            Severity.CRITICAL,
            rf"""(?:Query|QueryRow|Exec)(?:Context)?\s*\(\s*"[^"]*{SQL_KEYWORDS}[^"]*"\s*\+""",
            "go",
        ),
    ]


def java_patterns():
    """Java SQL-injection patterns."""
    return [
        (
            "Java Statement.execute with concat",
            Severity.HIGH,
            rf"""(?:Statement|stmt)\.\s*execute(?:Query|Update)?\s*\(\s*"[^"]*{SQL_KEYWORDS}[^"]*"\s*\+""",
            "java",
        ),
        (
            "Java String.format on SQL string",
            Severity.HIGH,
            rf"""String\.format\s*\(\s*"[^"]*{SQL_KEYWORDS}[^"]*%[sd]""",
            "java",
        ),
    ]


def php_patterns():
    """PHP SQL-injection patterns."""
    return [
        (
            "PHP mysqli_query with interpolated string",
            Severity.CRITICAL,
            rf"""mysqli_query\s*\(\s*\$[a-z_]+\s*,\s*"[^"]*{SQL_KEYWORDS}[^"]*\$""",
            "php",
        ),
        (
            "PHP mysql_query with concat",
            Severity.CRITICAL,
            rf"""mysql_query\s*\(\s*"[^"]*{SQL_KEYWORDS}[^"]*"\s*\.\s*\$""",
            "php",
        ),
        (
            "PHP PDO->query with concat (should be prepare)",
            Severity.HIGH,
            rf"""->query\s*\(\s*"[^"]*{SQL_KEYWORDS}[^"]*"\s*\.\s*\$""",
            "php",
        ),
    ]


def csharp_patterns():
    """C# SQL-injection patterns."""
    return [
        (
            "C# SqlCommand with string interpolation",
            Severity.CRITICAL,
            rf"""new SqlCommand\s*\(\s*\$"[^"]*{SQL_KEYWORDS}[^"]*\{{""",
            "csharp",
        ),
        (
            "C# SqlCommand with string concat",
            Severity.CRITICAL,
            rf"""new SqlCommand\s*\(\s*"[^"]*{SQL_KEYWORDS}[^"]*"\s*\+""",
            "csharp",
        ),
    ]


LANG_EXT_MAP = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
    "ruby": {".rb"},
    "go": {".go"},
    "java": {".java", ".kt", ".scala"},
    "php": {".php"},
    "csharp": {".cs"},
}
LANG_PATTERNS = {
    "python": py_patterns,
    "javascript": js_patterns,
    "ruby": ruby_patterns,
    "go": go_patterns,
    "java": java_patterns,
    "php": php_patterns,
    "csharp": csharp_patterns,
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

    for title, sev, pattern, _lang in LANG_PATTERNS[lang]():
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
                        f"pattern: `{snippet}`. If the interpolated value can "
                        "be influenced by external input, this is a "
                        "SQL-injection vector."
                    ),
                    remediation=(
                        "Replace the string-built query with a parameterized "
                        "query API. Per language: Python sqlite3/psycopg uses "
                        "`?` or `%s` placeholders; Node mysql2/pg uses `?` or "
                        "`$1`; Ruby uses `where(...)` with hash args; Go uses "
                        '`db.Query("SELECT ... WHERE x = ?", arg)`; Java '
                        "PreparedStatement with `setString(1, val)`. See "
                        "references/PLAYBOOK.md for per-language patterns."
                    ),
                    cwe_id="CWE-89",
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
    parser = argparse.ArgumentParser(description="SQL-injection pattern scanner")
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument(
        "--languages", default="all", help="Comma-separated: python,javascript,ruby,go,java,php,csharp (default: all)"
    )
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
