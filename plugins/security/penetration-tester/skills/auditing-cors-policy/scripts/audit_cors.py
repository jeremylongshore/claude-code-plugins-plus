#!/usr/bin/env python3
"""CORS policy auditor.

Companion to skill `auditing-cors-policy`. Probes the target with multiple
synthetic Origin values and grades the responses against known
misconfiguration patterns.

Checks performed:
    1. Baseline (no Origin) — establishes default headers
    2. Safe Origin — probes legitimate cross-origin behavior
    3. Attacker Origin — checks for blind reflection (CWE-942)
    4. Subdomain-bypass Origin — tests pattern matching weaknesses
    5. Origin:null — tests sandboxed-iframe / data: URL trust
    6. Preflight OPTIONS — checks Access-Control-Max-Age + allowed methods
    7. Allow-Credentials + wildcard combination — the worst-case combo
    8. Vary:Origin header presence — CDN poisoning risk

References:
    Fetch Standard (https://fetch.spec.whatwg.org/) — CORS protocol
    MDN CORS documentation — common misconfigurations
    OWASP A05:2021 Security Misconfiguration
    CWE-942 Permissive Cross-domain Policy with Untrusted Domains
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.authz_check import require_authorization  # noqa: E402
from lib.finding import Finding, Severity  # noqa: E402
from lib.http_client import make_session, safe_options  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "auditing-cors-policy"

# Synthetic origins used to probe behavior
ATTACKER_ORIGIN = "https://attacker.example"
SUBDOMAIN_BYPASS_ORIGIN = None  # computed per-target — see _subdomain_bypass_origin
NULL_ORIGIN = "null"


def _subdomain_bypass_origin(target_host: str) -> str:
    """Build an Origin that exploits a `*.example.com` regex written as
    `.endsWith('.example.com')` — appending a different parent domain.
    """
    # If target is api.example.com, bypass = api.example.com.attacker.com
    return f"https://{target_host}.attacker.com"


def _probe(sess, method: str, url: str, origin: str | None, timeout: float):
    headers = {}
    if origin is not None:
        headers["Origin"] = origin
    try:
        resp = sess.request(method, url, headers=headers, timeout=timeout, allow_redirects=False)
    except Exception:
        return None
    return resp


def _check_baseline(resp, target: str) -> list[Finding]:
    findings = []
    if resp is None:
        return findings
    allow_origin = resp.headers.get("Access-Control-Allow-Origin")
    allow_creds = resp.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
    if allow_origin == "*" and allow_creds:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="Allow-Credentials:true with Allow-Origin:* (browser rejects, server asserts worst)",
                severity=Severity.CRITICAL,
                target=target,
                detail=(
                    "The server returns Access-Control-Allow-Origin:* AND "
                    "Access-Control-Allow-Credentials:true on the same response. "
                    "Browsers reject this combination per Fetch standard, but the "
                    "server is asserting it would allow ANY origin to read "
                    "credentialed responses if the browser cooperated. This "
                    "signals the developer intent is wrong — fix immediately."
                ),
                remediation=(
                    "If the endpoint needs credentials cross-origin: replace * "
                    "with a specific allow-list of trusted origins, set "
                    "Vary:Origin, and validate Origin against the allow-list "
                    "server-side. If credentials aren't needed: drop "
                    "Allow-Credentials:true."
                ),
                cwe_id="CWE-942",
                owasp_category="A05:2021",
                affected_control="OWASP A05:2021",
                references=("https://fetch.spec.whatwg.org/#cors-protocol-and-credentials",),
            )
        )
    return findings


def _check_reflection(resp_attacker, resp_safe, target: str) -> list[Finding]:
    """If the attacker-origin probe gets that origin back in Allow-Origin,
    the server is doing blind reflection. Pair with credentials = critical.
    """
    findings = []
    if resp_attacker is None:
        return findings
    allow_origin_attacker = resp_attacker.headers.get("Access-Control-Allow-Origin", "")
    allow_creds_attacker = resp_attacker.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
    if allow_origin_attacker == ATTACKER_ORIGIN:
        sev = Severity.CRITICAL if allow_creds_attacker else Severity.HIGH
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="Origin header reflected without validation",
                severity=sev,
                target=target,
                detail=(
                    "The server echoed the synthetic Origin "
                    f"({ATTACKER_ORIGIN}) into Access-Control-Allow-Origin. "
                    + (
                        "Combined with Allow-Credentials:true, ANY origin can "
                        "read authenticated responses from this endpoint — full "
                        "session theft is possible via a malicious page the "
                        "victim visits while logged in."
                        if allow_creds_attacker
                        else "Any origin can read unauthenticated responses; "
                        "consequences are bounded but the configuration is wrong."
                    )
                ),
                remediation=(
                    "Replace reflection logic with an allow-list check. Common "
                    "framework patterns: Express cors() with `origin: ['https://a',"
                    " 'https://b']`; Spring `@CrossOrigin(origins = {\"https://a\"})`;"
                    ' FastAPI `CORSMiddleware(allow_origins=["https://a"])`. '
                    "Always set Vary:Origin when serving per-origin responses."
                ),
                cwe_id="CWE-942",
                owasp_category="A05:2021",
                affected_control="OWASP A05:2021",
                references=("https://cwe.mitre.org/data/definitions/942.html",),
            )
        )
    return findings


def _check_subdomain_bypass(resp_bypass, bypass_origin: str, target: str) -> list[Finding]:
    if resp_bypass is None:
        return []
    if resp_bypass.headers.get("Access-Control-Allow-Origin") == bypass_origin:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Subdomain-pattern CORS check bypassed via parent-domain append",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    f"Origin {bypass_origin!r} accepted. The server's allow-list "
                    "logic likely uses substring or endsWith() matching against "
                    "the trusted parent domain, which fails on attacker-controlled "
                    "subdomains under a different root."
                ),
                remediation=(
                    "Replace string-suffix matching with exact-equal or proper "
                    "URL parsing: extract the hostname from the Origin and check "
                    "exact equality against an allow-list."
                ),
                cwe_id="CWE-942",
            )
        ]
    return []


def _check_null_origin(resp_null, target: str) -> list[Finding]:
    if resp_null is None:
        return []
    if resp_null.headers.get("Access-Control-Allow-Origin") == "null":
        creds = resp_null.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Allow-Origin:null trusted (sandboxed iframes, data: URLs)",
                severity=Severity.CRITICAL if creds else Severity.HIGH,
                target=target,
                detail=(
                    "The server returns Allow-Origin:null. Sandboxed iframes "
                    "and data: URLs send Origin:null; an attacker can host "
                    "a malicious page in a sandboxed iframe to satisfy this "
                    "check and read responses."
                ),
                remediation="Never trust Origin:null. Remove it from the allow-list.",
                cwe_id="CWE-942",
            )
        ]
    return []


def _check_vary(resp_safe, target: str) -> list[Finding]:
    if resp_safe is None:
        return []
    allow_origin = resp_safe.headers.get("Access-Control-Allow-Origin")
    vary = resp_safe.headers.get("Vary", "")
    # If Allow-Origin is anything other than * (i.e., per-origin), Vary:Origin
    # must be set, else CDNs cache one origin's response for everyone.
    if allow_origin and allow_origin != "*" and "origin" not in vary.lower():
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Per-origin Allow-Origin without Vary:Origin (CDN poisoning risk)",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "The response varies CORS headers by Origin but does not "
                    "include Origin in the Vary header. CDNs and shared caches "
                    "may serve one origin's Allow-Origin response to a different "
                    "origin's requests."
                ),
                remediation=(
                    "Add `Vary: Origin` to every response that varies CORS "
                    "headers by Origin. nginx: `add_header Vary Origin always;`."
                ),
                affected_control="RFC 7234",
                references=("https://datatracker.ietf.org/doc/html/rfc7234#section-4.1",),
            )
        ]
    return []


def _check_preflight(resp_preflight, target: str) -> list[Finding]:
    if resp_preflight is None:
        return []
    findings = []
    max_age = resp_preflight.headers.get("Access-Control-Max-Age", "")
    try:
        max_age_int = int(max_age) if max_age else 0
    except ValueError:
        max_age_int = 0
    if max_age_int > 86400:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"Preflight cache exceeds 24h ({max_age_int}s)",
                severity=Severity.LOW,
                target=target,
                detail=(
                    "Access-Control-Max-Age is set very high, which prevents the "
                    "browser from re-requesting preflight when CORS policy "
                    "changes. Revocation agility is reduced."
                ),
                remediation="Cap Access-Control-Max-Age at 86400 (24h) or lower.",
            )
        )
    allow_methods = resp_preflight.headers.get("Access-Control-Allow-Methods", "")
    if "*" in allow_methods:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="Allow-Methods:* permits arbitrary HTTP methods",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "The preflight response permits ALL methods. Pair with any "
                    "CORS misconfiguration above for cross-origin CSRF on state-"
                    "changing methods."
                ),
                remediation=(
                    "Enumerate explicit methods the endpoint actually supports: "
                    "`Access-Control-Allow-Methods: GET, POST, PUT, DELETE`."
                ),
                owasp_category="A05:2021",
            )
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CORS policy auditor")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--method", default="GET", help="HTTP method for the main probe (default GET)")
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    parsed = urllib.parse.urlparse(args.url)
    target_host = parsed.hostname or "unknown"
    target = args.url

    sess = make_session(timeout=args.timeout)
    bypass_origin = _subdomain_bypass_origin(target_host)
    safe_origin = "https://allowed.example.com"

    # Six probes
    resp_baseline = _probe(sess, args.method, args.url, None, args.timeout)
    resp_safe = _probe(sess, args.method, args.url, safe_origin, args.timeout)
    resp_attacker = _probe(sess, args.method, args.url, ATTACKER_ORIGIN, args.timeout)
    resp_bypass = _probe(sess, args.method, args.url, bypass_origin, args.timeout)
    resp_null = _probe(sess, args.method, args.url, NULL_ORIGIN, args.timeout)
    resp_preflight = safe_options(
        sess,
        args.url,
        timeout=args.timeout,
        headers={
            "Origin": safe_origin,
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    if resp_baseline is None:
        sys.stderr.write(f"ERROR: target {target!r} unreachable\n")
        return 2

    findings: list[Finding] = []
    findings.extend(_check_baseline(resp_baseline, target))
    findings.extend(_check_reflection(resp_attacker, resp_safe, target))
    findings.extend(_check_subdomain_bypass(resp_bypass, bypass_origin, target))
    findings.extend(_check_null_origin(resp_null, target))
    findings.extend(_check_vary(resp_safe, target))
    findings.extend(_check_preflight(resp_preflight, target))

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    if not findings:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="No CORS misconfiguration detected in standard probe set",
                severity=Severity.INFO,
                target=target,
                detail="The 6-probe sweep did not surface any threshold violations.",
                remediation="No action needed; re-run on any CORS-config change.",
            )
        )

    emit(findings, args.output, args.format, target)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
