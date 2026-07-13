#!/usr/bin/env python3
"""Probe for accidentally-public admin / debug / introspection endpoints.

Companion to skill `detecting-debug-endpoints`. Sends a GET for each
path in a curated 40+ probe set covering Spring Boot Actuator, Apache
mod_status, Prometheus metrics, GraphQL playground, Swagger UI,
phpMyAdmin, Jolokia, Elasticsearch _cat, and generic admin/debug
panels.

Each 200 response is fingerprinted against the framework-specific
body pattern (Actuator returns `{"_links":...}`, mod_status returns
HTML containing "Apache Server Status", Prometheus returns
`# HELP`/`# TYPE` lines, etc.) so SPA index pages that 200 on every
route don't generate false positives.

References:
    OWASP WSTG v4.2 § 4.2.4 Enumerate Infrastructure
    OWASP A05:2021 Security Misconfiguration
    CWE-749 Exposed Dangerous Method
    CWE-285 Improper Authorization
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

SKILL_ID = "detecting-debug-endpoints"


# Probe set. Each entry: (path, title, severity, fingerprint_regex_or_None, control_id, cwe)
# fingerprint_regex applied case-insensitively against first 4 KiB of body.
PROBES = [
    # Critical — Spring Boot Actuator with sensitive endpoints exposed
    (
        "actuator/env",
        "Spring Boot Actuator /env exposed (leaks every environment variable)",
        Severity.CRITICAL,
        r'"propertySources"|"systemProperties"|"applicationConfig"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/heapdump",
        "Spring Boot Actuator /heapdump exposed (live heap snapshot)",
        Severity.CRITICAL,
        None,  # body is binary multi-MB; presence of 200 + content-length large is the signal
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/jolokia",
        "Spring Boot Actuator /jolokia exposed (JMX-over-HTTP, potential RCE)",
        Severity.CRITICAL,
        r'"agent"\s*:\s*"jolokia"|"protocol"\s*:\s*"jolokia"',
        "OWASP A05:2021",
        "CWE-749",
    ),
    (
        "actuator/threaddump",
        "Spring Boot Actuator /threaddump exposed (live thread state)",
        Severity.HIGH,
        r'"threads"\s*:\s*\[',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/loggers",
        "Spring Boot Actuator /loggers exposed (can change log levels remotely)",
        Severity.HIGH,
        r'"loggers"\s*:\s*\{|"configuredLevel"',
        "OWASP A05:2021",
        "CWE-749",
    ),
    (
        "actuator/configprops",
        "Spring Boot Actuator /configprops exposed (app config disclosure)",
        Severity.HIGH,
        r'"contexts"\s*:\s*\{|"beans"\s*:\s*\{',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/mappings",
        "Spring Boot Actuator /mappings exposed (full route table)",
        Severity.MEDIUM,
        r'"mappings"\s*:|"dispatcherServlets"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/beans",
        "Spring Boot Actuator /beans exposed (bean introspection)",
        Severity.MEDIUM,
        r'"beans"\s*:\s*\{|"applicationContext"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/metrics",
        "Spring Boot Actuator /metrics exposed",
        Severity.MEDIUM,
        r'"names"\s*:\s*\[',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator/health",
        "Spring Boot Actuator /health exposed (reveals dependency states)",
        Severity.MEDIUM,
        r'"status"\s*:\s*"(UP|DOWN|OUT_OF_SERVICE)"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "actuator",
        "Spring Boot Actuator index page exposed",
        Severity.HIGH,
        r'"_links"\s*:\s*\{',
        "OWASP A05:2021",
        "CWE-200",
    ),
    # phpMyAdmin — DB admin GUI
    (
        "phpmyadmin/",
        "phpMyAdmin reachable (if unauthed: full DB access)",
        Severity.CRITICAL,
        r"phpMyAdmin|pma_navigation|pma_username",
        "OWASP A07:2021",
        "CWE-285",
    ),
    (
        "pma/",
        "phpMyAdmin reachable at /pma/",
        Severity.CRITICAL,
        r"phpMyAdmin|pma_navigation",
        "OWASP A07:2021",
        "CWE-285",
    ),
    # Apache mod_status
    (
        "server-status",
        "Apache mod_status /server-status exposed (reveals internal request URLs + IPs)",
        Severity.HIGH,
        r"Apache Server Status|<title>Apache Status</title>",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "server-info",
        "Apache mod_info /server-info exposed (full config disclosure)",
        Severity.HIGH,
        r"Apache Server Information|Server Settings",
        "OWASP A05:2021",
        "CWE-200",
    ),
    # nginx status
    (
        "nginx_status",
        "nginx stub_status exposed",
        Severity.MEDIUM,
        r"Active connections:\s*\d+\nserver accepts handled",
        "OWASP A05:2021",
        "CWE-200",
    ),
    # Prometheus
    (
        "metrics",
        "Prometheus /metrics endpoint exposed (operational telemetry, may contain credentials in labels)",
        Severity.HIGH,
        r"^# HELP\s|^# TYPE\s",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "prometheus/api/v1/query",
        "Prometheus query API exposed",
        Severity.HIGH,
        r'"status"\s*:\s*"(success|error)"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    # Elasticsearch
    (
        "_cat/indices",
        "Elasticsearch /_cat/indices exposed (no auth)",
        Severity.HIGH,
        r"^(green|yellow|red)\s+(open|close)",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "_cluster/health",
        "Elasticsearch /_cluster/health exposed",
        Severity.HIGH,
        r'"cluster_name"\s*:|"number_of_nodes"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "_search",
        "Elasticsearch /_search exposed (no auth)",
        Severity.CRITICAL,
        r'"hits"\s*:\s*\{|"took"\s*:\s*\d+',
        "OWASP A05:2021",
        "CWE-285",
    ),
    # Kibana / Grafana / Eureka / Consul panels
    (
        "kibana/",
        "Kibana UI reachable",
        Severity.MEDIUM,
        r"kbn-name|Kibana|kbn-version",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "grafana/api/health",
        "Grafana exposed at /grafana/",
        Severity.MEDIUM,
        r'"database"\s*:\s*"(ok|fail)"|"version"',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "eureka/apps",
        "Spring Cloud Eureka registry exposed",
        Severity.HIGH,
        r"<applications>|EUREKA",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "consul/v1/catalog/services",
        "Consul catalog API exposed",
        Severity.HIGH,
        r"^\s*\{|consul",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "v1/agent/checks",
        "Consul agent checks API exposed",
        Severity.HIGH,
        r'"Checks"\s*:|^\s*\{',
        "OWASP A05:2021",
        "CWE-200",
    ),
    # GraphQL
    (
        "graphql",
        "GraphQL endpoint reachable",
        Severity.LOW,
        r'"data"\s*:|"errors"\s*:',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "graphiql",
        "GraphiQL IDE reachable on prod",
        Severity.MEDIUM,
        r"GraphiQL|graphql-playground",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "playground",
        "GraphQL Playground reachable on prod",
        Severity.MEDIUM,
        r"GraphQLPlayground|graphql-playground",
        "OWASP A05:2021",
        "CWE-200",
    ),
    # OpenAPI / Swagger
    (
        "swagger-ui/",
        "Swagger UI reachable on prod",
        Severity.MEDIUM,
        r"swagger-ui|SwaggerUI",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "swagger-ui.html",
        "Swagger UI reachable (Spring conventional path)",
        Severity.MEDIUM,
        r"swagger-ui|SwaggerUI",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "api-docs",
        "OpenAPI /api-docs JSON reachable",
        Severity.LOW,
        r'"openapi"\s*:|"swagger"\s*:',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "openapi.json",
        "OpenAPI spec /openapi.json reachable",
        Severity.LOW,
        r'"openapi"\s*:',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "v3/api-docs",
        "Spring v3 OpenAPI /v3/api-docs reachable",
        Severity.LOW,
        r'"openapi"\s*:',
        "OWASP A05:2021",
        "CWE-200",
    ),
    # Generic admin panels (FP-prone — fingerprint by HTML title/form patterns)
    (
        "admin/",
        "Generic /admin/ reachable",
        Severity.HIGH,
        r"<title>[^<]*(admin|dashboard)[^<]*</title>|name=['\"](username|email|password)['\"]",
        "OWASP A07:2021",
        "CWE-285",
    ),
    (
        "administrator/",
        "Joomla-style /administrator/ reachable",
        Severity.HIGH,
        r"Joomla|administrator",
        "OWASP A07:2021",
        "CWE-285",
    ),
    (
        "wp-admin/",
        "WordPress /wp-admin/ reachable",
        Severity.MEDIUM,
        r"WordPress|wp-login",
        "OWASP A07:2021",
        "CWE-285",
    ),
    # PHP debug
    (
        "phpinfo.php",
        "phpinfo() output reachable",
        Severity.MEDIUM,
        r"PHP Version|phpinfo\(\)",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "info.php",
        "PHP info reachable",
        Severity.MEDIUM,
        r"PHP Version|phpinfo\(\)",
        "OWASP A05:2021",
        "CWE-200",
    ),
    # Misc framework debug
    (
        "_debug/",
        "Django _debug toolbar reachable",
        Severity.HIGH,
        r"djDebug|debug-toolbar",
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "debug/vars",
        "Go expvar /debug/vars reachable",
        Severity.MEDIUM,
        r'"cmdline":|"memstats":',
        "OWASP A05:2021",
        "CWE-200",
    ),
    (
        "debug/pprof/",
        "Go pprof /debug/pprof/ reachable (heap/CPU profiles)",
        Severity.HIGH,
        r"/debug/pprof/|profiles:",
        "OWASP A05:2021",
        "CWE-200",
    ),
    # Robots.txt admin disclosure (low — informational)
    (
        "robots.txt",
        "robots.txt discloses admin paths (information leak)",
        Severity.LOW,
        r"^Disallow:\s*/(admin|api/admin|internal|wp-admin|phpmyadmin)",
        "OWASP A05:2021",
        "CWE-200",
    ),
]


def _verify_fingerprint(body_text: str, fingerprint_re: str | None, content_type: str, content_length: int) -> bool:
    """Return True if response body looks like the expected admin/debug page."""
    if fingerprint_re is None:
        # No body fingerprint (binary heap dumps etc.); accept any large 200
        # with non-HTML content-type as a signal
        if content_length > 100_000 and "text/html" not in content_type.lower():
            return True
        return False
    sample = body_text[:4096]
    if re.search(fingerprint_re, sample, re.MULTILINE | re.IGNORECASE):
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe for admin / debug / introspection endpoints")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--paths-file", default=None, help="Custom probe set (one path per line); replaces default")
    parser.add_argument(
        "--include-redirects",
        action="store_true",
        help="Flag 302/303 to login as exposure (panel exists, auth gates it)",
    )
    args = parser.parse_args(argv)

    require_authorization(args.url, args.authorized)

    base = args.url.rstrip("/") + "/"
    sess = make_session(timeout=args.timeout)
    findings: list[Finding] = []

    probe_set = PROBES
    if args.paths_file:
        paths = Path(args.paths_file).read_text().splitlines()
        probe_set = [
            (p.strip(), f"Custom path reachable: {p.strip()}", Severity.MEDIUM, None, "custom", "CWE-200")
            for p in paths
            if p.strip()
        ]

    for path, title, sev, fingerprint, control, cwe in probe_set:
        url = base + path.lstrip("/")
        resp = safe_get(sess, url, timeout=args.timeout, allow_redirects=False)
        if resp is None:
            continue

        is_redirect_to_login = resp.status_code in (301, 302, 303, 307, 308) and re.search(
            r"/(login|sign[-_]in|auth)", resp.headers.get("Location", ""), re.I
        )
        if is_redirect_to_login and args.include_redirects:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"{title} (auth-gated: redirects to login)",
                    severity=Severity.LOW,
                    target=url,
                    detail=(
                        f"GET {url} redirected to {resp.headers.get('Location')!r}. "
                        "The endpoint exists; authentication is in front of it. "
                        "Operationally fine, but discloses framework presence to attackers."
                    ),
                    remediation=(
                        "If the endpoint is not needed in production, disable it "
                        "rather than gating with auth. See references/PLAYBOOK.md."
                    ),
                    cwe_id=cwe,
                    affected_control=control,
                )
            )
            continue

        if resp.status_code != 200:
            continue
        body = resp.text or ""
        ctype = resp.headers.get("Content-Type", "")
        clen = len(resp.content or b"")
        if not _verify_fingerprint(body, fingerprint, ctype, clen):
            continue
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=title,
                severity=sev,
                target=url,
                detail=(
                    f"GET {url} returned 200 with content matching the "
                    f"framework-specific fingerprint for {path!r}. The "
                    "endpoint is publicly reachable."
                ),
                remediation=(
                    f"Take {path!r} behind authentication, restrict by IP allow-list, "
                    "or disable the framework feature entirely if not needed in "
                    "production. See references/PLAYBOOK.md for per-framework snippets."
                ),
                cwe_id=cwe,
                affected_control=control,
                evidence=(("status_code", 200), ("content_length", clen), ("content_type", ctype)),
            )
        )

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, args.url)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
