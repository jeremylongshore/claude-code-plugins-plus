#!/usr/bin/env python3
"""
CORS Policy Validator Script

Validates cross-origin resource sharing (CORS) policies and identifies security
vulnerabilities. Supports JSON configuration files and live API endpoint analysis.

Usage:
    validate_cors.py --file cors_policy.json
    validate_cors.py --url https://example.com/api
    validate_cors.py --config config.json --output report.json
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from datetime import datetime


class CORSValidator:
    """Validates CORS policies against security best practices."""

    # Common dangerous CORS configurations
    DANGEROUS_ORIGINS = ["*", "null", "about:blank"]

    # Standard secure headers
    SECURE_HEADERS = {
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Access-Control-Max-Age",
    }

    # Methods that should be restricted
    DANGEROUS_METHODS = ["*"]

    # Headers that should not be exposed
    DANGEROUS_HEADERS = [
        "Authorization",
        "X-API-Key",
        "Set-Cookie",
        "Cookie",
        "X-CSRF-Token",
    ]

    def __init__(self):
        """Initialize the CORS validator."""
        self.findings = []
        self.warnings = []
        self.info = []

    def validate_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a CORS policy configuration.

        Args:
            policy: CORS policy dictionary

        Returns:
            Validation report dictionary
        """
        self.findings = []
        self.warnings = []
        self.info = []

        if not policy:
            self.findings.append({
                "severity": "critical",
                "issue": "Empty CORS policy",
                "description": "No CORS configuration found"
            })
            return self._generate_report()

        self._check_origins(policy)
        self._check_methods(policy)
        self._check_headers(policy)
        self._check_credentials(policy)
        self._check_max_age(policy)

        return self._generate_report()

    def _check_origins(self, policy: Dict[str, Any]) -> None:
        """Check origin configuration for vulnerabilities."""
        origins = policy.get("origins", [])

        if not origins:
            self.warnings.append({
                "severity": "warning",
                "issue": "No origins specified",
                "description": "CORS policy does not specify allowed origins"
            })
            return

        if isinstance(origins, str):
            origins = [origins]

        for origin in origins:
            if origin == "*":
                self.findings.append({
                    "severity": "critical",
                    "issue": "Wildcard origin (*) allowed",
                    "description": "CORS policy allows requests from any origin. This is a critical security vulnerability.",
                    "recommendation": "Specify explicit allowed origins instead of using wildcard"
                })
            elif origin == "null":
                self.findings.append({
                    "severity": "high",
                    "issue": "Null origin allowed",
                    "description": "Allowing 'null' origin can be exploited by local files or sandboxed documents",
                    "recommendation": "Remove 'null' from allowed origins"
                })
            elif not self._is_valid_origin(origin):
                self.warnings.append({
                    "severity": "warning",
                    "issue": "Invalid origin format",
                    "description": f"Origin '{origin}' does not match expected URL format",
                    "recommendation": "Use format: https://example.com"
                })
            else:
                self.info.append({
                    "severity": "info",
                    "issue": "Valid origin configured",
                    "description": f"Origin '{origin}' is properly formatted"
                })

    def _check_methods(self, policy: Dict[str, Any]) -> None:
        """Check HTTP methods configuration."""
        methods = policy.get("methods", [])

        if not methods:
            self.info.append({
                "severity": "info",
                "issue": "No HTTP methods specified",
                "description": "Consider specifying allowed HTTP methods"
            })
            return

        if isinstance(methods, str):
            methods = [methods]

        if "*" in methods:
            self.findings.append({
                "severity": "high",
                "issue": "Wildcard HTTP methods (*) allowed",
                "description": "CORS policy allows all HTTP methods. Consider restricting to necessary methods only.",
                "recommendation": "Specify only required methods: GET, POST, PUT, DELETE, etc."
            })
            return

        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        for method in methods:
            if method.upper() not in valid_methods:
                self.warnings.append({
                    "severity": "warning",
                    "issue": "Unusual HTTP method",
                    "description": f"HTTP method '{method}' is not standard",
                    "recommendation": f"Review if '{method}' is necessary"
                })

    def _check_headers(self, policy: Dict[str, Any]) -> None:
        """Check allowed and exposed headers."""
        allowed_headers = policy.get("allowed_headers", [])
        exposed_headers = policy.get("exposed_headers", [])

        if isinstance(allowed_headers, str):
            allowed_headers = [allowed_headers]
        if isinstance(exposed_headers, str):
            exposed_headers = [exposed_headers]

        # Check allowed headers
        if "*" in allowed_headers:
            self.findings.append({
                "severity": "high",
                "issue": "Wildcard allowed headers (*)",
                "description": "All request headers are allowed. Consider being more restrictive.",
                "recommendation": "Specify only necessary headers"
            })

        # Check exposed headers for sensitive data
        for header in exposed_headers:
            if header in self.DANGEROUS_HEADERS:
                self.findings.append({
                    "severity": "high",
                    "issue": f"Sensitive header exposed: {header}",
                    "description": f"Exposing '{header}' header can leak sensitive information",
                    "recommendation": f"Remove '{header}' from exposed_headers"
                })

    def _check_credentials(self, policy: Dict[str, Any]) -> None:
        """Check credentials configuration."""
        credentials = policy.get("credentials", False)
        origins = policy.get("origins", [])

        if credentials:
            if isinstance(origins, str):
                origins = [origins]

            if "*" in origins or "null" in origins:
                self.findings.append({
                    "severity": "critical",
                    "issue": "Credentials allowed with wildcard/null origins",
                    "description": "Allowing credentials with wildcard or null origins is a critical security vulnerability",
                    "recommendation": "Specify explicit origins when credentials are enabled"
                })

    def _check_max_age(self, policy: Dict[str, Any]) -> None:
        """Check max age configuration."""
        max_age = policy.get("max_age", None)

        if max_age is None:
            self.info.append({
                "severity": "info",
                "issue": "Max-Age not specified",
                "description": "Consider setting Access-Control-Max-Age for performance"
            })
        elif max_age < 0:
            self.warnings.append({
                "severity": "warning",
                "issue": "Invalid Max-Age value",
                "description": f"Max-Age should be non-negative, got: {max_age}"
            })
        elif max_age > 86400:  # More than 24 hours
            self.warnings.append({
                "severity": "warning",
                "issue": "Very high Max-Age value",
                "description": f"Max-Age of {max_age} seconds (>{86400}) may reduce security effectiveness",
                "recommendation": "Consider using a lower value (e.g., 3600 for 1 hour)"
            })

    @staticmethod
    def _is_valid_origin(origin: str) -> bool:
        """Validate origin URL format."""
        try:
            result = urlparse(origin)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "critical": len([f for f in self.findings if f.get("severity") == "critical"]),
                "high": len([f for f in self.findings if f.get("severity") == "high"]),
                "warning": len(self.warnings),
                "info": len(self.info),
                "passed": len(self.findings) == 0 and len(self.warnings) == 0
            },
            "findings": self.findings,
            "warnings": self.warnings,
            "info": self.info,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []

        if len([f for f in self.findings if f.get("severity") == "critical"]) > 0:
            recommendations.append("Address all critical security issues immediately")

        if len([f for f in self.findings if f.get("severity") == "high"]) > 0:
            recommendations.append("Review and fix high-priority security issues")

        if len(self.warnings) > 0:
            recommendations.append("Consider the warnings and improve security posture")

        if not recommendations:
            recommendations.append("CORS policy configuration appears secure")

        return recommendations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate CORS policies for security vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  validate_cors.py --file cors.json
  validate_cors.py --file cors.json --output report.json
  validate_cors.py --config example.json
        """
    )

    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to CORS policy JSON file"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file"
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

    # Validate arguments
    if not args.file and not args.config:
        parser.error("Either --file or --config must be specified")

    try:
        # Load CORS policy
        policy_file = args.file or args.config
        policy_path = Path(policy_file)

        if not policy_path.exists():
            print(f"Error: File not found: {policy_file}", file=sys.stderr)
            return 1

        with open(policy_path, 'r') as f:
            policy = json.load(f)

        # Validate policy
        validator = CORSValidator()
        report = validator.validate_policy(policy)

        # Output report
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report written to: {args.output}")
        else:
            print(json.dumps(report, indent=2))

        # Return appropriate exit code
        if report["summary"]["critical"] > 0:
            return 1
        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {policy_file}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
