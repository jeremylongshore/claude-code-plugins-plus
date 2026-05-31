#!/usr/bin/env python3
"""Server-software fingerprinting via HTTP response signatures.

Companion to skill `fingerprinting-server-software`. Sends a baseline
GET + an OPTIONS + optionally a malformed-request error probe, then
parses every standard fingerprinting header and Set-Cookie name
pattern.

Each match grades against the threshold table in the skill body:
explicit-version disclosures are MEDIUM (CWE-200), framework
identification without version is LOW, stack-trace disclosure from
error pages is HIGH (CWE-209).

References:
    OWASP WSTG-INFO-02 Fingerprint Web Server
    OWASP WSTG-INFO-08 Fingerprint Web Application Framework
    CWE-200 Information Exposure
    CWE-209 Information Exposure Through an Error Message
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
from lib.http_client import make_session, safe_get, safe_options  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "fingerprinting-server-software"


# Headers that commonly leak version
VERSION_HEADERS = [
    "Server",
    "X-Powered-By",
    "X-AspNet-Version",
    "X-AspNetMvc-Version",
    "X-Runtime",
    "X-Generator",
    "X-Drupal-Cache",
    "X-Drupal-Dynamic-Cache",
    "X-Backend-Server",
    "X-Server-Powered-By",
    "X-Joomla-Version",
]
# Framework identification headers (lower severity — no version)
FRAMEWORK_HEADERS = [
    "X-Rails-Version",
    "X-Django-Version",
    "X-Frame-Options",  # only if present along with other framework signals
    "Via",
]
# Framework-default Set-Cookie names (low — identifies stack)
DEFAULT_COOKIES = {
    "PHPSESSID": "PHP",
    "JSESSIONID": "Java EE / Tomcat / WebSphere / WebLogic",
    "ASP.NET_SessionId": "ASP.NET",
    "ASPSESSIONID": "Classic ASP",
    "ASPSESSIONID*": "Classic ASP (pattern)",
    "connect.sid": "Express + connect.session",
    "session": "Generic — multiple frameworks",
    "_session_id": "Rails",
    "laravel_session": "Laravel",
    "ci_session": "CodeIgniter",
    "frontend": "Magento",
    "X-Mapping-*": "Sun ONE / iPlanet load-balancer",
    "BIGipServer*": "F5 BIG-IP load-balancer",
    "AWSALB": "AWS ALB",
    "AWSELB": "AWS ELB classic",
}
# Error-page stack-trace fingerprints
STACK_TRACE_SIGS = [
    (r"^[ \t]*at\s+[\w.<>$]+\([\w./\\:?]+:\d+\)", "Java stack trace"),
    (r"File\s+\"[/\\][\w/.\\]+\.py\",\s+line\s+\d+", "Python traceback"),
    (r"in\s+/[^\s]+\.php on line \d+", "PHP error trace"),
    (r"at\s+(?:[\w$]+\.)+[\w$]+\s+\([\w./:\\]+:\d+:\d+\)", "JavaScript stack trace"),
    (r"\(in /[\w/.-]+\.rb:\d+", "Ruby exception"),
    (r"goroutine\s+\d+\s+\[running\]:", "Go panic"),
    (r"System\.[\w.]+Exception:", ".NET exception"),
    (r"<title>[^<]*(stack trace|exception|fatal error)", "Generic error-page banner"),
]


def _version_in(value: str) -> bool:
    """Heuristic: header value contains an explicit version number."""
    return bool(re.search(r"\d+\.\d+", value))


def _check_version_headers(headers, target, source_label):
    findings = []
    for h in VERSION_HEADERS:
        v = headers.get(h)
        if not v:
            continue
        has_version = _version_in(v)
        sev = Severity.MEDIUM if has_version else Severity.LOW
        # Specific: X-AspNet-Version always shows runtime version — HIGH
        if h.lower().startswith("x-aspnet") and has_version:
            sev = Severity.HIGH
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"{h} header discloses {'version' if has_version else 'product'}: {v[:80]}",
                severity=sev,
                target=target,
                detail=(
                    f"The {source_label} response includes {h}: {v!r}. "
                    "Attackers query published CVE catalogs for the disclosed "
                    "version + family to enumerate exploitable conditions "
                    "without further probing."
                ),
                remediation=_remediation_for_header(h),
                cwe_id="CWE-200",
                affected_control="OWASP A05:2021",
                references=("https://cwe.mitre.org/data/definitions/200.html",),
                evidence=((f"header:{h}", v),),
            )
        )
    return findings


def _check_framework_headers(headers, target, source_label):
    findings = []
    for h in FRAMEWORK_HEADERS:
        v = headers.get(h)
        if not v:
            continue
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"{h} header discloses stack identification: {v[:80]}",
                severity=Severity.LOW,
                target=target,
                detail=(
                    f"The {source_label} response includes {h}: {v!r}. "
                    "Framework identification without version. Combined with "
                    "version-bearing headers, informs CVE lookup."
                ),
                remediation=_remediation_for_header(h),
                cwe_id="CWE-200",
                affected_control="OWASP A05:2021",
                evidence=((f"header:{h}", v),),
            )
        )
    return findings


def _check_cookies(headers, target):
    findings = []
    set_cookie = headers.get("Set-Cookie", "")
    if not set_cookie:
        return findings
    # requests joins multiple Set-Cookie headers with comma in .headers; iterate
    # cookie names separately
    for cookie_blob in set_cookie.split(","):
        # cookie name is the first token before '='
        name = cookie_blob.split("=", 1)[0].strip()
        for default_name, framework in DEFAULT_COOKIES.items():
            if default_name.endswith("*"):
                if name.startswith(default_name.rstrip("*")):
                    break
            elif name == default_name:
                break
        else:
            continue
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"Framework-default cookie name discloses stack: {name} ({framework})",
                severity=Severity.LOW,
                target=target,
                detail=(
                    f"Set-Cookie name {name!r} matches the conventional "
                    f"default for {framework}. Combined with other signals, "
                    "informs framework + version inference."
                ),
                remediation=(
                    "Rename the session cookie to a non-default value. In "
                    "Express: app.use(session({name: 'sid', ...})). In Spring: "
                    "server.servlet.session.cookie.name=sid. In Rails: "
                    "config.session_store :cookie_store, key: '_sid'."
                ),
                cwe_id="CWE-200",
                affected_control="OWASP A05:2021",
            )
        )
    return findings


def _check_etag(headers, target):
    etag = headers.get("ETag", "")
    if not etag:
        return []
    # Apache hex-ETag format: "<inode>-<size>-<mtime>"
    if re.match(r'^"[0-9a-f]+-[0-9a-f]+-[0-9a-f]+"$', etag):
        return [
            Finding(
                skill_id=SKILL_ID,
                title="ETag format reveals Apache inode-size-mtime triple (cluster-member fingerprint)",
                severity=Severity.LOW,
                target=target,
                detail=(
                    f"The ETag {etag!r} matches Apache's default "
                    "inode-size-mtime format. Across a load-balanced cluster, "
                    "the inode portion distinguishes individual nodes, enabling "
                    "node-by-node probing."
                ),
                remediation=(
                    "Apache: `FileETag MTime Size` (drop inode). Or `FileETag None` to disable ETags entirely."
                ),
                cwe_id="CWE-200",
            )
        ]
    return []


def _check_error_disclosure(body_text, target):
    findings = []
    sample = (body_text or "")[:8192]
    for pattern, name in STACK_TRACE_SIGS:
        if re.search(pattern, sample, re.MULTILINE | re.IGNORECASE):
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"Error page leaks {name}",
                    severity=Severity.HIGH,
                    target=target,
                    detail=(
                        f"The error response body contains content matching "
                        f"the {name} pattern. Server-internal file paths, "
                        "function names, and framework details are visible to "
                        "any external requestor that triggers an error."
                    ),
                    remediation=(
                        "Disable detailed error pages in production. Per-stack: "
                        "Django DEBUG=False, Rails Rails.application.config."
                        "consider_all_requests_local=false, Spring "
                        "server.error.include-stacktrace=never, ASP.NET "
                        "customErrors mode='RemoteOnly', Express "
                        "app.use(errorHandler({log:false,debug:false}))."
                    ),
                    cwe_id="CWE-209",
                    affected_control="OWASP A05:2021",
                )
            )
            break  # only flag the first stack-trace pattern that matches
    return findings


def _remediation_for_header(header: str) -> str:
    return {
        "Server": (
            "nginx: `server_tokens off;`. Apache: `ServerTokens Prod`. "
            "Caddy: omitted by default (Caddy 2.x). IIS: "
            "URL Rewrite module → outbound rule to strip header. "
            "ALB / CloudFront: response-header policy to drop Server."
        ),
        "X-Powered-By": (
            "PHP: `expose_php = Off` in php.ini. "
            "Express: `app.disable('x-powered-by')` or `helmet({hidePoweredBy:true})`. "
            "ASP.NET: web.config customHeaders → removeHeader X-Powered-By."
        ),
        "X-AspNet-Version": ('web.config: `<httpRuntime enableVersionHeader="false" />`.'),
        "X-AspNetMvc-Version": ("Global.asax: `MvcHandler.DisableMvcResponseHeader = true;`."),
        "X-Runtime": ("Rails: `config.action_dispatch.runtime_response_header = nil`."),
        "X-Generator": (
            "Drupal: settings.php → set $config['system.performance']['cache']['page']['max_age']. "
            "Wordpress: remove_action('wp_head', 'wp_generator')."
        ),
        "X-Drupal-Cache": "Drupal: configure reverse proxy to strip the header before serving.",
        "X-Drupal-Dynamic-Cache": "Drupal: same as above.",
        "X-Joomla-Version": "Joomla: remove from template metadata.",
        "Via": (
            "If the Via header is from your reverse proxy, configure the proxy "
            "to omit. nginx: `proxy_set_header Via '';`. CloudFront: "
            "response-header policy to strip Via."
        ),
        "X-Rails-Version": "Rails: middleware customization to strip header.",
        "X-Django-Version": "Django: middleware to strip header.",
    }.get(header, f"Configure the web stack to omit the {header} header on outbound responses.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Server-software fingerprinter")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--trigger-error", action="store_true", help="Send a malformed request to surface error-page disclosure"
    )
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    sess = make_session(timeout=args.timeout)
    findings: list[Finding] = []

    # Baseline GET
    resp = safe_get(sess, args.url, timeout=args.timeout, allow_redirects=False)
    if resp is None:
        sys.stderr.write(f"ERROR: target {args.url!r} unreachable\n")
        return 2
    headers = dict(resp.headers)
    findings.extend(_check_version_headers(headers, args.url, "baseline GET"))
    findings.extend(_check_framework_headers(headers, args.url, "baseline GET"))
    findings.extend(_check_cookies(headers, args.url))
    findings.extend(_check_etag(headers, args.url))

    # OPTIONS — different code path may reveal different headers
    options_resp = safe_options(sess, args.url, timeout=args.timeout)
    if options_resp is not None:
        opt_headers = dict(options_resp.headers)
        # Only flag headers that DIDN'T appear in the GET (dedupe)
        for h in VERSION_HEADERS + FRAMEWORK_HEADERS:
            if h in opt_headers and h not in headers:
                findings.extend(_check_version_headers({h: opt_headers[h]}, args.url, "OPTIONS"))
                findings.extend(_check_framework_headers({h: opt_headers[h]}, args.url, "OPTIONS"))

    # Optional: error-page disclosure
    if args.trigger_error:
        # Send a request with deliberately-malformed path
        err_url = args.url.rstrip("/") + "/this-route-should-not-exist-" + ("X" * 200)
        err_resp = safe_get(sess, err_url, timeout=args.timeout, allow_redirects=False)
        if err_resp is not None and err_resp.status_code >= 400:
            findings.extend(_check_error_disclosure(err_resp.text, args.url))

    # Severity floor
    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, args.url)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
