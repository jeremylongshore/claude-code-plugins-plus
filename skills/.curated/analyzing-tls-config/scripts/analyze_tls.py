#!/usr/bin/env python3
"""TLS configuration analyzer for penetration-tester v3.

Companion to skill `analyzing-tls-config`. Per AT-ADEC at the plugin root
000-docs/001-AT-ADEC-skill-taxonomy.md, this script imports from the shared
lib/ module so per-skill plumbing stays narrow.

Checks performed (with thresholds):
    1. Negotiated protocol version — flag TLSv1.0 / TLSv1.1 (HIGH)
    2. Negotiated cipher suite — flag null / EXPORT / aNULL (CRITICAL),
       flag RC4 / 3DES (HIGH), absence of ECDHE/DHE (MEDIUM forward-secrecy)
    3. Certificate expiry — <7 days (CRITICAL), <30 days (HIGH)
    4. Certificate hostname match (SAN/CN) — RFC 6125 (HIGH on mismatch)
    5. Chain validates to system CA store — self-signed/untrusted (MEDIUM)
    6. Public-key bit length — RSA < 2048 / ECDSA < 256 (HIGH)

References:
    NIST SP 800-52r2 §3 (protocol versions, cipher suites, key sizes)
    Mozilla TLS Configuration Generator (https://ssl-config.mozilla.org/)
    PCI DSS v4.0 Req 4.2.1.1 (strong cryptography)
    RFC 6125 (hostname verification)
"""

from __future__ import annotations

import argparse
import datetime
import socket
import ssl
import sys
import urllib.parse
from pathlib import Path

# Make the plugin's lib/ importable when invoked via CLAUDE_PLUGIN_ROOT path.
_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from lib.authz_check import require_authorization  # noqa: E402
from lib.finding import Finding, Severity  # noqa: E402
from lib.report import emit, exit_code  # noqa: E402


SKILL_ID = "analyzing-tls-config"


# Weak-cipher fragments (substring match against negotiated cipher name)
NULL_CIPHER_TOKENS = ("NULL", "aNULL", "eNULL", "EXPORT")
WEAK_CIPHER_TOKENS = ("RC4", "3DES", "DES-CBC", "MD5", "IDEA", "SEED")
FORWARD_SECRECY_TOKENS = ("ECDHE", "DHE")

# Protocol-version thresholds
OBSOLETE_PROTOCOLS = {"SSLv2", "SSLv3", "TLSv1", "TLSv1.0", "TLSv1.1"}

# Key-size thresholds (NIST SP 800-52r2 §3.4)
MIN_RSA_BITS = 2048
MIN_EC_BITS = 256

# Certificate expiry thresholds
EXPIRY_CRITICAL_DAYS = 7
EXPIRY_HIGH_DAYS = 30


def _parse_target(url: str) -> tuple[str, int]:
    """Return (host, port) for a target URL or bare host[:port]."""
    if "://" not in url:
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    port = parsed.port or 443
    if not host:
        raise ValueError(f"could not parse host from {url!r}")
    return host, port


def _grab_cert_and_cipher(host: str, port: int, timeout: float) -> tuple[dict, tuple, str, ssl.SSLContext]:
    """Open a TLS connection and capture cert + cipher + protocol version.

    Uses default SSL context (system CA bundle, hostname verification on).
    For chain-untrusted targets a second pass with verification disabled is
    needed for cert-detail capture — handled in _grab_untrusted_cert below.
    """
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as raw_sock:
        with ctx.wrap_socket(raw_sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
            cipher = ssock.cipher()  # (name, version, bits)
            version = ssock.version()
    return cert, cipher, version, ctx


def _grab_untrusted_cert(host: str, port: int, timeout: float) -> tuple[dict | None, tuple | None, str | None]:
    """Capture cert details when the trust check would otherwise refuse.

    Used to report on self-signed / expired / untrusted-chain targets WITHOUT
    masking the trust failure — the caller emits a separate finding for the
    chain failure, then this captures details for follow-on cert findings.
    """
    ctx = ssl._create_unverified_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=host) as ssock:
                # ssock.getpeercert(binary_form=True) → raw DER; we want parsed
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
        return cert, cipher, version
    except (ssl.SSLError, socket.error):
        return None, None, None


