"""Shared HTTP client setup for penetration-tester v3 active-scan skills.

Per AT-ADEC at 000-docs/001-AT-ADEC-skill-taxonomy.md, every skill that issues
HTTP requests against a target uses this module so timeouts, user-agent, and
redirect handling are consistent across the pack.

Design notes:
    - Uses `requests` because it's already a v2 dependency. Skills that need
      raw socket access (e.g. analyzing-tls-config) drop down to `ssl` +
      `socket` directly; this module covers the HTTP-level common case.
    - User-Agent is identifiable. We do NOT cloak as a browser — pentesters
      should be detectable to the target's IDS by design, and operators
      reading their access logs should be able to identify scan traffic.
    - No retry. A finding "endpoint times out" is itself a signal; auto-retry
      would mask transient unavailability.
    - No SSL verification override. If a skill needs to scan a cert that
      doesn't validate (e.g., expired or self-signed), it drops to raw `ssl`
      and reports the cert details rather than disabling verification globally.
"""

from __future__ import annotations

from typing import Any

import requests


USER_AGENT = "penetration-tester/3.0 (+https://github.com/jeremylongshore/claude-code-plugins)"


def make_session(timeout: float = 10.0, max_redirects: int = 5) -> requests.Session:
    """Build a Session pre-configured for pentest use.

    Args:
        timeout: per-request timeout in seconds. 10s default matches v2.
        max_redirects: follow this many 3xx redirects before treating as a finding.
            v2 silently followed unlimited redirects which masked redirect-loop
            misconfigurations.

    Returns:
        Configured Session. Caller still passes timeout per-request because
        Session doesn't have a default-timeout attribute — wrap with the
        `get`/`head`/`options` helpers below for that.
    """
    sess = requests.Session()
    sess.headers["User-Agent"] = USER_AGENT
    sess.max_redirects = max_redirects
    return sess


def safe_get(sess: requests.Session, url: str, timeout: float = 10.0, **kwargs: Any) -> requests.Response | None:
    """GET with timeout + connection-error capture.

    Returns None on connection error / DNS failure / timeout. Caller can
    decide whether the absence is itself a finding (e.g. "endpoint unreachable")
    or should be silently treated as "skip this check".
    """
    try:
        return sess.get(url, timeout=timeout, **kwargs)
    except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects):
        return None


def safe_head(sess: requests.Session, url: str, timeout: float = 10.0, **kwargs: Any) -> requests.Response | None:
    """HEAD with timeout + connection-error capture."""
    try:
        return sess.head(url, timeout=timeout, allow_redirects=True, **kwargs)
    except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects):
        return None


def safe_options(sess: requests.Session, url: str, timeout: float = 10.0, **kwargs: Any) -> requests.Response | None:
    """OPTIONS with timeout + connection-error capture.

    Used by probing-dangerous-http-methods skill to detect allowed-methods
    disclosure (Allow header) and CORS preflight behavior.
    """
    try:
        return sess.options(url, timeout=timeout, **kwargs)
    except (requests.ConnectionError, requests.Timeout, requests.TooManyRedirects):
        return None
