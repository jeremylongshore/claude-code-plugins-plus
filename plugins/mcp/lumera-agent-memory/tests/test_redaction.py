"""
Test redaction behavior: critical vs non-critical patterns.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from security.redact import redact_session


def test_redact_non_critical_email():
    """Non-critical: Email should be redacted and continue."""
    session = {
        "messages": [
            {"role": "user", "content": "Contact me at john@example.com"}
        ]
    }

    redacted, report = redact_session(session)

    # Should succeed and redact
    assert "[REDACTED:EMAIL]" in str(redacted)
    assert len(report.rules_fired) == 1
    assert report.rules_fired[0].rule_name == "email"
    assert not report.critical_detected


def test_redact_non_critical_phone():
    """Non-critical: Phone should be redacted and continue."""
    session = {
        "messages": [
            {"role": "user", "content": "Call me at 555-123-4567"}
        ]
    }

    redacted, report = redact_session(session)

    assert "[REDACTED:PHONE]" in str(redacted)
    assert len(report.rules_fired) == 1
    assert not report.critical_detected


def test_redact_non_critical_aws_access_key():
    """Non-critical: AWS access key should be redacted and continue."""
    session = {
        "messages": [
            {"role": "user", "content": "My key is AKIAIOSFODNN7EXAMPLE"}
        ]
    }

    redacted, report = redact_session(session)

    assert "[REDACTED:AWS_ACCESS_KEY]" in str(redacted)
    assert "AKIAIOSFODNN7EXAMPLE" not in str(redacted)
    assert not report.critical_detected


def test_fail_closed_on_private_key():
    """CRITICAL: Private key must fail-closed."""
    session = {
        "messages": [
            {"role": "user", "content": "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."}
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        redact_session(session)

    assert "CRITICAL" in str(exc_info.value)
    assert "private_key" in str(exc_info.value).lower()


def test_fail_closed_on_aws_secret_key():
    """CRITICAL: AWS secret key must fail-closed."""
    session = {
        "messages": [
            {"role": "user", "content": 'aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'}
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        redact_session(session)

    assert "CRITICAL" in str(exc_info.value)
    assert "aws_secret_key" in str(exc_info.value).lower()


def test_fail_closed_on_auth_header():
    """CRITICAL: Authorization header with bearer token must fail-closed."""
    session = {
        "messages": [
            {"role": "user", "content": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"}
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        redact_session(session)

    assert "CRITICAL" in str(exc_info.value)
    assert "auth_header" in str(exc_info.value).lower()


def test_multiple_non_critical_redactions():
    """Multiple non-critical patterns should all be redacted."""
    session = {
        "messages": [
            {"role": "user", "content": "Email john@example.com and call 555-1234 using AKIAIOSFODNN7EXAMPLE"}
        ]
    }

    redacted, report = redact_session(session)

    # All should be redacted
    assert "john@example.com" not in str(redacted)
    assert "555-1234" not in str(redacted)
    assert "AKIAIOSFODNN7EXAMPLE" not in str(redacted)

    # Should have fired multiple rules
    assert len(report.rules_fired) >= 2
    assert not report.critical_detected


def test_clean_session_no_redaction():
    """Clean session should pass through unchanged."""
    session = {
        "messages": [
            {"role": "user", "content": "Deploy the API to production"},
            {"role": "assistant", "content": "I'll help with that"}
        ]
    }

    redacted, report = redact_session(session)

    # Should be unchanged
    assert redacted == session
    assert len(report.rules_fired) == 0
    assert not report.critical_detected
