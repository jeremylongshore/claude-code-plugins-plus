#!/usr/bin/env python3
"""
JWT Token Analyzer Script

Analyzes JWT tokens by extracting claims, validating signatures, and checking
for security best practices compliance.

Usage:
    jwt_analyzer.py --token "eyJ..." --key public_key.pem
    jwt_analyzer.py --file jwt.txt --algorithm RS256
    jwt_analyzer.py --token "eyJ..." --validate
"""

import argparse
import json
import sys
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hmac
import hashlib


class JWTAnalyzer:
    """Analyzes JWT tokens for security issues."""

    VALID_ALGORITHMS = {
        "HS256", "HS384", "HS512",  # HMAC
        "RS256", "RS384", "RS512",  # RSA
        "ES256", "ES384", "ES512",  # ECDSA
        "PS256", "PS384", "PS512"   # RSA PSS
    }

    WEAK_ALGORITHMS = {"HS256", "HS384", "HS512"}
    STRONG_ALGORITHMS = {"RS256", "ES256", "PS256"}

    def __init__(self):
        """Initialize JWT analyzer."""
        self.findings = []
        self.warnings = []
        self.info = []

    def analyze_token(self, token: str, algorithm: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a JWT token.

        Args:
            token: JWT token string
            algorithm: Expected algorithm (for validation)

        Returns:
            Analysis report dictionary
        """
        self.findings = []
        self.warnings = []
        self.info = []

        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {
                    "valid": False,
                    "error": "Invalid JWT format (expected 3 parts separated by dots)",
                    "timestamp": datetime.now().isoformat()
                }

            header, payload, signature = parts

            # Decode header and payload
            decoded_header = self._decode_jwt_part(header)
            decoded_payload = self._decode_jwt_part(payload)

            if not decoded_header or not decoded_payload:
                return {
                    "valid": False,
                    "error": "Failed to decode JWT parts",
                    "timestamp": datetime.now().isoformat()
                }

            # Parse JSON
            try:
                header_json = json.loads(decoded_header)
                payload_json = json.loads(decoded_payload)
            except json.JSONDecodeError as e:
                return {
                    "valid": False,
                    "error": f"Invalid JSON in JWT: {e}",
                    "timestamp": datetime.now().isoformat()
                }

            # Analyze components
            self._analyze_header(header_json, algorithm)
            self._analyze_payload(payload_json)

            return self._generate_report(header_json, payload_json, signature)

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @staticmethod
    def _decode_jwt_part(part: str) -> Optional[str]:
        """Safely decode a base64url-encoded JWT part."""
        try:
            # Add padding if needed
            padding = 4 - (len(part) % 4)
            if padding != 4:
                part += '=' * padding

            decoded = base64.urlsafe_b64decode(part)
            return decoded.decode('utf-8')
        except Exception:
            return None

    def _analyze_header(self, header: Dict[str, Any], expected_alg: Optional[str] = None) -> None:
        """Analyze JWT header."""
        alg = header.get("alg", "")
        typ = header.get("typ", "")

        # Check algorithm
        if not alg:
            self.findings.append({
                "severity": "critical",
                "issue": "Missing algorithm in header",
                "description": "JWT header must specify an algorithm"
            })
        elif alg not in self.VALID_ALGORITHMS:
            self.findings.append({
                "severity": "critical",
                "issue": f"Invalid algorithm: {alg}",
                "description": f"Algorithm '{alg}' is not a valid JWT algorithm"
            })
        elif alg == "none":
            self.findings.append({
                "severity": "critical",
                "issue": "Algorithm set to 'none'",
                "description": "Using 'none' algorithm disables signature verification (critical vulnerability)",
                "recommendation": "Use a secure algorithm (RS256, ES256, etc.)"
            })
        elif alg in self.WEAK_ALGORITHMS:
            self.warnings.append({
                "severity": "high",
                "issue": f"Weak algorithm: {alg}",
                "description": "HMAC algorithms (HS256, etc.) are symmetric and less secure",
                "recommendation": "Consider migrating to RS256 (RSA) or ES256 (ECDSA)"
            })
        elif alg in self.STRONG_ALGORITHMS:
            self.info.append({
                "severity": "info",
                "issue": f"Strong algorithm: {alg}",
                "description": f"Using secure {alg} algorithm"
            })

        # Check if algorithm matches expected
        if expected_alg and alg != expected_alg:
            self.warnings.append({
                "severity": "high",
                "issue": f"Algorithm mismatch",
                "description": f"Expected {expected_alg} but found {alg}",
                "recommendation": "Verify token was issued with correct algorithm"
            })

        # Check typ claim
        if typ and typ.lower() != "jwt":
            self.warnings.append({
                "severity": "low",
                "issue": f"Unusual token type: {typ}",
                "description": "Expected 'JWT' type"
            })

        # Check for extra claims in header
        standard_claims = {"alg", "typ", "kid", "cty"}
        extra_claims = set(header.keys()) - standard_claims
        if extra_claims:
            self.info.append({
                "severity": "info",
                "issue": f"Extra header claims: {', '.join(extra_claims)}",
                "description": "Non-standard claims in header"
            })

    def _analyze_payload(self, payload: Dict[str, Any]) -> None:
        """Analyze JWT payload (claims)."""
        now = datetime.utcnow().timestamp()

        # Check expiration
        exp = payload.get("exp")
        if not exp:
            self.findings.append({
                "severity": "high",
                "issue": "Missing expiration claim (exp)",
                "description": "Tokens should have expiration times",
                "recommendation": "Add 'exp' claim with reasonable timeout"
            })
        else:
            if isinstance(exp, (int, float)):
                exp_datetime = datetime.utcfromtimestamp(exp)
                if exp < now:
                    self.warnings.append({
                        "severity": "warning",
                        "issue": f"Token has expired",
                        "description": f"Expiration time: {exp_datetime.isoformat()}",
                        "expired_at": exp_datetime.isoformat()
                    })
                else:
                    expires_in_seconds = int(exp - now)
                    self.info.append({
                        "severity": "info",
                        "issue": "Token is valid",
                        "description": f"Expires in {expires_in_seconds} seconds",
                        "expires_at": exp_datetime.isoformat()
                    })

        # Check issued at
        iat = payload.get("iat")
        if iat:
            if isinstance(iat, (int, float)):
                iat_datetime = datetime.utcfromtimestamp(iat)
                self.info.append({
                    "severity": "info",
                    "issue": "Token issued time",
                    "description": f"Issued at: {iat_datetime.isoformat()}",
                    "issued_at": iat_datetime.isoformat()
                })

        # Check not before
        nbf = payload.get("nbf")
        if nbf:
            if isinstance(nbf, (int, float)):
                nbf_datetime = datetime.utcfromtimestamp(nbf)
                if nbf > now:
                    self.warnings.append({
                        "severity": "warning",
                        "issue": "Token not yet valid",
                        "description": f"Valid from: {nbf_datetime.isoformat()}"
                    })

        # Check audience
        aud = payload.get("aud")
        if not aud:
            self.warnings.append({
                "severity": "medium",
                "issue": "Missing audience claim (aud)",
                "description": "Audience claim helps prevent token misuse",
                "recommendation": "Add 'aud' claim specifying intended audience"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": f"Audience specified: {aud}",
                "description": "Token is intended for specific audience(s)"
            })

        # Check issuer
        iss = payload.get("iss")
        if not iss:
            self.warnings.append({
                "severity": "medium",
                "issue": "Missing issuer claim (iss)",
                "description": "Issuer claim identifies token source",
                "recommendation": "Add 'iss' claim"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": f"Issuer: {iss}",
                "description": "Token issuer is identified"
            })

        # Check subject
        sub = payload.get("sub")
        if not sub:
            self.warnings.append({
                "severity": "low",
                "issue": "Missing subject claim (sub)",
                "description": "Subject claim typically identifies the user/entity"
            })

        # Check for sensitive data in payload
        sensitive_keywords = {"password", "secret", "api_key", "private_key", "token"}
        for key in payload.keys():
            if any(keyword in key.lower() for keyword in sensitive_keywords):
                self.findings.append({
                    "severity": "high",
                    "issue": f"Potential sensitive data in payload: {key}",
                    "description": "JWT payloads are base64-encoded but NOT encrypted",
                    "recommendation": "Do not store passwords, API keys, or secrets in JWT payload"
                })

        # Check token length
        payload_size = sum(len(str(v)) for v in payload.values())
        if payload_size > 5000:
            self.warnings.append({
                "severity": "medium",
                "issue": "Large JWT payload",
                "description": f"Payload size exceeds 5KB (actual: {payload_size} bytes)",
                "recommendation": "Keep JWT payloads small for performance"
            })

    def _generate_report(
        self,
        header: Dict[str, Any],
        payload: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """Generate analysis report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "valid": len([f for f in self.findings if f.get("severity") == "critical"]) == 0,
            "header": {
                "algorithm": header.get("alg"),
                "type": header.get("typ"),
                "key_id": header.get("kid"),
                "full": header
            },
            "payload": {
                "subject": payload.get("sub"),
                "issuer": payload.get("iss"),
                "audience": payload.get("aud"),
                "expires_at": datetime.utcfromtimestamp(payload.get("exp")).isoformat() if payload.get("exp") else None,
                "issued_at": datetime.utcfromtimestamp(payload.get("iat")).isoformat() if payload.get("iat") else None,
                "not_before": datetime.utcfromtimestamp(payload.get("nbf")).isoformat() if payload.get("nbf") else None,
                "custom_claims": {k: v for k, v in payload.items() if k not in ["sub", "iss", "aud", "exp", "iat", "nbf", "jti"]},
                "full": payload
            },
            "signature": {
                "value": signature[:50] + "..." if len(signature) > 50 else signature,
                "note": "Signature validation requires the signing key"
            },
            "summary": {
                "critical": len([f for f in self.findings if f.get("severity") == "critical"]),
                "high": len([f for f in self.findings if f.get("severity") == "high"]),
                "medium": len([f for f in self.findings if f.get("severity") == "medium"]),
                "warning": len(self.warnings),
                "info": len(self.info)
            },
            "findings": self.findings,
            "warnings": self.warnings,
            "info": self.info,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations."""
        recommendations = []

        if len([f for f in self.findings if f.get("severity") == "critical"]) > 0:
            recommendations.append("Address critical issues immediately")

        if any("password" in str(f) or "secret" in str(f) or "key" in str(f) for f in self.findings):
            recommendations.append("Remove sensitive data from JWT payload")

        if any("expiration" in str(f) or "exp" in str(f) for f in self.findings + self.warnings):
            recommendations.append("Always use expiration claims (exp) on tokens")

        if not recommendations:
            recommendations.append("JWT appears to follow security best practices")

        return recommendations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze JWT tokens for security issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jwt_analyzer.py --token "eyJ..."
  jwt_analyzer.py --token "eyJ..." --algorithm RS256
  jwt_analyzer.py --file token.txt --output analysis.json
        """
    )

    parser.add_argument(
        "-t", "--token",
        type=str,
        help="JWT token to analyze"
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="File containing JWT token"
    )
    parser.add_argument(
        "-a", "--algorithm",
        type=str,
        help="Expected signing algorithm (for validation)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file for JSON report"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Get token
    token = None
    if args.token:
        token = args.token
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                token = f.read().strip()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1
    else:
        parser.error("Either --token or --file is required")

    try:
        analyzer = JWTAnalyzer()
        report = analyzer.analyze_token(token, args.algorithm)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Analysis written to: {args.output}")
        else:
            print(json.dumps(report, indent=2))

        # Exit code based on critical issues
        if not report.get("valid"):
            return 1
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
