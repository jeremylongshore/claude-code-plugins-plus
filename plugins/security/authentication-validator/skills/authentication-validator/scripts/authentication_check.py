#!/usr/bin/env python3
"""
Authentication Validator Script

Automates validation of authentication implementations against security best practices.
Checks JWT, OAuth, session-based, and API key implementations.

Usage:
    authentication_check.py --config auth.json
    authentication_check.py --code app.py --output report.json
    authentication_check.py --scan /path/to/project
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class AuthenticationValidator:
    """Validates authentication implementations."""

    def __init__(self):
        """Initialize the authentication validator."""
        self.findings = []
        self.warnings = []
        self.info = []

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate authentication configuration.

        Args:
            config: Authentication configuration dictionary

        Returns:
            Validation report dictionary
        """
        self.findings = []
        self.warnings = []
        self.info = []

        if not config:
            self.findings.append({
                "severity": "critical",
                "issue": "Empty authentication configuration",
                "description": "No authentication configuration found"
            })
            return self._generate_report()

        # Determine auth method and validate accordingly
        auth_method = config.get("method", "unknown")

        if auth_method == "jwt":
            self._validate_jwt(config)
        elif auth_method == "oauth":
            self._validate_oauth(config)
        elif auth_method == "session":
            self._validate_session(config)
        elif auth_method == "api_key":
            self._validate_api_key(config)
        else:
            self.warnings.append({
                "severity": "warning",
                "issue": "Unknown authentication method",
                "description": f"Authentication method '{auth_method}' is not recognized"
            })

        # Generic authentication checks
        self._check_password_policy(config)
        self._check_mfa(config)
        self._check_account_lockout(config)

        return self._generate_report()

    def _validate_jwt(self, config: Dict[str, Any]) -> None:
        """Validate JWT configuration."""
        jwt_config = config.get("jwt", {})

        # Check signing algorithm
        algorithm = jwt_config.get("algorithm", "")
        if not algorithm:
            self.findings.append({
                "severity": "critical",
                "issue": "No signing algorithm specified",
                "description": "JWT configuration missing algorithm",
                "recommendation": "Specify a strong algorithm (e.g., HS256, RS256)"
            })
        elif algorithm in ["none", "HS256"] and jwt_config.get("use_public_key"):
            self.findings.append({
                "severity": "critical",
                "issue": f"Weak JWT algorithm: {algorithm}",
                "description": "Using HS256 with public key verification is vulnerable",
                "recommendation": "Use RS256 or ES256 with proper key management"
            })
        elif algorithm in ["HS256"]:
            self.warnings.append({
                "severity": "high",
                "issue": "HS256 algorithm used",
                "description": "HS256 is symmetric and less secure than RS256 or ES256",
                "recommendation": "Consider migrating to RS256 (RSA) or ES256 (ECDSA)"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": "Strong JWT algorithm",
                "description": f"Using {algorithm} for JWT signing"
            })

        # Check token expiration
        expiration = jwt_config.get("expiration_seconds")
        if not expiration:
            self.findings.append({
                "severity": "high",
                "issue": "No token expiration set",
                "description": "JWT tokens without expiration present a security risk",
                "recommendation": "Set expiration to a reasonable value (e.g., 3600 seconds)"
            })
        elif expiration > 86400:  # More than 24 hours
            self.warnings.append({
                "severity": "high",
                "issue": f"Very long token expiration: {expiration} seconds",
                "description": "Token expiration exceeds 24 hours, increasing compromise risk",
                "recommendation": "Reduce expiration to 1-24 hours depending on use case"
            })

        # Check refresh token
        refresh_token = jwt_config.get("refresh_token", {})
        if not refresh_token:
            self.warnings.append({
                "severity": "medium",
                "issue": "No refresh token mechanism",
                "description": "Consider implementing refresh tokens for better security"
            })
        else:
            refresh_expiration = refresh_token.get("expiration_seconds")
            if refresh_expiration and refresh_expiration <= expiration:
                self.findings.append({
                    "severity": "high",
                    "issue": "Refresh token expiration <= access token expiration",
                    "description": "Refresh token should have longer expiration than access token",
                    "recommendation": "Set refresh token expiration to 7-30 days"
                })

        # Check audience and issuer
        if not jwt_config.get("audience"):
            self.warnings.append({
                "severity": "medium",
                "issue": "JWT audience not specified",
                "description": "Audience claim helps prevent token misuse",
                "recommendation": "Add audience validation to JWT validation"
            })

        if not jwt_config.get("issuer"):
            self.warnings.append({
                "severity": "medium",
                "issue": "JWT issuer not specified",
                "description": "Issuer claim helps identify token source",
                "recommendation": "Add issuer validation to JWT validation"
            })

    def _validate_oauth(self, config: Dict[str, Any]) -> None:
        """Validate OAuth configuration."""
        oauth_config = config.get("oauth", {})

        # Check client credentials security
        client_secret = oauth_config.get("client_secret")
        if not client_secret:
            self.findings.append({
                "severity": "critical",
                "issue": "No client secret configured",
                "description": "OAuth client secret is missing"
            })

        # Check redirect URIs
        redirect_uris = oauth_config.get("redirect_uris", [])
        if not redirect_uris:
            self.findings.append({
                "severity": "high",
                "issue": "No redirect URIs configured",
                "description": "OAuth configuration missing redirect URIs",
                "recommendation": "Specify all allowed redirect URIs"
            })
        else:
            for uri in redirect_uris:
                if uri == "*" or uri.endswith("/*"):
                    self.findings.append({
                        "severity": "critical",
                        "issue": f"Wildcard redirect URI: {uri}",
                        "description": "Wildcard redirect URIs enable open redirect attacks",
                        "recommendation": "Specify exact redirect URIs only"
                    })
                elif not uri.startswith("https://"):
                    self.warnings.append({
                        "severity": "high",
                        "issue": f"Non-HTTPS redirect URI: {uri}",
                        "description": "HTTP redirect URIs can leak authorization codes",
                        "recommendation": "Use HTTPS for all redirect URIs"
                    })

        # Check scope configuration
        scopes = oauth_config.get("scopes", [])
        if not scopes:
            self.warnings.append({
                "severity": "medium",
                "issue": "No OAuth scopes defined",
                "description": "Scopes should be restricted to necessary permissions"
            })

        # Check PKCE
        if not oauth_config.get("pkce_enabled"):
            self.warnings.append({
                "severity": "high",
                "issue": "PKCE not enabled",
                "description": "PKCE should be enabled to prevent authorization code interception",
                "recommendation": "Enable PKCE for all OAuth flows"
            })

    def _validate_session(self, config: Dict[str, Any]) -> None:
        """Validate session-based authentication."""
        session_config = config.get("session", {})

        # Check cookie attributes
        cookie_config = session_config.get("cookie", {})

        if not cookie_config.get("secure"):
            self.findings.append({
                "severity": "critical",
                "issue": "Secure flag not set on session cookie",
                "description": "Session cookie can be transmitted over HTTP",
                "recommendation": "Set 'Secure' flag on session cookie"
            })

        if not cookie_config.get("httponly"):
            self.findings.append({
                "severity": "high",
                "issue": "HttpOnly flag not set on session cookie",
                "description": "Session cookie can be accessed via JavaScript (XSS vulnerability)",
                "recommendation": "Set 'HttpOnly' flag on session cookie"
            })

        samesite = cookie_config.get("samesite", "").lower()
        if samesite not in ["strict", "lax"]:
            self.findings.append({
                "severity": "high",
                "issue": f"SameSite attribute not properly set: {samesite}",
                "description": "SameSite protection against CSRF is not configured",
                "recommendation": "Set SameSite to 'Strict' or 'Lax'"
            })

        # Check session timeout
        timeout = session_config.get("timeout_seconds")
        if not timeout:
            self.warnings.append({
                "severity": "high",
                "issue": "No session timeout configured",
                "description": "Sessions should have a timeout for security"
            })
        elif timeout > 86400:  # More than 24 hours
            self.warnings.append({
                "severity": "high",
                "issue": f"Very long session timeout: {timeout} seconds",
                "description": "Session timeout exceeds 24 hours",
                "recommendation": "Reduce session timeout to 30 minutes to 8 hours"
            })

        # Check idle timeout
        idle_timeout = session_config.get("idle_timeout_seconds")
        if not idle_timeout:
            self.warnings.append({
                "severity": "medium",
                "issue": "No idle timeout configured",
                "description": "Sessions should timeout after inactivity"
            })

    def _validate_api_key(self, config: Dict[str, Any]) -> None:
        """Validate API key authentication."""
        api_key_config = config.get("api_key", {})

        # Check key storage
        if api_key_config.get("store_plaintext"):
            self.findings.append({
                "severity": "critical",
                "issue": "API keys stored in plaintext",
                "description": "API keys should never be stored in plaintext",
                "recommendation": "Hash API keys using bcrypt or PBKDF2"
            })

        # Check key length
        min_length = api_key_config.get("minimum_length", 0)
        if min_length < 32:
            self.warnings.append({
                "severity": "high",
                "issue": f"Short API key minimum length: {min_length}",
                "description": "API keys should be at least 32 characters",
                "recommendation": "Set minimum length to 64 or use UUID v4"
            })

        # Check key rotation
        if not api_key_config.get("rotation_enabled"):
            self.warnings.append({
                "severity": "high",
                "issue": "API key rotation not enabled",
                "description": "API keys should be rotated periodically",
                "recommendation": "Implement automatic key rotation every 90 days"
            })

        # Check rate limiting
        if not api_key_config.get("rate_limiting_enabled"):
            self.warnings.append({
                "severity": "medium",
                "issue": "Rate limiting not enabled for API keys",
                "description": "API keys should have rate limiting to prevent abuse"
            })

    def _check_password_policy(self, config: Dict[str, Any]) -> None:
        """Check password policy configuration."""
        password_policy = config.get("password_policy", {})

        if not password_policy:
            self.findings.append({
                "severity": "high",
                "issue": "No password policy defined",
                "description": "Password policies help ensure strong credentials"
            })
            return

        # Check minimum length
        min_length = password_policy.get("minimum_length", 0)
        if min_length < 8:
            self.findings.append({
                "severity": "high",
                "issue": f"Weak password minimum length: {min_length}",
                "description": "Passwords should be at least 12 characters",
                "recommendation": "Set minimum password length to 12-16 characters"
            })

        # Check complexity requirements
        requires_uppercase = password_policy.get("require_uppercase", False)
        requires_lowercase = password_policy.get("require_lowercase", False)
        requires_numbers = password_policy.get("require_numbers", False)
        requires_special = password_policy.get("require_special_chars", False)

        if not (requires_uppercase and requires_lowercase and requires_numbers):
            self.warnings.append({
                "severity": "medium",
                "issue": "Weak password complexity requirements",
                "description": "Passwords should require mixed case, numbers, and special characters",
                "recommendation": "Enable uppercase, lowercase, numeric, and special character requirements"
            })

        # Check password history
        history_count = password_policy.get("password_history_count", 0)
        if history_count < 5:
            self.warnings.append({
                "severity": "medium",
                "issue": f"Low password history requirement: {history_count}",
                "description": "Password history should prevent reuse of recent passwords"
            })

    def _check_mfa(self, config: Dict[str, Any]) -> None:
        """Check multi-factor authentication configuration."""
        mfa_config = config.get("mfa", {})

        if not mfa_config or not mfa_config.get("enabled"):
            self.warnings.append({
                "severity": "high",
                "issue": "Multi-factor authentication not enabled",
                "description": "MFA provides additional account protection",
                "recommendation": "Enable and enforce MFA for all users or sensitive operations"
            })
        else:
            mfa_methods = mfa_config.get("methods", [])
            if not mfa_methods:
                self.findings.append({
                    "severity": "high",
                    "issue": "No MFA methods configured",
                    "description": "At least one MFA method should be available"
                })
            elif "sms" in mfa_methods and not "totp" in mfa_methods:
                self.warnings.append({
                    "severity": "medium",
                    "issue": "Only SMS MFA available",
                    "description": "TOTP should be offered as more secure alternative to SMS"
                })

    def _check_account_lockout(self, config: Dict[str, Any]) -> None:
        """Check account lockout policy."""
        lockout_config = config.get("account_lockout", {})

        if not lockout_config or not lockout_config.get("enabled"):
            self.findings.append({
                "severity": "high",
                "issue": "Account lockout not configured",
                "description": "Account lockout helps prevent brute force attacks",
                "recommendation": "Enable account lockout after N failed attempts"
            })
        else:
            max_attempts = lockout_config.get("max_attempts", 0)
            if max_attempts == 0 or max_attempts > 10:
                self.warnings.append({
                    "severity": "medium",
                    "issue": f"High account lockout threshold: {max_attempts}",
                    "description": "Account lockout should occur within 5 failed attempts"
                })

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "critical": len([f for f in self.findings if f.get("severity") == "critical"]),
                "high": len([f for f in self.findings if f.get("severity") == "high"]),
                "medium": len([f for f in self.findings if f.get("severity") == "medium"]),
                "warning": len(self.warnings),
                "info": len(self.info),
                "passed": len(self.findings) == 0 and len(self.warnings) == 0
            },
            "findings": self.findings,
            "warnings": self.warnings,
            "info": self.info
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate authentication implementations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  authentication_check.py --config auth.json
  authentication_check.py --config auth.json --output report.json
        """
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to authentication configuration JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file for JSON report (stdout if not specified)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if not args.config:
        parser.error("--config is required")

    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            return 1

        with open(config_path, 'r') as f:
            config = json.load(f)

        validator = AuthenticationValidator()
        report = validator.validate_config(config)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report written to: {args.output}")
        else:
            print(json.dumps(report, indent=2))

        if report["summary"]["critical"] > 0:
            return 1
        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.config}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
