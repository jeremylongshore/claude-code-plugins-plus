#!/usr/bin/env python3
"""HTTP security headers auditor.

Companion to skill `checking-http-security-headers`. Probes the target
GET response and grades each canonical security header.

Checks performed:
    1. Strict-Transport-Security — presence, max-age, includeSubDomains, preload
    2. Content-Security-Policy — presence, unsafe-inline, unsafe-eval,
       frame-ancestors
    3. X-Frame-Options — present OR CSP frame-ancestors set
    4. X-Content-Type-Options:nosniff
    5. Referrer-Policy — present, not unsafe-url
    6. Permissions-Policy
    7. Server: header version disclosure
    8. Cache-Control on authenticated endpoint

References:
    MDN — HTTP security headers
    OWASP Secure Headers Project (https://owasp.org/www-project-secure-headers/)
    Mozilla Observatory
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

SKILL_ID = "checking-http-security-headers"

PRELOAD_MIN_MAX_AGE = 31536000  # 1 year (hstspreload.org requirement)


def _check_hsts(headers: dict, target: str, is_https: bool) -> list[Finding]:
    findings: list[Finding] = []
    if not is_https:
        return findings
    hsts = headers.get("Strict-Transport-Security")
    if not hsts:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Strict-Transport-Security header missing",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    "No HSTS header on the HTTPS response. The first time a "
                    "client visits the site over HTTPS (or any first-visit after "
                    "their HSTS cache expires), an attacker on the network can "
                    "rewrite the response to use HTTP — and clients have no "
                    "pinning to refuse the downgrade."
                ),
                remediation=(
                    "Add: `Strict-Transport-Security: max-age=31536000; "
                    "includeSubDomains; preload`. nginx: `add_header "
                    'Strict-Transport-Security "max-age=31536000; '
                    'includeSubDomains; preload" always;`.'
                ),
                cwe_id="CWE-319",
                owasp_category="A05:2021",
                references=("https://hstspreload.org/",),
            )
        ]
    # Parse max-age
    m = re.search(r"max-age\s*=\s*(\d+)", hsts)
    if m:
        max_age = int(m.group(1))
        if max_age < PRELOAD_MIN_MAX_AGE:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"HSTS max-age ({max_age}s) below preload threshold",
                    severity=Severity.MEDIUM,
                    target=target,
                    detail=(
                        f"HSTS max-age is {max_age}s. hstspreload.org requires "
                        f"≥{PRELOAD_MIN_MAX_AGE}s (1 year) for preload-list "
                        "submission."
                    ),
                    remediation=f"Increase max-age to {PRELOAD_MIN_MAX_AGE}.",
                )
            )
    if "preload" in hsts.lower() and "includesubdomains" not in hsts.lower():
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="HSTS preload directive without includeSubDomains",
                severity=Severity.LOW,
                target=target,
                detail=("The preload directive requires includeSubDomains per hstspreload.org policy."),
                remediation="Add `includeSubDomains` to the HSTS header value.",
            )
        )
    return findings


def _check_csp(headers: dict, target: str) -> list[Finding]:
    findings: list[Finding] = []
    csp = headers.get("Content-Security-Policy") or headers.get("Content-Security-Policy-Report-Only")
    if not csp:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Content-Security-Policy header missing",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    "No CSP. The browser will execute any inline script the "
                    "server (or any injection vector) returns. Reflected and "
                    "stored XSS classes are unmitigated."
                ),
                remediation=(
                    "Start with a report-only policy: "
                    "`Content-Security-Policy-Report-Only: default-src 'self'; "
                    "report-uri /csp-report`. Move to enforcing once violations "
                    "settle. See references/PLAYBOOK.md § CSP rollout."
                ),
                cwe_id="CWE-79",
                owasp_category="A03:2021",
            )
        ]
    if "'unsafe-inline'" in csp:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="CSP includes 'unsafe-inline'",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "'unsafe-inline' permits inline <script> and onclick= "
                    "handlers. This is the most common XSS-protection bypass."
                ),
                remediation=(
                    "Replace inline handlers with addEventListener; replace "
                    "inline styles with classes; if migration is gradual, use "
                    "nonce-source or hash-source CSP entries per script block."
                ),
                cwe_id="CWE-79",
                owasp_category="A03:2021",
            )
        )
    if "'unsafe-eval'" in csp:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="CSP includes 'unsafe-eval'",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "'unsafe-eval' permits eval(), new Function(), and similar. "
                    "Most modern frameworks (React/Vue/Angular in production "
                    "mode) don't need this."
                ),
                remediation=(
                    "Audit dependencies for eval usage; replace or upgrade. "
                    "Common offenders: older Angular dev mode, older Vue "
                    "with template-runtime."
                ),
            )
        )
    return findings


def _check_clickjacking(headers: dict, target: str) -> list[Finding]:
    xfo = headers.get("X-Frame-Options", "").lower()
    csp = (headers.get("Content-Security-Policy") or "").lower()
    if xfo or "frame-ancestors" in csp:
        return []
    return [
        Finding(
            skill_id=SKILL_ID,
            title="No clickjacking protection (X-Frame-Options + frame-ancestors both absent)",
            severity=Severity.HIGH,
            target=target,
            detail=(
                "Neither X-Frame-Options nor CSP frame-ancestors is set. The "
                "page can be embedded in an attacker's iframe and used for "
                "UI-redress (clickjacking) attacks against authenticated "
                "users."
            ),
            remediation=(
                "Add `X-Frame-Options: DENY` for pages never embedded, or "
                "`Content-Security-Policy: frame-ancestors 'self' "
                "https://embedded-by.example.com` for selective embedding."
            ),
            cwe_id="CWE-1021",
        )
    ]


def _check_nosniff(headers: dict, target: str) -> list[Finding]:
    if headers.get("X-Content-Type-Options", "").lower() == "nosniff":
        return []
    return [
        Finding(
            skill_id=SKILL_ID,
            title="X-Content-Type-Options:nosniff missing",
            severity=Severity.MEDIUM,
            target=target,
            detail=(
                "Without nosniff, browsers may MIME-sniff a response served "
                "as text/plain and execute it as JavaScript if it looks "
                "script-shaped. Closes a class of file-upload XSS."
            ),
            remediation="Add `X-Content-Type-Options: nosniff` to every response.",
            cwe_id="CWE-79",
        )
    ]


def _check_referrer(headers: dict, target: str) -> list[Finding]:
    rp = headers.get("Referrer-Policy", "").lower()
    if not rp:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Referrer-Policy missing",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "Without a Referrer-Policy, the browser uses no-referrer-"
                    "when-downgrade by default — internal URLs leak to external "
                    "sites the user navigates to."
                ),
                remediation=("Add `Referrer-Policy: strict-origin-when-cross-origin` (the modern recommendation)."),
            )
        ]
    if rp in ("unsafe-url",):
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"Referrer-Policy:{rp} leaks full URL cross-origin",
                severity=Severity.MEDIUM,
                target=target,
                detail="unsafe-url sends the full URL to every cross-origin destination.",
                remediation="Change to `strict-origin-when-cross-origin`.",
            )
        ]
    return []


def _check_permissions_policy(headers: dict, target: str) -> list[Finding]:
    if headers.get("Permissions-Policy"):
        return []
    return [
        Finding(
            skill_id=SKILL_ID,
            title="Permissions-Policy header missing",
            severity=Severity.LOW,
            target=target,
            detail=(
                "Without Permissions-Policy, the browser permits the page to "
                "request all device capabilities (camera, mic, geo, USB, "
                "serial). On a public-content page these should be denied by "
                "default."
            ),
            remediation=(
                "Add `Permissions-Policy: camera=(), microphone=(), "
                "geolocation=(), interest-cohort=()` (deny-all baseline)."
            ),
        )
    ]


def _check_server_disclosure(headers: dict, target: str) -> list[Finding]:
    server = headers.get("Server", "")
    if re.search(r"\d+\.\d+", server):
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"Server header discloses version: {server}",
                severity=Severity.LOW,
                target=target,
                detail=(
                    "The Server header includes a version number, letting "
                    "fingerprinters target known CVEs in that exact version."
                ),
                remediation=(
                    "nginx: `server_tokens off;`. "
                    "Apache: `ServerTokens Prod`. "
                    "Caddy: omit version by default (Caddy 2.x doesn't disclose)."
                ),
                cwe_id="CWE-200",
            )
        ]
    return []


def _check_cache_control(headers: dict, target: str, authenticated: bool) -> list[Finding]:
    cc = headers.get("Cache-Control", "").lower()
    if authenticated and ("public" in cc or "max-age" in cc and "private" not in cc and "no-store" not in cc):
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Authenticated endpoint allows shared caching",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    "Authenticated content with public-cacheable Cache-Control "
                    "can be served by shared caches (CDN, corporate proxy) to "
                    "different users — one user's authenticated response leaks "
                    "to another."
                ),
                remediation=("Set `Cache-Control: private, no-store` on every authenticated endpoint."),
                cwe_id="CWE-525",
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HTTP security headers auditor")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--authenticated", action="store_true", help="Apply stricter Cache-Control checks")
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    sess = make_session(timeout=args.timeout)
    resp = safe_get(sess, args.url, timeout=args.timeout)
    if resp is None:
        sys.stderr.write(f"ERROR: target {args.url!r} unreachable\n")
        return 2

    is_https = args.url.lower().startswith("https://")
    target = args.url

    findings: list[Finding] = []
    findings.extend(_check_hsts(dict(resp.headers), target, is_https))
    findings.extend(_check_csp(dict(resp.headers), target))
    findings.extend(_check_clickjacking(dict(resp.headers), target))
    findings.extend(_check_nosniff(dict(resp.headers), target))
    findings.extend(_check_referrer(dict(resp.headers), target))
    findings.extend(_check_permissions_policy(dict(resp.headers), target))
    findings.extend(_check_server_disclosure(dict(resp.headers), target))
    findings.extend(_check_cache_control(dict(resp.headers), target, args.authenticated))

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, target)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
