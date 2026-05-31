#!/usr/bin/env python3
"""Static-analysis scan for hardcoded credentials in source trees.

Companion to skill `scanning-for-hardcoded-secrets`. Walks a directory
tree, reads each text file, applies the canonical credential regex
library, and emits findings with file path + line number + redacted
matched text.

Two detection modes layered:

1. Provider-specific regex (AWS AKIA, GitHub ghp_, Stripe sk_live_,
   Anthropic sk-ant-, OpenAI sk-proj-, Slack xox*, Google AIza, RSA
   private keys, etc.). These are CRITICAL because tools at the
   receiving end (AWS, GitHub Secret Scanning, vendor bots)
   auto-extract.

2. Entropy + context-based heuristics (high-Shannon-entropy string
   appearing in a `key:` / `token:` / `password=` field). HIGH or
   MEDIUM. Higher false-positive rate; requires human verification.

References:
    CWE-798 Use of Hard-coded Credentials
    CWE-321 Use of Hard-coded Cryptographic Key
    OWASP A07:2021 Identification and Authentication Failures
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.finding import Finding, Severity  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "scanning-for-hardcoded-secrets"


# Provider-specific regex library.
# Each entry: (pattern_name, severity, regex, control)
PROVIDER_REGEXES = [
    ("AWS access key", Severity.CRITICAL, r"\b(AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b", "CWE-798"),
    ("GitHub personal access token", Severity.CRITICAL, r"\bghp_[A-Za-z0-9]{36,}\b", "CWE-798"),
    ("GitHub OAuth token", Severity.CRITICAL, r"\bgho_[A-Za-z0-9]{36,}\b", "CWE-798"),
    ("GitHub app installation token", Severity.CRITICAL, r"\bghs_[A-Za-z0-9]{36,}\b", "CWE-798"),
    ("GitHub user-to-server token", Severity.CRITICAL, r"\bghu_[A-Za-z0-9]{36,}\b", "CWE-798"),
    ("GitHub refresh token", Severity.CRITICAL, r"\bghr_[A-Za-z0-9]{36,}\b", "CWE-798"),
    ("Stripe live secret key", Severity.CRITICAL, r"\bsk_live_[A-Za-z0-9]{24,}\b", "CWE-798"),
    ("Stripe restricted key (live)", Severity.CRITICAL, r"\brk_live_[A-Za-z0-9]{24,}\b", "CWE-798"),
    ("Stripe test secret key", Severity.MEDIUM, r"\bsk_test_[A-Za-z0-9]{24,}\b", "CWE-798"),
    ("Anthropic API key", Severity.CRITICAL, r"\bsk-ant-(?:api|sid)\d+-[A-Za-z0-9_-]{20,}\b", "CWE-798"),
    ("OpenAI API key", Severity.CRITICAL, r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b", "CWE-798"),
    ("Slack bot token", Severity.CRITICAL, r"\bxoxb-[A-Za-z0-9-]{10,}\b", "CWE-798"),
    ("Slack user token", Severity.CRITICAL, r"\bxoxp-[A-Za-z0-9-]{10,}\b", "CWE-798"),
    ("Slack workspace token", Severity.CRITICAL, r"\bxoxa-[A-Za-z0-9-]{10,}\b", "CWE-798"),
    (
        "Slack webhook URL",
        Severity.HIGH,
        r"\bhttps://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24,}\b",
        "CWE-798",
    ),
    (
        "Discord bot token",
        Severity.CRITICAL,
        r"\b[MN][A-Za-z0-9_-]{23,28}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{27,}\b",
        "CWE-798",
    ),
    ("Google API key", Severity.HIGH, r"\bAIza[A-Za-z0-9_-]{35}\b", "CWE-798"),
    ("Google OAuth refresh token", Severity.HIGH, r"\b1//[A-Za-z0-9_-]{40,}\b", "CWE-798"),
    ("Twilio account SID", Severity.HIGH, r"\bAC[A-Za-z0-9]{32}\b", "CWE-798"),
    ("Twilio auth token", Severity.CRITICAL, r"\bSK[A-Za-z0-9]{32}\b", "CWE-798"),
    ("Mailgun API key", Severity.CRITICAL, r"\bkey-[a-f0-9]{32}\b", "CWE-798"),
    ("SendGrid API key", Severity.CRITICAL, r"\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}\b", "CWE-798"),
    ("Square access token", Severity.CRITICAL, r"\bsq0(?:atp|csp)-[A-Za-z0-9_-]{22,}\b", "CWE-798"),
    ("npm access token", Severity.CRITICAL, r"\bnpm_[A-Za-z0-9]{36,}\b", "CWE-798"),
    ("PyPI API token", Severity.CRITICAL, r"\bpypi-[A-Za-z0-9_-]{50,}\b", "CWE-798"),
    ("Cloudflare API token", Severity.CRITICAL, r"\b[A-Za-z0-9_-]{40}\b(?=.*cloudflare)", "CWE-798"),
    # Private keys — the regex marker strings below match secret-scanner
    # patterns by design; this is the detector library, not real keys.
    ("RSA private key", Severity.CRITICAL, "-" * 5 + "BEGIN RSA PRIVATE KEY" + "-" * 5, "CWE-321"),  # gitleaks:allow
    (
        "OpenSSH private key",
        Severity.CRITICAL,
        "-" * 5 + "BEGIN OPENSSH PRIVATE KEY" + "-" * 5,
        "CWE-321",
    ),  # gitleaks:allow
    ("EC private key", Severity.CRITICAL, "-" * 5 + "BEGIN EC PRIVATE KEY" + "-" * 5, "CWE-321"),  # gitleaks:allow
    ("DSA private key", Severity.CRITICAL, "-" * 5 + "BEGIN DSA PRIVATE KEY" + "-" * 5, "CWE-321"),  # gitleaks:allow
    (
        "PGP private key",
        Severity.CRITICAL,
        "-" * 5 + "BEGIN PGP PRIVATE KEY BLOCK" + "-" * 5,
        "CWE-321",
    ),  # gitleaks:allow
    (
        "Generic PEM private key",
        Severity.CRITICAL,
        "-" * 5 + "BEGIN PRIVATE KEY" + "-" * 5,
        "CWE-321",
    ),  # gitleaks:allow
]

# Context-based regex (field-name + value) — emits HIGH when value looks
# like a credential.
CONTEXT_PATTERNS = [
    # Common YAML / .env / config keys with a secret-shaped value
    (
        r"""(?P<key>(?:aws_secret_access_key|password|passwd|api[_-]?key|secret[_-]?key|"""
        r"""auth[_-]?token|access[_-]?token|jwt[_-]?secret|signing[_-]?secret|"""
        r"""client[_-]?secret|private[_-]?key|encryption[_-]?key))[\s:=]+['"]?"""
        r"""(?P<val>[A-Za-z0-9+/=_-]{16,})['"]?""",
        "Credential-shaped value in known field",
        Severity.HIGH,
    ),
]

