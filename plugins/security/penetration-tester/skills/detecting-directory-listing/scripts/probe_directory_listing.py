#!/usr/bin/env python3
"""Directory-listing probe.

Companion to skill `detecting-directory-listing`. For each candidate
directory path, appends a trailing slash and sends a GET. If the
response is 200 and the body matches a framework-specific autoindex
fingerprint, it's a finding.

References:
    OWASP WSTG-CONF-04 Review Old Backup and Unreferenced Files
    CWE-548 Exposure of Information Through Directory Listing
    nginx autoindex docs, Apache mod_autoindex docs
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

SKILL_ID = "detecting-directory-listing"


# Probe set. Each entry: (path, severity, control)
PROBES = [
    # CRITICAL — config + VCS directories
    ("config/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    ("conf/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    (".config/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    (".git/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    (".git/objects/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    (".svn/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    (".hg/", Severity.CRITICAL, "NIST 800-53 SC-28"),
    # HIGH — backup / upload / log / dump dirs
    ("backup/", Severity.HIGH, "CWE-548"),
    ("backups/", Severity.HIGH, "CWE-548"),
    ("uploads/", Severity.HIGH, "CWE-548"),
    ("upload/", Severity.HIGH, "CWE-548"),
    ("logs/", Severity.HIGH, "CWE-548"),
    ("log/", Severity.HIGH, "CWE-548"),
    ("dump/", Severity.HIGH, "CWE-548"),
    ("dumps/", Severity.HIGH, "CWE-548"),
    ("tmp/", Severity.HIGH, "CWE-548"),
    ("temp/", Severity.HIGH, "CWE-548"),
    ("cache/", Severity.HIGH, "CWE-548"),
    ("data/", Severity.HIGH, "CWE-548"),
    ("private/", Severity.HIGH, "CWE-548"),
    ("internal/", Severity.HIGH, "CWE-548"),
    ("storage/", Severity.HIGH, "CWE-548"),
    ("var/", Severity.HIGH, "CWE-548"),
    ("files/", Severity.HIGH, "CWE-548"),
    # MEDIUM — asset / public-ish dirs (file enumeration enabled)
    ("assets/", Severity.MEDIUM, "CWE-548"),
    ("static/", Severity.MEDIUM, "CWE-548"),
    ("public/", Severity.MEDIUM, "CWE-548"),
    ("media/", Severity.MEDIUM, "CWE-548"),
    ("images/", Severity.MEDIUM, "CWE-548"),
    ("img/", Severity.MEDIUM, "CWE-548"),
    ("downloads/", Severity.MEDIUM, "CWE-548"),
    ("docs/", Severity.MEDIUM, "CWE-548"),
    ("documentation/", Severity.MEDIUM, "CWE-548"),
    ("vendor/", Severity.MEDIUM, "CWE-548"),
    ("node_modules/", Severity.HIGH, "CWE-548"),  # higher: enables specific version-CVE lookup
    ("bower_components/", Severity.HIGH, "CWE-548"),
    # MEDIUM — generic root
    ("", Severity.MEDIUM, "OWASP A05:2021"),  # root itself
]


# Framework-specific autoindex fingerprints applied to first 4 KiB of body
AUTOINDEX_PATTERNS = [
    (r"<title>Index of /", "Apache mod_autoindex"),
    (r"<h1>Index of /", "Apache mod_autoindex / nginx fancyindex"),
    (r"<title>Directory listing for /", "Python http.server"),
    (r"<title>Directory: /", "Caddy file_server browse"),
    (r"<table[^>]*class=['\"]listing", "Caddy file_server browse"),
    (r"<pre><a href=['\"]\.\.['\"]>\.\./</a>", "nginx default autoindex"),
    (r"<head>\s*<title>Index of [^<]+</title>", "Generic autoindex"),
    (r"^\s*<\?xml.+<ListBucketResult", "AWS S3 ListBucket XML"),
    (r"<EnumerationResults", "Azure Blob list-blob XML"),
    (r"<title>Objects:", "GCS bucket browse"),
    (r"<h1>Listing", "Rails / Rack::Directory listing"),
    (r"<title>Index - /", "Lighttpd mod_dirlisting"),
    (r"^\s*<!DOCTYPE\s+html>[\s\S]+<h1>\s*Index of\s+/", "Variant Index of"),
]


def _is_autoindex(body_text: str) -> tuple[bool, str | None]:
    """Returns (matched, framework_name) — True if body looks like an autoindex page."""
    sample = (body_text or "")[:4096]
    for pattern, framework in AUTOINDEX_PATTERNS:
        if re.search(pattern, sample, re.MULTILINE | re.IGNORECASE):
            return True, framework
    return False, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Directory-listing probe")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--paths-file", default=None, help="Custom probe set (one path per line); replaces default")
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    sess = make_session(timeout=args.timeout)
    base = args.url.rstrip("/") + "/"
    findings: list[Finding] = []

    probe_set = PROBES
    if args.paths_file:
        paths = Path(args.paths_file).read_text().splitlines()
        probe_set = [(p.strip().rstrip("/") + "/", Severity.MEDIUM, "custom") for p in paths if p.strip()]

    for path, sev, control in probe_set:
        url = base + path.lstrip("/")
        resp = safe_get(sess, url, timeout=args.timeout, allow_redirects=False)
        if resp is None or resp.status_code != 200:
            continue
        body = resp.text or ""
        ctype = resp.headers.get("Content-Type", "")
        # Reject application/* responses (e.g. JSON APIs returning a 200) —
        # those aren't autoindex pages
        if "html" not in ctype.lower() and "xml" not in ctype.lower():
            continue
        matched, framework = _is_autoindex(body)
        if not matched:
            continue
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"Directory listing exposed at /{path} ({framework})",
                severity=sev,
                target=url,
                detail=(
                    f"GET {url} returned 200 with HTML body matching the "
                    f"{framework} autoindex fingerprint. Every file in this "
                    "directory is enumerable to any external requestor, "
                    "including files the application never explicitly linked to."
                ),
                remediation=(
                    f"Disable autoindex for {path!r} at the web-server layer. "
                    "See references/PLAYBOOK.md for per-server snippets "
                    "(nginx `autoindex off`, Apache `Options -Indexes`, "
                    "Caddy drop the `file_server browse` directive, S3 "
                    "remove `s3:ListBucket` from the public bucket policy)."
                ),
                cwe_id="CWE-548",
                affected_control=control,
                evidence=(
                    ("framework", framework or "unknown"),
                    ("content_type", ctype),
                    ("body_sample_len", len(body)),
                ),
            )
        )

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, args.url)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