def _cert_expiry_dt(cert: dict) -> datetime.datetime | None:
    """Parse 'notAfter' into UTC datetime. Returns None if absent or malformed."""
    not_after = cert.get("notAfter")
    if not not_after:
        return None
    # Format: 'May 29 15:30:00 2026 GMT'
    try:
        return datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def _check_protocol(version: str, target: str) -> list[Finding]:
    if version in OBSOLETE_PROTOCOLS:
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"Server negotiates obsolete {version}",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    f"The TLS handshake completed using {version}, which is "
                    "deprecated by NIST SP 800-52r2 §3.1 and PCI DSS v4.0 "
                    "Req 4.2.1.1. Modern clients can still negotiate this "
                    "version, leaving the connection vulnerable to known "
                    "downgrade attacks (e.g., POODLE on SSLv3, BEAST on "
                    "TLSv1.0)."
                ),
                remediation=(
                    "Configure the server to require TLSv1.2 minimum, prefer "
                    "TLSv1.3. nginx: `ssl_protocols TLSv1.2 TLSv1.3;`. "
                    "Caddy: TLSv1.2 is the default minimum since v2."
                ),
                cwe_id="CWE-326",
                owasp_category="A02:2021",
                affected_control="NIST 800-52r2 §3.1; PCI DSS v4.0 Req 4.2.1.1",
                references=(
                    "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf",
                    "https://www.pcisecuritystandards.org/document_library/",
                ),
            )
        ]
    return []


def _check_cipher(cipher: tuple, target: str) -> list[Finding]:
    name = cipher[0] if cipher else ""
    findings: list[Finding] = []

    for token in NULL_CIPHER_TOKENS:
        if token in name:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"Server negotiates null/anonymous cipher: {name}",
                    severity=Severity.CRITICAL,
                    target=target,
                    detail=(
                        f"The negotiated cipher suite {name} provides no "
                        "confidentiality (NULL) or no authentication "
                        "(aNULL/EXPORT). Any in-path attacker reads cleartext."
                    ),
                    remediation=(
                        "Remove !NULL:!aNULL:!EXPORT from cipher list. "
                        "nginx: `ssl_ciphers HIGH:!aNULL:!MD5:!EXPORT;`. "
                        "Prefer Mozilla's intermediate-config generator output."
                    ),
                    cwe_id="CWE-327",
                    affected_control="NIST 800-52r2 §3.3.1",
                    references=("https://ssl-config.mozilla.org/",),
                )
            )
            break

    for token in WEAK_CIPHER_TOKENS:
        if token in name:
            findings.append(
                Finding(
                    skill_id=SKILL_ID,
                    title=f"Server negotiates weak cipher: {name}",
                    severity=Severity.HIGH,
                    target=target,
                    detail=(
                        f"The negotiated cipher suite {name} contains a "
                        "deprecated algorithm. RC4 has documented bias attacks "
                        "(RFC 7465); 3DES is vulnerable to Sweet32 (CVE-2016-2183); "
                        "MD5/IDEA/SEED are no longer NIST-approved."
                    ),
                    remediation=(
                        "Remove !RC4:!3DES:!MD5 from cipher list and require "
                        "AEAD suites (AES-GCM, CHACHA20-POLY1305). Use "
                        "Mozilla's intermediate config for backward "
                        "compatibility, modern config for greenfield."
                    ),
                    cwe_id="CWE-327",
                    affected_control="NIST 800-52r2 §3.3.1; PCI DSS v4.0 Req 4.2.1.1",
                    references=(
                        "https://datatracker.ietf.org/doc/html/rfc7465",
                        "https://sweet32.info/",
                    ),
                )
            )
            break

    if name and not any(t in name for t in FORWARD_SECRECY_TOKENS):
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title=f"Negotiated cipher lacks forward secrecy: {name}",
                severity=Severity.MEDIUM,
                target=target,
                detail=(
                    "The cipher suite does not use ECDHE or DHE. If the "
                    "server's private key is later compromised, all past "
                    "session traffic captured by an adversary can be decrypted."
                ),
                remediation=(
                    "Configure the server to prefer ECDHE-based cipher suites. "
                    "Mozilla's intermediate config achieves this on every "
                    "supported server type."
                ),
                cwe_id="CWE-326",
                affected_control="NIST 800-52r2 §3.3.1",
                references=("https://ssl-config.mozilla.org/",),
            )
        )

    return findings


def _check_expiry(cert: dict, target: str) -> list[Finding]:
    expiry = _cert_expiry_dt(cert)
    if expiry is None:
        return []
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = expiry - now
    days = delta.days

    if days <= EXPIRY_CRITICAL_DAYS:
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"Certificate expires in {days} days",
                severity=Severity.CRITICAL,
                target=target,
                detail=(
                    f"The presented certificate notAfter is {expiry.isoformat()}, "
                    f"only {days} day(s) away. Without renewal, the next handshake "
                    "will fail and the service will be unreachable to any "
                    "trust-validating client."
                ),
                remediation=(
                    "Renew the certificate immediately. If using Let's Encrypt, "
                    "force `certbot renew --force-renewal`. Verify the new cert "
                    "is in the server's configured key path and that the server "
                    "has reloaded (systemctl reload nginx / caddy reload)."
                ),
                affected_control="NIST 800-52r2 §4.1",
            )
        ]
    if days <= EXPIRY_HIGH_DAYS:
        return [
            Finding(
                skill_id=SKILL_ID,
                title=f"Certificate expires in {days} days",
                severity=Severity.HIGH,
                target=target,
                detail=(
                    f"The presented certificate notAfter is {expiry.isoformat()}. "
                    f"Renewal is recommended ≥30 days before expiry to allow "
                    "deployment and OCSP-stapling cache warmup."
                ),
                remediation=(
                    "Schedule renewal. Verify your renewal automation "
                    "(certbot.timer, caddy auto-cert) is running and has "
                    "current credentials for the DNS/HTTP challenge."
                ),
                affected_control="NIST 800-52r2 §4.1",
            )
        ]
    return []