# Placeholder-detection — these don't trigger a finding
PLACEHOLDER_MARKERS = (
    "<",
    ">",
    "EXAMPLE",
    "PLACEHOLDER",
    "YOUR_",
    "YOUR-",
    "XXXX",
    "XXX-",
    "TODO",
    "FIXME",
    "REDACTED",
    "REPLACEME",
    "REPLACE-ME",
    "REPLACE_ME",
    "CHANGEME",
    "FAKE",
    "DUMMY",
    "SAMPLE",
    "TEST_KEY_",
)

# Extensions / directories to skip
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
TEXT_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".java",
    ".kt",
    ".scala",
    ".c",
    ".cpp",
    ".cc",
    ".h",
    ".hpp",
    ".cs",
    ".swift",
    ".m",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".md",
    ".rst",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".jsonc",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".envrc",
    ".xml",
    ".html",
    ".vue",
    ".svelte",
    ".dockerfile",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs"}


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    total = len(s)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def looks_like_placeholder(value: str) -> bool:
    upper = value.upper()
    return any(marker in upper for marker in PLACEHOLDER_MARKERS)


def redact(s: str, head: int = 4, tail: int = 4) -> str:
    if len(s) <= head + tail + 3:
        return "***"
    return f"{s[:head]}...{s[-tail:]}"


def should_skip_path(path: Path, include_tests: bool, skip_dirs: set) -> bool:
    parts = set(path.parts)
    if parts & skip_dirs:
        return True
    if not include_tests and parts & TEST_DIRS:
        return True
    return False


