#!/usr/bin/env python3
"""Probe for accidentally-served secret-bearing files in the web root.

Companion to skill `detecting-exposed-secrets-files`. Sends a GET for
each path in a curated 40+ probe set. For 200 responses, fingerprints
the body to distinguish a real file from an SPA index page that 200s
on any route.

References:
    OWASP WSTG v4.2 § 4.2.4 Enumerate Infrastructure / Application
    NIST SP 800-53 SC-28 Protection of Information at Rest
    CWE-538 File and Directory Information Exposure
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.authz_check import require_authorization  # noqa: E402
from lib.finding import Finding, Severity  # noqa: E402
from lib.http_client import make_session, safe_get  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "detecting-exposed-secrets-files"


# Probe set. Each entry: (path, label, severity, body_fingerprint_regex_or_None, control)
# fingerprint_regex applied case-insensitively against first 2 KiB of body.
PROBES = [
    # Critical - direct credential / source / data exposure
    (
        ".git/HEAD",
        "Git repository .git/HEAD exposed",
        Severity.CRITICAL,
        r"^(ref:\s*refs/|[0-9a-f]{40})",
        "NIST 800-53 SC-28",
    ),
    (
        ".git/config",
        "Git repository .git/config exposed (may include remote credentials)",
        Severity.CRITICAL,
        r"\[remote\b",
        "NIST 800-53 SC-28",
    ),
    (".git/index", "Git repository .git/index exposed", Severity.CRITICAL, r"^DIRC", "NIST 800-53 SC-28"),
    (
        ".git/logs/HEAD",
        "Git repository ref log exposed",
        Severity.CRITICAL,
        r"[0-9a-f]{40}\s+[0-9a-f]{40}",
        "NIST 800-53 SC-28",
    ),
    (
        ".env",
        ".env file exposed (likely contains API keys, DB credentials)",
        Severity.CRITICAL,
        r"^[A-Z_][A-Z0-9_]*\s*=",
        "OWASP A05:2021",
    ),
    (".env.production", ".env.production exposed", Severity.CRITICAL, r"^[A-Z_][A-Z0-9_]*\s*=", "OWASP A05:2021"),
    (".env.local", ".env.local exposed", Severity.CRITICAL, r"^[A-Z_][A-Z0-9_]*\s*=", "OWASP A05:2021"),
    (
        ".aws/credentials",
        "AWS credentials file exposed",
        Severity.CRITICAL,
        r"\[default\]|aws_access_key_id",
        "CWE-200",
    ),
    (".aws/config", "AWS config file exposed", Severity.CRITICAL, r"\[default\]|region\s*=", "CWE-200"),
    ("id_rsa", "SSH private key exposed", Severity.CRITICAL, r"BEGIN\s+(RSA|OPENSSH|EC|DSA)?\s*PRIVATE KEY", "CWE-321"),
    ("id_ed25519", "SSH ed25519 private key exposed", Severity.CRITICAL, r"BEGIN\s+OPENSSH\s+PRIVATE KEY", "CWE-321"),
    ("server.pem", "Server PEM key exposed", Severity.CRITICAL, r"BEGIN\s+(RSA\s+)?PRIVATE KEY", "CWE-321"),
    ("backup.sql", "SQL backup exposed", Severity.CRITICAL, r"CREATE\s+TABLE|INSERT\s+INTO", "CWE-538"),
    ("dump.sql", "SQL dump exposed", Severity.CRITICAL, r"CREATE\s+TABLE|INSERT\s+INTO", "CWE-538"),
    ("database.sql", "Database SQL exposed", Severity.CRITICAL, r"CREATE\s+TABLE|INSERT\s+INTO", "CWE-538"),
    ("backup.zip", "Archive backup.zip exposed", Severity.CRITICAL, None, "CWE-538"),
    ("backup.tar.gz", "Archive backup.tar.gz exposed", Severity.CRITICAL, None, "CWE-538"),
    ("dump.tar.gz", "Archive dump.tar.gz exposed", Severity.CRITICAL, None, "CWE-538"),
    # High - VCS metadata (less direct than .git but still source-of-truth-leaking)
    (".svn/entries", "Subversion .svn/entries exposed", Severity.HIGH, r"^\d+\s|^svn:", "NIST 800-53 SC-28"),
    (".svn/wc.db", "Subversion working copy DB exposed", Severity.HIGH, r"^SQLite", "NIST 800-53 SC-28"),
    (".hg/store/00manifest.i", "Mercurial repo manifest exposed", Severity.HIGH, None, "NIST 800-53 SC-28"),
    (".bzr/branch-format", "Bazaar branch format exposed", Severity.HIGH, r"Bazaar", "NIST 800-53 SC-28"),
    # Medium - useful enumeration for attacker
    (
        ".DS_Store",
        "macOS .DS_Store exposed (reveals directory structure)",
        Severity.MEDIUM,
        r"^Bud1|^\x00\x00\x00\x01Bud1",
        "CWE-538",
    ),
    ("Thumbs.db", "Windows Thumbs.db exposed", Severity.MEDIUM, None, "CWE-538"),
    ("phpinfo.php", "phpinfo() output exposed", Severity.MEDIUM, r"PHP Version|phpinfo\(\)", "CWE-200"),
    ("info.php", "PHP info exposed", Severity.MEDIUM, r"PHP Version|phpinfo\(\)", "CWE-200"),
    ("test.php", "Test PHP file exposed", Severity.MEDIUM, r"PHP Version|phpinfo\(\)", "CWE-200"),
    # Low - infrastructure metadata
    (".idea/workspace.xml", "JetBrains IDE config exposed", Severity.LOW, r"<project", "CWE-200"),
    (".vscode/settings.json", "VS Code config exposed", Severity.LOW, r"^\s*\{", "CWE-200"),
    (".gitlab-ci.yml", "GitLab CI config exposed", Severity.LOW, r"stages:|script:", "CWE-200"),
    (".github/workflows/", "GitHub Actions workflows dir exposed", Severity.LOW, None, "CWE-200"),
    ("Dockerfile", "Dockerfile exposed", Severity.LOW, r"^FROM\s+", "CWE-200"),
    ("docker-compose.yml", "docker-compose.yml exposed", Severity.LOW, r"^version:|services:", "CWE-200"),
    ("composer.json", "PHP composer.json exposed on web root", Severity.LOW, r'"name":\s*"', "CWE-200"),
    ("package.json", "Node package.json exposed on web root", Severity.LOW, r'"name":\s*"', "CWE-200"),
    ("requirements.txt", "Python requirements.txt exposed", Severity.LOW, r"^[a-zA-Z][a-zA-Z0-9_.-]*[=<>]", "CWE-200"),
    ("Gemfile", "Ruby Gemfile exposed", Severity.LOW, r"^source\s+['\"]https", "CWE-200"),
    ("config.yml", "Generic config.yml exposed", Severity.LOW, None, "CWE-200"),
    ("config.json", "Generic config.json exposed", Severity.LOW, r"^\s*\{", "CWE-200"),
    ("README.md", "README.md exposed on production web root", Severity.LOW, r"^#\s+", "CWE-200"),
]


def _verify_fingerprint(body_text: str, fingerprint_re: str | None, content_type: str) -> bool:
    """Return True if response body looks like the expected file type."""
    if fingerprint_re is None:
        # No fingerprint check requested (e.g. binary archives) — trust the 200
        return True
    # Inspect first 2 KiB
    sample = body_text[:2048]
    if re.search(fingerprint_re, sample, re.MULTILINE | re.IGNORECASE):
        return True
    # If server claimed it's HTML / SPA, treat as false positive
    if "text/html" in content_type.lower():
        return False
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe for exposed secrets files")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--paths-file", default=None, help="Custom probe set (one path per line); replaces default")
    parser.add_argument(
        "--check-only", action="store_true", help="Skip body fingerprint check (treat any 200 as a finding)"
    )
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    base = args.url.rstrip("/") + "/"
    sess = make_session(timeout=args.timeout)
    findings: list[Finding] = []

    if args.paths_file:
        paths = Path(args.paths_file).read_text().splitlines()
        probe_set = [
            (p.strip(), f"Custom path exposed: {p.strip()}", Severity.MEDIUM, None, "custom")
            for p in paths
            if p.strip()
        ]
    else:
        probe_set = PROBES

    for path, title, sev, fingerprint, control in probe_set:
        url = base + path.lstrip("/")
        resp = safe_get(sess, url, timeout=args.timeout, allow_redirects=False)
        if resp is None or resp.status_code != 200:
            continue
        body = resp.text or ""
        ctype = resp.headers.get("Content-Type", "")
        if not args.check_only and not _verify_fingerprint(body, fingerprint, ctype):
            continue
        evidence = (("status_code", 200), ("content_length", len(resp.content or b"")), ("content_type", ctype))
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=title,
                severity=sev,
                target=url,
                detail=(
                    f"GET {url} returned 200 with content matching the expected "
                    f"signature of {path!r}. The file is publicly reachable "
                    "and likely contains sensitive data."
                ),
                remediation=(
                    f"Configure the web server to deny requests to {path!r} and "
                    "the directory it lives in. See references/PLAYBOOK.md for "
                    "nginx / Apache / Caddy / ALB snippets per category."
                ),
                cwe_id=None,
                affected_control=control,
                evidence=evidence,
            )
        )

    # Severity floor
    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    target_display = args.url
    emit(findings, args.output, args.format, target_display)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
