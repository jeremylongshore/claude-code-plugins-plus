#!/usr/bin/env python3
"""Static-analysis scan for insecure-deserialization API usage.

References:
    CWE-502 Deserialization of Untrusted Data
    OWASP A08:2021 Software and Data Integrity Failures
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

SKILL_ID = "detecting-insecure-deserialization"


PY_PATTERNS = [
    ("Python pickle.loads", Severity.CRITICAL, r"\b(?:cPickle|pickle)\.loads?\s*\(", "python"),
    ("Python dill.loads", Severity.CRITICAL, r"\bdill\.loads?\s*\(", "python"),
    (
        "Python yaml.load() without Loader=Safe",
        Severity.CRITICAL,
        r"\byaml\.load\s*\((?![^)]*Loader\s*=\s*[Yy]aml\.(?:Safe|safe_load))",
        "python",
    ),
    ("Python yaml.unsafe_load (explicit unsafe)", Severity.CRITICAL, r"\byaml\.unsafe_load\s*\(", "python"),
    ("Python yaml.full_load", Severity.HIGH, r"\byaml\.full_load\s*\(", "python"),
    ("Python shelve.open (pickle-backed)", Severity.HIGH, r"\bshelve\.open\s*\(", "python"),
    ("Python marshal.loads (legacy, unsafe)", Severity.CRITICAL, r"\bmarshal\.loads?\s*\(", "python"),
]
JS_PATTERNS = [
    (
        "Node node-serialize.unserialize (known-vulnerable lib)",
        Severity.CRITICAL,
        r"require\s*\(\s*['\"]node-serialize['\"]\s*\)|from\s+['\"]node-serialize['\"]",
        "javascript",
    ),
    ("JSON.parse with reviver function", Severity.MEDIUM, r"JSON\.parse\s*\([^,)]+,\s*function\s*\(", "javascript"),
]
RUBY_PATTERNS = [
    ("Ruby Marshal.load on non-literal", Severity.CRITICAL, r"\bMarshal\.load\s*\(\s*(?!['\"])", "ruby"),
    ("Ruby YAML.load without permitted_classes", Severity.HIGH, r"\bYAML\.load\s*\((?![^)]*permitted_classes)", "ruby"),
]
JAVA_PATTERNS = [
    ("Java ObjectInputStream.readObject", Severity.CRITICAL, r"\bObjectInputStream\b[^;]*\.readObject\s*\(", "java"),
    (
        "Java XMLDecoder.readObject (unsafe XML deserialization)",
        Severity.CRITICAL,
        r"\bXMLDecoder\b[^;]*\.readObject\s*\(",
        "java",
    ),
    ("Java SnakeYAML new Yaml() default constructor (unsafe)", Severity.HIGH, r"new\s+Yaml\s*\(\s*\)", "java"),
]
PHP_PATTERNS = [
    ("PHP unserialize on non-literal", Severity.CRITICAL, r"\bunserialize\s*\(\s*(?!['\"])", "php"),
]
CSHARP_PATTERNS = [
    (
        "C# BinaryFormatter.Deserialize (deprecated unsafe)",
        Severity.CRITICAL,
        r"\bBinaryFormatter\s*\(?\s*\)?\s*\.\s*Deserialize\s*\(",
        "csharp",
    ),
    (
        "C# NetDataContractSerializer.ReadObject",
        Severity.CRITICAL,
        r"\bNetDataContractSerializer\b[^;]*\.(?:Read|Deserialize)",
        "csharp",
    ),
    (
        "C# LosFormatter.Deserialize (ViewState)",
        Severity.CRITICAL,
        r"\bLosFormatter\b[^;]*\.Deserialize\s*\(",
        "csharp",
    ),
    (
        "C# ObjectStateFormatter.Deserialize (ViewState)",
        Severity.CRITICAL,
        r"\bObjectStateFormatter\b[^;]*\.Deserialize\s*\(",
        "csharp",
    ),
    (
        "C# JavaScriptSerializer with SimpleTypeResolver",
        Severity.HIGH,
        r"new\s+JavaScriptSerializer\s*\(\s*new\s+SimpleTypeResolver",
        "csharp",
    ),
]


LANG_EXT_MAP = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
    "ruby": {".rb"},
    "java": {".java", ".kt", ".scala"},
    "php": {".php"},
    "csharp": {".cs"},
}
LANG_PATTERNS = {
    "python": PY_PATTERNS,
    "javascript": JS_PATTERNS,
    "ruby": RUBY_PATTERNS,
    "java": JAVA_PATTERNS,
    "php": PHP_PATTERNS,
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
                        f"File {rel} line {line_no} calls {title}: `{snippet}`. "
                        "If the input is attacker-controllable, this is an "
                        "arbitrary-code-execution vector via deserialization "
                        "gadget chains."
                    ),
                    remediation=(
                        "Migrate to a schema-validated format. Python: json + "
                        "Pydantic. Ruby: JSON with strict schema. Java: Jackson "
                        "with allow-list. PHP: json_decode. .NET: System.Text.Json. "
                        "If polymorphic types are required, use HMAC-signed "
                        "serialization with explicit type allow-list. See "
                        "references/PLAYBOOK.md."
                    ),
                    cwe_id="CWE-502",
                    affected_control="OWASP A08:2021",
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
    parser = argparse.ArgumentParser(description="Insecure-deserialization scanner")
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
