#!/usr/bin/env python3
"""
CORS Policy Test Case Generator

Generates comprehensive test cases for different CORS configurations,
ensuring coverage of potential vulnerabilities and security scenarios.

Usage:
    generate_test_cases.py --output test_cases.json
    generate_test_cases.py --template cors.json --output tests.json
    generate_test_cases.py --coverage high --output comprehensive_tests.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class CORSTestCaseGenerator:
    """Generates comprehensive test cases for CORS policies."""

    def __init__(self):
        """Initialize test case generator."""
        self.test_cases = []

    def generate_test_cases(self, coverage: str = "standard") -> List[Dict[str, Any]]:
        """
        Generate test cases based on coverage level.

        Args:
            coverage: Coverage level (basic, standard, comprehensive, high)

        Returns:
            List of test case dictionaries
        """
        self.test_cases = []

        if coverage in ["basic", "standard", "comprehensive", "high"]:
            self._generate_origin_tests()
            self._generate_method_tests()
            self._generate_header_tests()
            self._generate_credential_tests()

            if coverage in ["comprehensive", "high"]:
                self._generate_edge_case_tests()
                self._generate_advanced_attack_tests()

        return self.test_cases

    def _add_test_case(
        self,
        name: str,
        description: str,
        policy: Dict[str, Any],
        expected_result: str,
        severity: str = "medium"
    ) -> None:
        """Add a test case to the collection."""
        self.test_cases.append({
            "id": f"test_{len(self.test_cases) + 1:03d}",
            "name": name,
            "description": description,
            "policy": policy,
            "expected_result": expected_result,
            "severity": severity,
            "category": "security_test"
        })

    def _generate_origin_tests(self) -> None:
        """Generate tests for origin validation."""
        # Test 1: Wildcard origin
        self._add_test_case(
            name="Wildcard Origin Vulnerability",
            description="Tests if policy allows requests from any origin",
            policy={
                "origins": ["*"],
                "methods": ["GET", "POST"],
                "credentials": False
            },
            expected_result="FAIL",
            severity="critical"
        )

        # Test 2: Null origin
        self._add_test_case(
            name="Null Origin Vulnerability",
            description="Tests if policy allows null origin",
            policy={
                "origins": ["null"],
                "methods": ["GET"],
                "credentials": False
            },
            expected_result="FAIL",
            severity="high"
        )

        # Test 3: Specific origins
        self._add_test_case(
            name="Specific Origins",
            description="Tests valid specific origin configuration",
            policy={
                "origins": ["https://example.com", "https://app.example.com"],
                "methods": ["GET", "POST"],
                "credentials": False
            },
            expected_result="PASS",
            severity="info"
        )

        # Test 4: Subdomain wildcard
        self._add_test_case(
            name="Subdomain Wildcard",
            description="Tests if policy allows subdomain wildcards",
            policy={
                "origins": ["https://*.example.com"],
                "methods": ["GET", "POST"],
                "credentials": False
            },
            expected_result="WARNING",
            severity="high"
        )

        # Test 5: Mixed HTTP and HTTPS
        self._add_test_case(
            name="Mixed HTTP and HTTPS Origins",
            description="Tests configuration with both HTTP and HTTPS",
            policy={
                "origins": ["http://example.com", "https://example.com"],
                "methods": ["GET"],
                "credentials": False
            },
            expected_result="PASS",
            severity="info"
        )

    def _generate_method_tests(self) -> None:
        """Generate tests for HTTP method validation."""
        # Test 6: Wildcard methods
        self._add_test_case(
            name="Wildcard HTTP Methods",
            description="Tests if policy allows all HTTP methods",
            policy={
                "origins": ["https://example.com"],
                "methods": ["*"],
                "credentials": False
            },
            expected_result="FAIL",
            severity="high"
        )

        # Test 7: Restrictive methods
        self._add_test_case(
            name="Restrictive HTTP Methods",
            description="Tests policy with limited HTTP methods",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET", "POST"],
                "credentials": False
            },
            expected_result="PASS",
            severity="info"
        )

        # Test 8: Dangerous method combinations
        self._add_test_case(
            name="Dangerous Method Combination",
            description="Tests configuration allowing DELETE and PUT from public origins",
            policy={
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "credentials": False
            },
            expected_result="FAIL",
            severity="critical"
        )

        # Test 9: Safe method subset
        self._add_test_case(
            name="Safe Method Subset",
            description="Tests policy with only safe methods",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET", "HEAD", "OPTIONS"],
                "credentials": False
            },
            expected_result="PASS",
            severity="info"
        )

    def _generate_header_tests(self) -> None:
        """Generate tests for header validation."""
        # Test 10: Wildcard allowed headers
        self._add_test_case(
            name="Wildcard Allowed Headers",
            description="Tests if policy allows all request headers",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET", "POST"],
                "allowed_headers": ["*"]
            },
            expected_result="WARNING",
            severity="medium"
        )

        # Test 11: Sensitive exposed headers
        self._add_test_case(
            name="Sensitive Exposed Headers",
            description="Tests exposure of Authorization and API key headers",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET"],
                "exposed_headers": ["Authorization", "X-API-Key"]
            },
            expected_result="FAIL",
            severity="high"
        )

        # Test 12: Safe exposed headers
        self._add_test_case(
            name="Safe Exposed Headers",
            description="Tests exposure of non-sensitive headers",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET"],
                "exposed_headers": ["Content-Type", "X-Total-Count", "X-Page-Number"]
            },
            expected_result="PASS",
            severity="info"
        )

        # Test 13: Cookie exposure
        self._add_test_case(
            name="Cookie Header Exposure",
            description="Tests exposure of Set-Cookie header",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET"],
                "exposed_headers": ["Set-Cookie"]
            },
            expected_result="FAIL",
            severity="critical"
        )

    def _generate_credential_tests(self) -> None:
        """Generate tests for credential handling."""
        # Test 14: Credentials with wildcard origins
        self._add_test_case(
            name="Credentials with Wildcard Origins",
            description="Tests critical vulnerability: credentials allowed with wildcard origins",
            policy={
                "origins": ["*"],
                "methods": ["GET", "POST"],
                "credentials": True
            },
            expected_result="FAIL",
            severity="critical"
        )

        # Test 15: Credentials with specific origins
        self._add_test_case(
            name="Credentials with Specific Origins",
            description="Tests safe credentials configuration",
            policy={
                "origins": ["https://trusted.example.com"],
                "methods": ["GET", "POST"],
                "credentials": True
            },
            expected_result="PASS",
            severity="info"
        )

        # Test 16: Credentials with multiple origins
        self._add_test_case(
            name="Credentials with Multiple Origins",
            description="Tests credentials with multiple specific origins",
            policy={
                "origins": ["https://app1.example.com", "https://app2.example.com"],
                "methods": ["GET", "POST"],
                "credentials": True
            },
            expected_result="PASS",
            severity="info"
        )

    def _generate_edge_case_tests(self) -> None:
        """Generate edge case tests."""
        # Test 17: Empty configuration
        self._add_test_case(
            name="Empty CORS Configuration",
            description="Tests behavior with empty policy",
            policy={},
            expected_result="WARNING",
            severity="medium"
        )

        # Test 18: Max age too high
        self._add_test_case(
            name="Excessive Max Age",
            description="Tests policy with very high max_age value",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET"],
                "max_age": 604800  # 7 days
            },
            expected_result="WARNING",
            severity="low"
        )

        # Test 19: Invalid origin format
        self._add_test_case(
            name="Invalid Origin Format",
            description="Tests policy with malformed origin",
            policy={
                "origins": ["invalid-origin", "https://valid.com"],
                "methods": ["GET"]
            },
            expected_result="WARNING",
            severity="medium"
        )

        # Test 20: Localhost origin
        self._add_test_case(
            name="Localhost Origin",
            description="Tests configuration with localhost",
            policy={
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET", "POST"],
                "credentials": True
            },
            expected_result="INFO",
            severity="info"
        )

    def _generate_advanced_attack_tests(self) -> None:
        """Generate tests for advanced attack scenarios."""
        # Test 21: Regex-based origin bypass
        self._add_test_case(
            name="Potential Regex Origin Bypass",
            description="Tests policy vulnerable to regex bypass",
            policy={
                "origins": ["https://example.com.*"],
                "methods": ["GET", "POST"],
                "credentials": False
            },
            expected_result="WARNING",
            severity="high"
        )

        # Test 22: Port manipulation
        self._add_test_case(
            name="Port-based Origin Distinction",
            description="Tests configuration distinguishing ports",
            policy={
                "origins": ["https://example.com:443", "https://example.com:8443"],
                "methods": ["GET"]
            },
            expected_result="PASS",
            severity="info"
        )

        # Test 23: Case sensitivity
        self._add_test_case(
            name="Origin Case Sensitivity Test",
            description="Tests if origin matching respects case",
            policy={
                "origins": ["https://Example.com", "https://example.com"],
                "methods": ["GET"]
            },
            expected_result="PASS",
            severity="info"
        )

        # Test 24: Path-based origins
        self._add_test_case(
            name="Path in Origin",
            description="Tests if policy attempts to use paths in origin",
            policy={
                "origins": ["https://example.com/api"],
                "methods": ["GET"]
            },
            expected_result="WARNING",
            severity="medium"
        )

        # Test 25: Superdomain risk
        self._add_test_case(
            name="Superdomain Vulnerability",
            description="Tests configuration allowing parent domain",
            policy={
                "origins": ["https://example.com"],
                "methods": ["GET", "POST"],
                "credentials": True
            },
            expected_result="PASS",
            severity="info"
        )

    def generate_from_template(self, template_path: str) -> List[Dict[str, Any]]:
        """
        Generate test cases based on existing policy template.

        Args:
            template_path: Path to CORS policy template file

        Returns:
            List of test cases
        """
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)

            # Generate variations of the template
            variations = self._create_policy_variations(template)
            return variations
        except Exception as e:
            print(f"Error loading template: {e}", file=sys.stderr)
            return []

    @staticmethod
    def _create_policy_variations(base_policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create policy variations for testing."""
        variations = []
        variations.append({
            "id": "variation_original",
            "name": "Original Policy",
            "policy": base_policy,
            "expected_result": "EVALUATE"
        })
        return variations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate CORS policy test cases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  generate_test_cases.py --output test_cases.json
  generate_test_cases.py --coverage high --output comprehensive_tests.json
  generate_test_cases.py --template cors.json --output variant_tests.json
        """
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default="cors_test_cases.json",
        help="Output file for test cases (default: cors_test_cases.json)"
    )
    parser.add_argument(
        "-c", "--coverage",
        type=str,
        choices=["basic", "standard", "comprehensive", "high"],
        default="standard",
        help="Coverage level for test generation (default: standard)"
    )
    parser.add_argument(
        "-t", "--template",
        type=str,
        help="Template CORS policy file to generate variations from"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        generator = CORSTestCaseGenerator()

        if args.template:
            if not Path(args.template).exists():
                print(f"Error: Template file not found: {args.template}", file=sys.stderr)
                return 1
            test_cases = generator.generate_from_template(args.template)
        else:
            test_cases = generator.generate_test_cases(coverage=args.coverage)

        # Create output structure
        output = {
            "generated": datetime.now().isoformat(),
            "coverage": args.coverage,
            "total_tests": len(test_cases),
            "test_cases": test_cases,
            "summary": {
                "critical": len([t for t in test_cases if t.get("severity") == "critical"]),
                "high": len([t for t in test_cases if t.get("severity") == "high"]),
                "medium": len([t for t in test_cases if t.get("severity") == "medium"]),
                "low": len([t for t in test_cases if t.get("severity") == "low"]),
                "info": len([t for t in test_cases if t.get("severity") == "info"])
            }
        }

        # Write output
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Generated {len(test_cases)} test cases")
        print(f"Output written to: {args.output}")

        if args.verbose:
            print("\nSeverity Summary:")
            for severity, count in output["summary"].items():
                if count > 0:
                    print(f"  {severity}: {count}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
