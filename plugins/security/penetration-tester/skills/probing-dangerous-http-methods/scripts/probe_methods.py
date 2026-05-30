#!/usr/bin/env python3
"""HTTP method probe — flags methods that shouldn't be enabled.

Companion to skill `probing-dangerous-http-methods`. Sends each
canonical "dangerous" method against the target and grades the response.

Methods probed:
    TRACE     — XST attack vector (RFC 7231 §4.3.8)
    PUT       — unrestricted upload (CWE-434)
    DELETE    — unauthorized resource removal
    CONNECT   — proxy abuse (CWE-441)
    DEBUG     — legacy IIS/dev-server diagnostic
    PROPFIND  — WebDAV directory listing (RFC 4918)
    MKCOL     — WebDAV directory creation
    COPY      — WebDAV file copy
    MOVE      — WebDAV file move
    OPTIONS   — enumerate Allow header (informational, can disclose)

References:
    RFC 7231 §4.3 — HTTP method semantics
    RFC 4918 — WebDAV
    OWASP WSTG-CONF-06 — Test HTTP Methods
    CWE-441 Unintended Proxy or Intermediary
    CWE-538 File and Directory Information Exposure
    CWE-693 Protection Mechanism Failure (XST)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.authz_check import require_authorization  # noqa: E402
from lib.finding import Finding, Severity  # noqa: E402
from lib.http_client import make_session  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "probing-dangerous-http-methods"

# Probe set — (method, expected_failure_codes, severity_if_succeeds, finding_template)
DANGEROUS_METHODS = [
    ("TRACE", {405, 403, 404, 400, 501}, Severity.HIGH, "TRACE method enabled (XST attack vector)"),
    ("CONNECT", {405, 403, 400, 501, 502}, Severity.CRITICAL, "CONNECT method enabled (proxy abuse)"),
    ("DEBUG", {405, 403, 404, 501}, Severity.HIGH, "DEBUG method enabled (legacy diagnostic)"),
    ("PROPFIND", {405, 403, 404, 501}, Severity.HIGH, "WebDAV PROPFIND enabled"),
    ("MKCOL", {405, 403, 404, 501}, Severity.HIGH, "WebDAV MKCOL enabled"),
    ("COPY", {405, 403, 404, 501}, Severity.HIGH, "WebDAV COPY enabled"),
    ("MOVE", {405, 403, 404, 501}, Severity.HIGH, "WebDAV MOVE enabled"),
]

# These are only "dangerous" outside API endpoints
API_DEPENDENT_METHODS = [
    ("PUT", {405, 403, 404, 401}, Severity.HIGH, "PUT method enabled outside API path"),
    ("DELETE", {405, 403, 404, 401}, Severity.HIGH, "DELETE method enabled outside API path"),
]


def _probe_method(sess, method: str, url: str, timeout: float):
    try:
        # Use sess.request to handle non-standard methods (PROPFIND, MKCOL, etc.)
        resp = sess.request(method, url, timeout=timeout, allow_redirects=False)
        return resp
    except Exception:
        return None


def _grade_response(
    method: str, resp, expected_fail: set, severity: Severity, title: str, target: str, is_xst: bool = False
) -> list[Finding]:
    if resp is None:
        return []
    if resp.status_code in expected_fail:
        return []  # Method correctly blocked
    if resp.status_code >= 500:
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"{method} returns {resp.status_code} (error handling concern)",
                severity=Severity.INFO,
                target=target,
                detail=(
                    f"The {method} method returned {resp.status_code}. While "
                    "blocking is the intended behavior, a 500 suggests the server "
                    "tried to handle the method and crashed — better to return "
                    "405 cleanly."
                ),
                remediation=f"Configure the server to return 405 Method Not Allowed for {method}.",
            )
        ]
    # Status 2xx, 3xx, or 405-like — the method was handled successfully or
    # at least not cleanly rejected. This is the finding.
    detail = (
        f"The {method} method returned status {resp.status_code}. "
        f"This method should be rejected with 405 Method Not Allowed."
    )
    if is_xst:
        # Check if the response body echoes the request — confirms XST
        if "TRACE / HTTP" in (resp.text or "") or method.encode() in (resp.content or b""):
            detail += (
                " Response body echoes the request, confirming XST viability. "
                "An attacker who can execute JavaScript on the origin can "
                "use TRACE-via-XHR to read HttpOnly cookies."
            )

    return [
        Finding(
            skill_id=SKILL_ID,
            title=title,
            severity=severity,
            target=target,
            detail=detail,
            remediation=_remediation_for(method),
            cwe_id=_cwe_for(method),
            owasp_category="A05:2021",
            evidence=(("status_code", resp.status_code), ("response_len", len(resp.content or b""))),
        )
    ]


def _remediation_for(method: str) -> str:
    base = {
        "TRACE": (
            "Disable TRACE explicitly. nginx: `if ($request_method = TRACE) "
            "{ return 405; }`. Apache: `TraceEnable Off`. "
            "Load balancers (ALB/Cloudflare): block at the LB level."
        ),
        "CONNECT": (
            "Disable CONNECT. nginx and Apache reject by default; if you see "
            "this enabled, you have a misconfigured proxy. Audit your reverse "
            "proxy rules for `proxy_method` or `ProxyRequests On`."
        ),
        "DEBUG": (
            "Legacy IIS / dev-server method. Disable in production. "
            "IIS: remove DEBUG verb from handler mappings. Express dev "
            "middleware: ensure NODE_ENV=production."
        ),
        "PUT": (
            "If this endpoint shouldn't accept PUT, return 405. nginx: "
            "`limit_except GET POST { deny all; }`. Express: ensure no "
            "PUT route handler is registered."
        ),
        "DELETE": (
            "If this endpoint shouldn't accept DELETE, return 405. Same "
            "pattern as PUT above. If DELETE should be available, ensure "
            "authentication + authorization are wired."
        ),
        "PROPFIND": "Disable WebDAV. nginx: `dav_methods off;`. Apache: `<Limit PROPFIND>Require all denied</Limit>`.",
        "MKCOL": "Disable WebDAV — see PROPFIND remediation.",
        "COPY": "Disable WebDAV — see PROPFIND remediation.",
        "MOVE": "Disable WebDAV — see PROPFIND remediation.",
    }
    return base.get(method, f"Disable {method} method at the server level.")


def _cwe_for(method: str) -> str:
    mapping = {
        "TRACE": "CWE-693",
        "CONNECT": "CWE-441",
        "DEBUG": "CWE-489",
        "PUT": "CWE-434",
        "DELETE": "CWE-285",
        "PROPFIND": "CWE-538",
        "MKCOL": "CWE-538",
        "COPY": "CWE-538",
        "MOVE": "CWE-538",
    }
    return mapping.get(method, "CWE-200")


def _check_options(sess, url: str, timeout: float, target: str) -> list[Finding]:
    try:
        resp = sess.options(url, timeout=timeout, allow_redirects=False)
    except Exception:
        return []
    if resp is None:
        return []
    allow = resp.headers.get("Allow", "")
    if not allow:
        return []
    if "*" in allow:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="OPTIONS Allow header is wildcard",
                severity=Severity.LOW,
                target=target,
                detail="Server advertises Allow:* — information disclosure.",
                remediation="Configure server to return explicit allowed-method list.",
                cwe_id="CWE-200",
            )
        ]
    methods = [m.strip().upper() for m in allow.split(",")]
    unused = [m for m in methods if m in {"DEBUG", "TRACE", "PROPFIND", "MKCOL", "COPY", "MOVE", "CONNECT"}]
    if unused:
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"OPTIONS Allow header discloses unused methods: {', '.join(unused)}",
                severity=Severity.LOW,
                target=target,
                detail=(
                    "The Allow header lists methods that are typically not used "
                    "in a modern web app. Either disable them or remove from "
                    "the Allow advertisement."
                ),
                remediation="See findings on individual methods for remediation steps.",
                cwe_id="CWE-200",
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HTTP method probe")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--is-api", action="store_true", help="Target is an API endpoint (PUT/DELETE are expected)")
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    sess = make_session(timeout=args.timeout)
    target = args.url
    findings: list[Finding] = []

    method_set = list(DANGEROUS_METHODS)
    if not args.is_api:
        method_set.extend(API_DEPENDENT_METHODS)

    for method, expected_fail, sev, title in method_set:
        resp = _probe_method(sess, method, args.url, args.timeout)
        findings.extend(
            _grade_response(
                method,
                resp,
                expected_fail,
                sev,
                title,
                target,
                is_xst=(method == "TRACE"),
            )
        )

    findings.extend(_check_options(sess, args.url, args.timeout, target))

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, target)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