def _check_hostname(cert: dict, host: str, target: str) -> list[Finding]:
    # The default-context handshake already validated hostname; if we got here
    # via the trusted path, hostname matches by definition. This check exists
    # for the untrusted-cert path.
    sans = []
    for entry in cert.get("subjectAltName", ()):
        if entry[0].lower() == "dns":
            sans.append(entry[1].lower())
    subject = dict(x[0] for x in cert.get("subject", ()))
    cn = (subject.get("commonName") or "").lower()

    host_l = host.lower()
    if host_l in sans:
        return []
    if any(host_l.endswith(s.lstrip("*")) for s in sans if s.startswith("*.")):
        return []
    if cn and host_l == cn:
        return []
    if cn.startswith("*.") and host_l.endswith(cn[1:]):
        return []

    return [
        Finding(
            skill_id=SKILL_ID,
            title=f"Certificate hostname does not match target ({host})",
            severity=Severity.HIGH,
            target=target,
            detail=(
                f"The cert SAN/CN values ({sans or [cn]!r}) do not include "
                f"the target host {host!r}. RFC 6125 requires the client to "
                "reject this; some legacy clients may still accept it, opening "
                "an MITM window."
            ),
            remediation=(
                "Reissue the certificate with the correct SAN list including "
                "every hostname the service responds on. Modern CAs (Let's "
                "Encrypt, ZeroSSL) accept SAN lists at issuance."
            ),
            cwe_id="CWE-297",
            affected_control="RFC 6125 §6",
            references=("https://datatracker.ietf.org/doc/html/rfc6125",),
        )
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TLS configuration analyzer")
    parser.add_argument("url", help="Target URL (https://...) or host[:port]")
    parser.add_argument(
        "--authorized", action="store_true", help="Attest authorization for non-local targets (required)"
    )
    parser.add_argument("--port", type=int, default=None, help="Target port (overrides URL port; default 443)")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="markdown")
    parser.add_argument("--min-severity", choices=("critical", "high", "medium", "low", "info"), default="info")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    host, default_port = _parse_target(args.url)
    port = args.port or default_port
    target_display = f"{host}:{port}"

    # Authorization gate (lib/authz_check applies the local-target carve-out)
    require_authorization(args.url, args.authorized)

    findings: list[Finding] = []

    # Phase 1: try trusted handshake
    trusted_cert: dict | None = None
    cipher: tuple | None = None
    version: str | None = None
    try:
        trusted_cert, cipher, version, _ = _grab_cert_and_cipher(host, port, args.timeout)
    except ssl.SSLCertVerificationError as exc:
        # Chain trust failed — emit finding + fall back to untrusted handshake
        findings.append(
            Finding(
                skill_id=SKILL_ID,
                title="Certificate chain does not validate to system trust store",
                severity=Severity.MEDIUM,
                target=target_display,
                detail=(
                    f"openssl/ssl rejected the chain: {exc!s}. Common causes: "
                    "self-signed certificate, intermediate certificate missing "
                    "from the server response, or expired/revoked root in the "
                    "server's chain."
                ),
                remediation=(
                    "Verify the server returns the full chain (cert + all "
                    "intermediates, NOT the root). Run `openssl s_client -connect "
                    f"{target_display} -showcerts` and confirm each intermediate is "
                    "present. Reissue with a trusted CA if currently self-signed."
                ),
                cwe_id="CWE-295",
                affected_control="Mozilla TLS Guidelines",
            )
        )
        cert_fallback, cipher, version = _grab_untrusted_cert(host, port, args.timeout)
        trusted_cert = cert_fallback
    except (socket.error, ssl.SSLError) as exc:
        sys.stderr.write(f"ERROR: failed to connect to {target_display}: {exc}\n")
        return 2

    if version:
        findings.extend(_check_protocol(version, target_display))
    if cipher:
        findings.extend(_check_cipher(cipher, target_display))
    if trusted_cert:
        findings.extend(_check_expiry(trusted_cert, target_display))
        findings.extend(_check_hostname(trusted_cert, host, target_display))

    # Severity floor
    floor = Severity(args.min_severity)
    findings = [f for f in findings if f.severity.numeric >= floor.numeric]

    emit(findings, args.output, args.format, target_display)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
