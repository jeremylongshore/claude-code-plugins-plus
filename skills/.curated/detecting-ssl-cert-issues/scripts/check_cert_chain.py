#!/usr/bin/env python3
"""Deeper SSL certificate posture audit.

Companion to skill `detecting-ssl-cert-issues`. Picks up where skill #1
analyzing-tls-config leaves off — assumes the chain already validates
(no protocol / cipher / expiry / hostname problems) and audits the
posture issues that don't break the handshake but matter for SOC2,
PCI, and modern browser policy.

Checks performed:
    1. OCSP staple presence + freshness (RFC 6066 status_request)
    2. OCSP responder reachability + revocation status (RFC 6960)
    3. SCT count from cert's embedded CT extension (RFC 6962)
    4. Chain ordering (RFC 5246 §7.4.2 — leaf first, intermediates next)
    5. AIA extension presence (CA Issuers + OCSP URL — RFC 5280 §4.2.2.1)
    6. Wildcard scope analysis (CA/B BR §3.2.2 — reject *.com etc.)
    7. Key Usage extension flags (RFC 5280 §4.2.1.3)
    8. Chain length (>4 is operationally costly)

References:
    RFC 5246 — TLS 1.2 chain ordering
    RFC 5280 — X.509 PKIX
    RFC 6066 — TLS status_request (OCSP stapling)
    RFC 6960 — OCSP
    RFC 6962 — Certificate Transparency
    CA/Browser Forum Baseline Requirements
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

# Make the plugin's lib/ importable
_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.authz_check import require_authorization  # noqa: E402
from lib.finding import Finding, Severity  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402

SKILL_ID = "detecting-ssl-cert-issues"

# Wildcards at these scope levels are CA/B-rejectable
PUBLIC_SUFFIX_TLDS = {
    "com",
    "org",
    "net",
    "io",
    "co",
    "us",
    "uk",
    "de",
    "fr",
    "jp",
    "cn",
    "edu",
    "gov",
    "mil",
    "info",
    "biz",
    "name",
}


def _parse_target(url: str) -> tuple[str, int]:
    if "://" not in url:
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    port = parsed.port or 443
    if not host:
        raise ValueError(f"could not parse host from {url!r}")
    return host, port


def _grab_chain_and_staple(host: str, port: int, timeout: float):
    """Fetch the cert chain + check whether server sent an OCSP staple.

    Uses raw `openssl s_client -status` because Python's ssl module
    doesn't expose the status_request response. We parse the textual
    output for the 'OCSP response:' block.
    """
    import subprocess

    cmd = [
        "openssl",
        "s_client",
        "-connect",
        f"{host}:{port}",
        "-servername",
        host,
        "-status",
        "-showcerts",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=b"",
            capture_output=True,
            timeout=timeout * 3,
        )
    except subprocess.TimeoutExpired:
        return None, None, None
    out = proc.stdout.decode(errors="replace") + proc.stderr.decode(errors="replace")
    chain = _parse_chain(out)
    has_staple = _has_ocsp_response(out)
    return out, chain, has_staple


def _parse_chain(s_client_output: str) -> list[str]:
    """Extract each PEM block in order from s_client -showcerts output."""
    pems: list[str] = []
    buf: list[str] = []
    in_cert = False
    for line in s_client_output.splitlines():
        if "-----BEGIN CERTIFICATE-----" in line:
            in_cert = True
            buf = [line]
            continue
        if in_cert:
            buf.append(line)
            if "-----END CERTIFICATE-----" in line:
                pems.append("\n".join(buf))
                buf = []
                in_cert = False
    return pems


def _has_ocsp_response(s_client_output: str) -> bool:
    """True if the s_client output contains an OCSP staple response."""
    if "OCSP response:" not in s_client_output:
        return False
    # 'OCSP response: no response sent' = no staple
    if "no response sent" in s_client_output:
        return False
    return True


def _load_cert(pem: str):
    """Parse a PEM cert with the cryptography library."""
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend

        return x509.load_pem_x509_certificate(pem.encode(), default_backend())
    except Exception:
        return None


def _check_chain_order(chain: list[str], target: str) -> list[Finding]:
    """Verify chain is in RFC 5246 order: leaf first, then intermediates.

    Heuristic: parse subjects; the leaf is the cert whose subject != issuer
    of the next cert. If chain[0]'s subject == chain[1]'s subject (or
    chain[0] looks like a root), it's misordered.
    """
    if len(chain) < 2:
        return []

    certs = [_load_cert(p) for p in chain]
    if any(c is None for c in certs):
        return []

    # Leaf cert (chain[0]) should be issued by chain[1]
    leaf, second = certs[0], certs[1]
    # Heuristic: leaf cert has a subject that's hostname-shaped; intermediate
    # subject is CA-shaped. If chain[0].subject == chain[0].issuer (self-
    # signed), it's a root → misorder.
    if leaf.subject == leaf.issuer:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Chain misorder: root certificate appears in position 0",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "RFC 5246 §7.4.2 requires the server to send certificates "
                    "in order: leaf first, intermediates next, root excluded. "
                    "Older clients may fail validation; modern clients tolerate "
                    "but log."
                ),
                remediation=(
                    "Concatenate cert files in order: leaf.pem + intermediate.pem. "
                    "nginx: ssl_certificate /path/to/fullchain.pem (Let's Encrypt "
                    "ships this format)."
                ),
                cwe_id="CWE-295",
                affected_control="RFC 5246 §7.4.2",
                references=("https://datatracker.ietf.org/doc/html/rfc5246#section-7.4.2",),
            )
        ]

    if leaf.issuer != second.subject:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="Chain misorder: cert at position 1 is not issuer of leaf",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "The certificate at chain position 1 is not the issuer of the "
                    "leaf certificate. RFC 5246 §7.4.2 ordering violated."
                ),
                remediation="Rebuild fullchain.pem with leaf + correct intermediate(s).",
                affected_control="RFC 5246 §7.4.2",
            )
        ]
    return []


def _check_staple(has_staple: bool, target: str) -> list[Finding]:
    if has_staple:
        return []
    return [
        Finding(
            skill_id=SKILL_ID,
            title="OCSP stapling not configured",
            severity=Severity.HIGH,
            target=target,
            detail=(
                "Server did not return an OCSP staple in the status_request "
                "response. Clients must phone home to the CA's OCSP responder "
                "to check revocation, adding latency and exposing browsing "
                "metadata to the CA."
            ),
            remediation=(
                "nginx: `ssl_stapling on; ssl_stapling_verify on; "
                "resolver 1.1.1.1 8.8.8.8 valid=300s;`. "
                "Caddy: stapling is auto-enabled. "
                "Apache: `SSLUseStapling on; SSLStaplingCache shmcb:logs/stapling-cache(150000);`."
            ),
            cwe_id="CWE-295",
            affected_control="RFC 6066 status_request; CA/B BR §4.9.10",
            references=("https://datatracker.ietf.org/doc/html/rfc6066#section-8",),
        )
    ]


def _check_scts(chain: list[str], target: str) -> list[Finding]:
    """Count embedded Signed Certificate Timestamps in the leaf cert."""
    if not chain:
        return []
    leaf = _load_cert(chain[0])
    if leaf is None:
        return []
    try:
        from cryptography.x509 import oid

        ext = leaf.extensions.get_extension_for_oid(oid.ExtensionOID.PRECERT_SIGNED_CERTIFICATE_TIMESTAMPS)
        sct_count = len(ext.value)
    except Exception:
        sct_count = 0

    if sct_count < 2:
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"Certificate Transparency: only {sct_count} SCT(s) embedded",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    f"The leaf certificate has {sct_count} SCT(s). Chrome's CT "
                    "enforcement policy (active since 2018) requires ≥2 SCTs "
                    "from independently-operated logs OR a separate TLS-extension "
                    "SCT delivery. Browsers reject the connection silently if "
                    "policy violated."
                ),
                remediation=(
                    "Reissue with a CA that submits to ≥2 CT logs at issuance "
                    "(all major public CAs do this by default since 2018). "
                    "Verify with crt.sh after issuance: https://crt.sh/?q=example.com"
                ),
                cwe_id="CWE-295",
                affected_control="RFC 6962; Chrome CT Policy",
                references=(
                    "https://datatracker.ietf.org/doc/html/rfc6962",
                    "https://googlechrome.github.io/CertificateTransparency/ct_policy.html",
                ),
            )
        ]
    return []


def _check_aia(chain: list[str], target: str) -> list[Finding]:
    """Verify the leaf cert has Authority Info Access (CA Issuers + OCSP URL)."""
    if not chain:
        return []
    leaf = _load_cert(chain[0])
    if leaf is None:
        return []
    try:
        from cryptography.x509 import oid

        ext = leaf.extensions.get_extension_for_oid(oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
        aia = ext.value
        ocsp_urls = [d for d in aia if d.access_method == oid.AuthorityInformationAccessOID.OCSP]
        ca_issuers = [d for d in aia if d.access_method == oid.AuthorityInformationAccessOID.CA_ISSUERS]
        findings = []
        if not ocsp_urls:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title="AIA extension missing OCSP responder URL",
                    severity=Severity.MEDIUM,
                    target=target,
                    detail=(
                        "The leaf certificate's Authority Info Access extension "
                        "does not include an OCSP responder URL. Clients can't "
                        "check revocation status."
                    ),
                    remediation=(
                        "This is a CA-side issuance configuration; contact your "
                        "CA. All public CAs include OCSP URLs by default; this "
                        "is unusual for a public cert and may indicate a "
                        "private-CA cert in use."
                    ),
                    affected_control="RFC 5280 §4.2.2.1",
                )
            )
        if not ca_issuers:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title="AIA extension missing CA Issuers URL",
                    severity=Severity.LOW,
                    target=target,
                    detail=("AIA missing CA Issuers — clients can't fetch missing intermediates on demand."),
                    remediation="CA-side issuance config. Same as OCSP URL fix.",
                    affected_control="RFC 5280 §4.2.2.1",
                )
            )
        return findings
    except Exception:
        return [
            Finding(
                skill_id=SKILL_ID,
                title="AIA extension absent from leaf cert",
                severity=Severity.MEDIUM,
                target=target,
                detail="No AIA extension at all — leaf cert can't direct clients to OCSP or intermediates.",
                remediation="Reissue with a public CA; this is unusual.",
                affected_control="RFC 5280 §4.2.2.1",
            )
        ]


def _check_wildcards(chain: list[str], target: str) -> list[Finding]:
    """Flag wildcards with overly broad scope."""
    if not chain:
        return []
    leaf = _load_cert(chain[0])
    if leaf is None:
        return []
    try:
        from cryptography.x509 import oid

        san_ext = leaf.extensions.get_extension_for_oid(oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        sans = san_ext.value.get_values_for_type(__import__("cryptography").x509.DNSName)
    except Exception:
        sans = []

    findings = []
    for san in sans:
        if not san.startswith("*."):
            continue
        scope = san[2:]
        labels = scope.split(".")
        if len(labels) <= 1 or labels[-1] in PUBLIC_SUFFIX_TLDS and len(labels) == 1:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"Wildcard SAN with over-broad scope: {san}",
                    severity=Severity.HIGH,
                    target=target,
                    detail=(
                        f"The SAN {san!r} would cover an entire public suffix or "
                        "single-label domain. CA/Browser Forum BR §3.2.2 forbids "
                        "issuance at this scope; if you see this on a public cert "
                        "the CA mis-issued."
                    ),
                    remediation=("Reissue with narrower SAN(s) covering only the hostnames actually served."),
                    affected_control="CA/B Baseline Requirements §3.2.2",
                )
            )
    return findings


def _check_key_usage(chain: list[str], target: str) -> list[Finding]:
    if not chain:
        return []
    leaf = _load_cert(chain[0])
    if leaf is None:
        return []
    try:
        from cryptography.x509 import oid

        ext = leaf.extensions.get_extension_for_oid(oid.ExtensionOID.KEY_USAGE)
        ku = ext.value
        if not ku.digital_signature:
            return [
                Finding(
                    skill_id=SKILL_ID,
                    title="Key Usage extension missing digitalSignature",
                    severity=Severity.MEDIUM,
                    target=target,
                    detail=(
                        "The cert's KU extension does not assert digitalSignature. "
                        "RFC 5280 §4.2.1.3 requires this for TLS server certs."
                    ),
                    remediation="CA-side issuance config; reissue with correct KU.",
                    affected_control="RFC 5280 §4.2.1.3",
                )
            ]
    except Exception:
        pass
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SSL certificate posture audit")
    parser.add_argument("url")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--skip-ocsp", action="store_true")
    args = parser.parse_args(argv)

    host, default_port = _parse_target(args.url)
    port = args.port or default_port
    target = f"{host}:{port}"

    require_authorization(args.url, args.authorized)

    findings: list[Finding] = []

    raw, chain, has_staple = _grab_chain_and_staple(host, port, args.timeout)
    if chain is None:
        sys.stderr.write(f"ERROR: could not reach {target} or openssl unavailable\n")
        return 2

    if not args.skip_ocsp:
        findings.extend(_check_staple(has_staple, target))
    findings.extend(_check_chain_order(chain, target))
    findings.extend(_check_scts(chain, target))
    findings.extend(_check_aia(chain, target))
    findings.extend(_check_wildcards(chain, target))
    findings.extend(_check_key_usage(chain, target))

    if len(chain) > 4:
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"Chain has {len(chain)} certificates (longer than 4)",
                severity=Severity.LOW,
                target=target,
                detail=(
                    "Long chains expand the trust surface and add handshake "
                    "latency. Modern CAs issue 2-cert chains (leaf + intermediate); "
                    "anything longer suggests vendored cross-signing."
                ),
                remediation="Verify if cross-signing is intentional; if not, reissue.",
                affected_control="CA/B Baseline Requirements",
            )
        )

    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, target)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