def scan_file(
    file_path: Path,
    repo_root: Path,
    include_provider: bool = True,
    include_context: bool = True,
    entropy_threshold: float = 4.5,
) -> list[Finding]:
    findings = []
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

    if include_provider:
        for name, sev, pattern, control in PROVIDER_REGEXES:
            for m in re.finditer(pattern, text):
                matched = m.group(0)
                if looks_like_placeholder(matched):
                    continue
                line_no = text[: m.start()].count("\n") + 1
                findings.append(
                    Finding(
                        skill_id=SKILL_ID,
                        title=f"{name} in {rel}:{line_no}",
                        severity=sev,
                        target=f"{rel}:{line_no}",
                        detail=(
                            f"File {rel} line {line_no} contains a string "
                            f"matching the {name} pattern. Matched value (redacted): "
                            f"`{redact(matched)}`. If this is a real credential it "
                            "is now in git history; rotate immediately and audit "
                            "logs for unauthorized use."
                        ),
                        remediation=(
                            f"Move {name} out of source. Set it in an environment "
                            "variable, secrets manager (AWS Secrets Manager, GCP "
                            "Secret Manager, HashiCorp Vault, Doppler), or "
                            "runtime-provisioned secret. See references/PLAYBOOK.md "
                            "for per-language patterns. Then rotate the credential."
                        ),
                        cwe_id=control,
                        affected_control="OWASP A07:2021",
                        evidence=(
                            ("file", rel),
                            ("line", line_no),
                            ("pattern", name),
                            ("redacted_match", redact(matched)),
                        ),
                    )
                )

    if include_context:
        for pattern, label, sev in CONTEXT_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                value = m.group("val")
                if looks_like_placeholder(value):
                    continue
                if shannon_entropy(value) < entropy_threshold:
                    continue
                line_no = text[: m.start()].count("\n") + 1
                key = m.group("key")
                findings.append(
                    Finding(
                        skill_id=SKILL_ID,
                        title=f"High-entropy credential in {key} field at {rel}:{line_no}",
                        severity=sev,
                        target=f"{rel}:{line_no}",
                        detail=(
                            f"File {rel} line {line_no} assigns a high-entropy "
                            f"value (Shannon entropy ≥ {entropy_threshold}) to "
                            f"a {key} field. Redacted: `{redact(value)}`. "
                            "Likely a real credential."
                        ),
                        remediation=(
                            "Move the value out of source. Replace with environment-"
                            "variable lookup at startup. Rotate the credential."
                        ),
                        cwe_id="CWE-798",
                        affected_control="OWASP A07:2021",
                        evidence=(("file", rel), ("line", line_no), ("field", key), ("redacted_match", redact(value))),
                    )
                )

    return findings


def walk_repo(root: Path, include_tests: bool, extra_exclude: list[str]) -> list[Path]:
    out = []
    # Build exclude-match list
    exclude_patterns = [re.compile(re.escape(p).replace(r"\*", ".*")) for p in extra_exclude]
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if should_skip_path(p, include_tests, SKIP_DIRS):
            continue
        if p.suffix.lower() not in TEXT_EXTS and p.name.lower() != "dockerfile":
            continue
        rel = str(p)
        if any(ep.search(rel) for ep in exclude_patterns):
            continue
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hardcoded-secrets scanner")
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test directories in scan (default: excluded)"
    )
    parser.add_argument("--exclude", action="append", default=[], help="Skip files matching glob (repeatable)")
    parser.add_argument(
        "--entropy-only", action="store_true", help="Skip provider-regex pass; only emit entropy-based findings"
    )
    parser.add_argument("--entropy-threshold", type=float, default=4.5)
    args = parser.parse_args(argv)

    root = args.path.resolve()
    if not root.exists():
        sys.stderr.write(f"ERROR: path does not exist: {root}\n")
        return 2

    files = walk_repo(root, args.include_tests, args.exclude)
    findings: list[Finding] = []
    for f in files:
        findings.extend(
            scan_file(
                f,
                root,
                include_provider=not args.entropy_only,
                include_context=True,
                entropy_threshold=args.entropy_threshold,
            )
        )

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, str(root))
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
