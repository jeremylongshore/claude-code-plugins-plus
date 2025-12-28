#!/usr/bin/env python3

###############################################################################
# license_compliance_checker.py
#
# Check license compatibility of project dependencies
#
# Analyzes licenses and identifies compatibility issues
# Supports multiple package managers and license formats
#
# Usage:
#   ./license_compliance_checker.py
#   ./license_compliance_checker.py --format json
#   ./license_compliance_checker.py --strict --output report.txt
#
# Exit Codes:
#   0 - All licenses compatible
#   1 - Incompatible licenses found
#   2 - Invalid arguments
###############################################################################

import argparse
import json
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class License:
    """Represents a software license."""

    name: str
    spdx_id: str
    category: str  # permissive, copyleft, proprietary, unknown
    description: str

    def is_permissive(self) -> bool:
        """Check if license is permissive."""
        return self.category == "permissive"

    def is_copyleft(self) -> bool:
        """Check if license is copyleft."""
        return self.category == "copyleft"

    def is_proprietary(self) -> bool:
        """Check if license is proprietary."""
        return self.category == "proprietary"


# Known licenses database
KNOWN_LICENSES: Dict[str, License] = {
    "MIT": License("MIT", "MIT", "permissive", "Very permissive license"),
    "Apache-2.0": License(
        "Apache License 2.0", "Apache-2.0", "permissive", "Permissive with patent grant"
    ),
    "BSD-2-Clause": License(
        "BSD 2-Clause", "BSD-2-Clause", "permissive", "Simple BSD-style license"
    ),
    "BSD-3-Clause": License(
        "BSD 3-Clause", "BSD-3-Clause", "permissive", "Standard BSD license"
    ),
    "ISC": License("ISC", "ISC", "permissive", "ISC/OpenBSD style license"),
    "GPL-2.0": License(
        "GNU GPL v2", "GPL-2.0", "copyleft", "Strong copyleft (requires source)"
    ),
    "GPL-3.0": License(
        "GNU GPL v3", "GPL-3.0", "copyleft", "Strong copyleft (requires source)"
    ),
    "LGPL-2.1": License(
        "GNU LGPL v2.1", "LGPL-2.1", "copyleft", "Weak copyleft (library only)"
    ),
    "LGPL-3.0": License(
        "GNU LGPL v3", "LGPL-3.0", "copyleft", "Weak copyleft (library only)"
    ),
    "AGPL-3.0": License(
        "GNU AGPL v3",
        "AGPL-3.0",
        "copyleft",
        "Strong copyleft (includes network use)",
    ),
    "MPL-2.0": License(
        "Mozilla Public License 2.0", "MPL-2.0", "copyleft", "File-level copyleft"
    ),
    "EPL-1.0": License(
        "Eclipse Public License 1.0", "EPL-1.0", "copyleft", "Weak copyleft"
    ),
    "Unlicense": License("Unlicense", "Unlicense", "permissive", "Public domain-like"),
    "CC0-1.0": License("CC0 1.0", "CC0-1.0", "permissive", "Public domain waiver"),
}

# License compatibility matrix (permissive and MIT compatible with all)
INCOMPATIBLE_COMBINATIONS: Set[Tuple[str, str]] = {
    ("GPL-2.0", "Apache-2.0"),  # GPL v2 incompatible with Apache
    ("GPL-2.0", "GPL-3.0"),  # GPL v2 and v3 can conflict
    ("AGPL-3.0", "MIT"),  # AGPL is very restrictive
    ("GPL-3.0", "CDDL-1.0"),  # Some conflicts
}


@dataclass
class Dependency:
    """Represents a project dependency."""

    name: str
    version: str
    license: str
    license_obj: Optional[License] = None

    def is_compatible_with_permissive(self) -> bool:
        """Check if this dependency is compatible with permissive licenses."""
        if self.license_obj is None:
            return False
        return self.license_obj.is_permissive() or self.license_obj.is_proprietary()


