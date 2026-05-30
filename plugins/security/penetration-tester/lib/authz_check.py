"""Authorization gate for active-scan skills.

Per AT-ADEC 685 scope decision: every penetration-tester v3 skill that issues
network requests against a target the user does NOT obviously own (i.e., not
localhost / 127.0.0.1 / RFC1918 / the user's own GitHub-resolved repo path)
MUST gate behind explicit attestation before running the scan.

The attestation pattern is a two-step gate:

  1. The skill's SKILL.md instructs Claude to ask the user verbatim:
     "Do you have authorization to perform security testing on this target?
      I need confirmation before proceeding."

  2. The skill's script accepts --authorized as a required flag for
     non-local targets. The flag MUST be set explicitly; there is no env-var
     fallback (which would let CI silently scan anything).

This module exposes the helper that distinguishes "obviously local / owned"
from "everything else" so each skill can apply the gate consistently.

References:
    - OWASP WSTG v4.2 § 2.1 "Set the scope, define rules of engagement"
    - Penetration Testing Execution Standard (PTES) § Pre-engagement Interactions
    - NIST SP 800-115 § 5.1 "Planning"
"""

from __future__ import annotations

import ipaddress
import sys
import urllib.parse


_RFC1918_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]
_LOOPBACK_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
]


def is_obviously_local(target: str) -> bool:
    """True if target is a loopback / link-local / RFC1918 URL or path.

    Used to short-circuit the authz gate for targets the user obviously owns.
    Errs on the side of REQUIRING attestation: any ambiguity → False → gate
    fires.
    """
    parsed = urllib.parse.urlparse(target)
    host = parsed.hostname

    if not host:
        # Treat empty / unparseable as non-local — force the gate.
        return False

    if host in ("localhost", "localhost.localdomain"):
        return True

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Hostname — not an IP. Not provably local.
        return False

    if any(ip in net for net in _LOOPBACK_NETS):
        return True
    if any(ip in net for net in _RFC1918_NETS):
        return True
    if ip.is_link_local:
        return True
    return False


def require_authorization(target: str, authorized_flag: bool) -> None:
    """Gate active-scan skills. Exits with error if attestation missing.

    Args:
        target: the URL or IP about to be scanned
        authorized_flag: True if the caller passed --authorized

    Raises SystemExit(2) if attestation required and missing. Exit code 2
    distinguishes from generic error (1) — operators can grep for it in CI logs.
    """
    if is_obviously_local(target):
        return  # No gate needed for loopback / RFC1918

    if authorized_flag:
        return

    sys.stderr.write(
        "ERROR: target appears to be non-local (%s).\n"
        "       Active scanning requires explicit authorization attestation.\n"
        "       Re-run with --authorized after confirming with the target owner\n"
        "       that you have written permission to test.\n"
        "       See references/AUTHORIZATION.md for the attestation pattern.\n" % target
    )
    raise SystemExit(2)
