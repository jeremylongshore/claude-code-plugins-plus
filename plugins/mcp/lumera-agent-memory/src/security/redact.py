"""
Redaction module with fail-closed for critical patterns, redact-and-continue for non-critical.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Tuple


@dataclass
class RedactionRule:
    """A single redaction rule."""
    rule_name: str
    pattern: re.Pattern
    critical: bool  # If True, fail-closed; if False, redact and continue
    count: int = 0


@dataclass
class RedactionReport:
    """Report of redactions performed."""
    rules_fired: list[RedactionRule] = field(default_factory=list)
    critical_detected: bool = False

    def to_dict(self) -> dict:
        return {
            "rules_fired": [
                {"rule": r.rule_name, "count": r.count, "critical": r.critical}
                for r in self.rules_fired
            ],
            "critical_detected": self.critical_detected
        }


# Redaction rules: critical patterns MUST fail-closed
REDACTION_RULES = [
    # CRITICAL: Fail-closed patterns
    RedactionRule(
        "aws_secret_key",
        re.compile(r'aws_secret_access_key["\s:=\\]+([A-Za-z0-9/+=]{40})', re.IGNORECASE),
        critical=True
    ),
    RedactionRule(
        "private_key",
        re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', re.IGNORECASE),
        critical=True
    ),
    RedactionRule(
        "auth_header_raw",
        re.compile(r'Authorization:\s*(Bearer|Basic)\s+[A-Za-z0-9+/=._-]{20,}', re.IGNORECASE),
        critical=True
    ),
    RedactionRule(
        "database_password",
        re.compile(r'(password|passwd|pwd)["\s:=]+(["\'][^"\']{8,}["\']|[A-Za-z0-9!@#$%^&*]{8,})\s*(;|,|$)', re.IGNORECASE),
        critical=True
    ),

    # NON-CRITICAL: Redact and continue
    RedactionRule(
        "aws_access_key",
        re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),
        critical=False
    ),
    RedactionRule(
        "email",
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        critical=False
    ),
    RedactionRule(
        "phone",
        re.compile(r'\b\d{3}[-.]?\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        critical=False
    ),
    RedactionRule(
        "api_token_looking",
        re.compile(r'\b[A-Za-z0-9_-]{32,}\b'),  # Generic long tokens
        critical=False
    ),
    RedactionRule(
        "ipv4",
        re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        critical=False
    ),
]


def redact_session(session_data: dict) -> Tuple[dict, RedactionReport]:
    """
    Redact PII and secrets from session data.

    - Critical patterns: Fail immediately if detected
    - Non-critical patterns: Redact and continue

    Returns: (redacted_data, report)
    """
    # Convert to JSON string for pattern matching
    import json
    session_json = json.dumps(session_data, indent=2)

    report = RedactionReport()
    redacted_json = session_json

    # Check all rules
    for rule in REDACTION_RULES:
        matches = list(rule.pattern.finditer(redacted_json))

        if matches:
            rule.count = len(matches)
            report.rules_fired.append(rule)

            if rule.critical:
                # Fail-closed for critical patterns
                report.critical_detected = True
                raise ValueError(
                    f"CRITICAL: Detected {rule.rule_name} pattern in session data. "
                    f"Cannot safely store to Cascade. Found {len(matches)} occurrence(s). "
                    f"Remove sensitive data from source CASS session before storing."
                )
            else:
                # Redact non-critical patterns
                redacted_json = rule.pattern.sub(f"[REDACTED:{rule.rule_name.upper()}]", redacted_json)

    # Convert back to dict
    redacted_data = json.loads(redacted_json)

    return redacted_data, report