class LicenseCompliance:
    """Check license compliance of project dependencies."""

    def __init__(self, strict_mode: bool = False, verbose: bool = False):
        """Initialize the license compliance checker.

        Args:
            strict_mode: Treat warnings as errors
            verbose: Enable verbose output
        """
        self.strict_mode = strict_mode
        self.verbose = verbose
        self.dependencies: List[Dependency] = []
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled.

        Args:
            message: Message to log
        """
        if self.verbose:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message
        """
        print(f"ERROR: {message}", file=sys.stderr)

    def warning(self, message: str) -> None:
        """Add a warning.

        Args:
            message: Warning message
        """
        self.warnings.append(message)
        if self.verbose:
            print(f"[WARNING] {message}", file=sys.stderr)

    def issue(self, message: str) -> None:
        """Add an issue.

        Args:
            message: Issue message
        """
        self.issues.append(message)

    def resolve_license(self, license_str: str) -> Optional[License]:
        """Resolve a license string to a License object.

        Args:
            license_str: License string (name, SPDX ID, or combination)

        Returns:
            License object or None if not found
        """
        if not license_str:
            return None

        # Normalize the string
        license_str = license_str.strip()

        # Check exact match
        if license_str in KNOWN_LICENSES:
            return KNOWN_LICENSES[license_str]

        # Check by SPDX ID
        for lic in KNOWN_LICENSES.values():
            if lic.spdx_id.lower() == license_str.lower():
                return lic

        # Try to find by name
        license_lower = license_str.lower()
        for lic in KNOWN_LICENSES.values():
            if lic.name.lower() in license_lower:
                return lic

        # Unknown license
        self.log(f"Unknown license: {license_str}")
        return None

    def check_npm_licenses(self) -> bool:
        """Check npm/Node.js project licenses.

        Returns:
            True if successful, False otherwise
        """
        self.log("Checking npm licenses")

        try:
            result = subprocess.run(
                ["npm", "ls", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode not in [0, 1]:
                self.error(f"npm ls failed: {result.stderr}")
                return False

            data = json.loads(result.stdout)
            self._process_npm_dependencies(data.get("dependencies", {}))
            return True
        except subprocess.TimeoutExpired:
            self.error("npm ls timeout")
            return False
        except json.JSONDecodeError as e:
            self.error(f"Invalid npm output: {e}")
            return False
        except Exception as e:
            self.error(f"Failed to check npm licenses: {e}")
            return False

    def _process_npm_dependencies(self, deps: Dict[str, Any], parent: str = "") -> None:
        """Process npm dependencies recursively.

        Args:
            deps: Dependencies dictionary
            parent: Parent package name
        """
        for name, info in deps.items():
            if not isinstance(info, dict):
                continue

            version = info.get("version", "unknown")
            license_str = info.get("license", "Unknown")

            self.log(f"Found npm dependency: {name}@{version} ({license_str})")

            license_obj = self.resolve_license(license_str)
            dep = Dependency(
                name=name, version=version, license=license_str, license_obj=license_obj
            )

            self.dependencies.append(dep)

            # Recursively process nested dependencies
            nested = info.get("dependencies", {})
            if nested:
                self._process_npm_dependencies(nested, parent=name)

    def check_python_licenses(self) -> bool:
        """Check Python project licenses.

        Returns:
            True if successful, False otherwise
        """
        self.log("Checking Python licenses")

        try:
            # Try pip-licenses
            if subprocess.run(
                ["pip-licenses", "--version"], capture_output=True
            ).returncode == 0:
                result = subprocess.run(
                    ["pip-licenses", "--format=json", "--with-urls"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    self.warning("pip-licenses failed")
                    return False

                data = json.loads(result.stdout)
                self._process_python_dependencies(data)
                return True
            else:
                self.warning("pip-licenses not installed (install with: pip install pip-licenses)")
                return False

        except subprocess.TimeoutExpired:
            self.error("pip-licenses timeout")
            return False
        except json.JSONDecodeError as e:
            self.error(f"Invalid pip-licenses output: {e}")
            return False
        except Exception as e:
            self.error(f"Failed to check Python licenses: {e}")
            return False

    def _process_python_dependencies(self, deps: List[Dict[str, Any]]) -> None:
        """Process Python dependencies.

        Args:
            deps: Dependencies list
        """
        for dep_info in deps:
            name = dep_info.get("Name", "Unknown")
            version = dep_info.get("Version", "unknown")
            license_str = dep_info.get("License", "Unknown")

            self.log(f"Found Python dependency: {name}@{version} ({license_str})")

            license_obj = self.resolve_license(license_str)
            dep = Dependency(
                name=name, version=version, license=license_str, license_obj=license_obj
            )

            self.dependencies.append(dep)

    def check_compatibility(self) -> None:
        """Check overall license compatibility."""
        if not self.dependencies:
            return

        self.log("Checking compatibility...")

        # Check for unknown licenses
        for dep in self.dependencies:
            if dep.license_obj is None:
                self.warning(f"Unknown license for {dep.name}: {dep.license}")

        # Check for proprietary or restrictive licenses
        for dep in self.dependencies:
            if dep.license_obj and dep.license_obj.is_proprietary():
                self.issue(f"Proprietary license found: {dep.name} ({dep.license})")

            if dep.license_obj and dep.license_obj.is_copyleft():
                # Warn if using strong copyleft
                if dep.license in ["GPL-2.0", "GPL-3.0", "AGPL-3.0"]:
                    self.warning(
                        f"Strong copyleft license: {dep.name} ({dep.license})"
                    )

        # Check for incompatible combinations
        license_types = set()
        for dep in self.dependencies:
            if dep.license_obj:
                license_types.add(dep.license_obj.spdx_id)

        for lic1 in license_types:
            for lic2 in license_types:
                if (lic1, lic2) in INCOMPATIBLE_COMBINATIONS or (
                    lic2,
                    lic1,
                ) in INCOMPATIBLE_COMBINATIONS:
                    self.issue(f"Potentially incompatible licenses: {lic1} and {lic2}")

    def to_text(self) -> str:
        """Format report as plain text.

        Returns:
            Text formatted report
        """
        lines = [
            "License Compliance Report",
            "=" * 70,
            f"\nTotal Dependencies: {len(self.dependencies)}",
            "",
        ]

        # Summary by license type
        by_category: Dict[str, List[Dependency]] = {}
        for dep in self.dependencies:
            category = (
                dep.license_obj.category if dep.license_obj else "unknown"
            )
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(dep)

        lines.append("Summary by Category:")
        for category in sorted(by_category.keys()):
            deps = by_category[category]
            lines.append(f"  {category.upper()}: {len(deps)}")

        # Details
        lines.append("\n" + "-" * 70)
        lines.append("Licenses Found:")
        lines.append("-" * 70)

        for category in sorted(by_category.keys()):
            deps = by_category[category]
            lines.append(f"\n{category.upper()}:")

            for dep in sorted(deps, key=lambda d: d.name):
                lines.append(f"  - {dep.name}@{dep.version}: {dep.license}")

        # Issues and warnings
        if self.issues:
            lines.append("\n" + "!" * 70)
            lines.append("ISSUES:")
            lines.append("!" * 70)
            for issue in self.issues:
                lines.append(f"  - {issue}")

        if self.warnings:
            lines.append("\n" + "-" * 70)
            lines.append("WARNINGS:")
            lines.append("-" * 70)
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        lines.append("")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Format report as JSON.

        Returns:
            JSON formatted report
        """
        output = {
            "summary": {
                "total_dependencies": len(self.dependencies),
                "has_issues": len(self.issues) > 0,
                "has_warnings": len(self.warnings) > 0,
            },
            "dependencies": [
                {
                    "name": dep.name,
                    "version": dep.version,
                    "license": dep.license,
                    "category": (
                        dep.license_obj.category
                        if dep.license_obj
                        else "unknown"
                    ),
                }
                for dep in self.dependencies
            ],
            "issues": self.issues,
            "warnings": self.warnings,
        }

        return json.dumps(output, indent=2)

    def check(self) -> bool:
        """Run complete license compliance check.

        Returns:
            True if no issues, False if issues found
        """
        # Try to detect and check
        if Path("package.json").exists():
            self.check_npm_licenses()

        if Path("requirements.txt").exists() or Path("pyproject.toml").exists():
            self.check_python_licenses()

        # Check compatibility
        self.check_compatibility()

        if self.strict_mode and self.warnings:
            self.issues.extend(self.warnings)

        return len(self.issues) == 0


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for issues, 2 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Check license compatibility of project dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --format json
  %(prog)s --strict --output report.txt
""",
    )

    parser.add_argument(
        "--format",
        "-f",
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Run checker
    checker = LicenseCompliance(strict_mode=args.strict, verbose=args.verbose)

    print("License Compliance Checker")
    print("=" * 70)

    if not checker.check():
        print("License compliance issues found!", file=sys.stderr)

    # Format and output report
    if args.format == "json":
        output = checker.to_json()
    else:
        output = checker.to_text()

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"\nReport saved to: {args.output}")
        except Exception as e:
            print(f"ERROR: Failed to write output: {e}", file=sys.stderr)
            return 1
    else:
        print(output)

    # Return exit code
    if len(checker.issues) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
