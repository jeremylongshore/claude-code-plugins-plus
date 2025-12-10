#!/usr/bin/env python3
"""
Password Policy Validator Script

Evaluates password policies against defined security criteria including
length, complexity, history, and expiration requirements.

Usage:
    password_policy_check.py --config policy.json
    password_policy_check.py --test-password user@password.com --policy policy.json
    password_policy_check.py --analyze /path/to/auth/config
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class PasswordPolicyValidator:
    """Validates password policies and passwords against policies."""

    # Industry standard recommendations
    RECOMMENDED_MIN_LENGTH = 12
    RECOMMENDED_MAX_LENGTH = 128
    RECOMMENDED_HISTORY_COUNT = 5
    RECOMMENDED_MAX_AGE_DAYS = 90

    def __init__(self):
        """Initialize the password policy validator."""
        self.findings = []
        self.warnings = []
        self.info = []

    def validate_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate password policy configuration.

        Args:
            policy: Password policy configuration dictionary

        Returns:
            Validation report dictionary
        """
        self.findings = []
        self.warnings = []
        self.info = []

        if not policy:
            self.findings.append({
                "severity": "critical",
                "issue": "Empty password policy",
                "description": "No password policy configuration found"
            })
            return self._generate_policy_report()

        self._check_length_policy(policy)
        self._check_complexity_policy(policy)
        self._check_history_policy(policy)
        self._check_expiration_policy(policy)
        self._check_lockout_policy(policy)
        self._check_hashing_algorithm(policy)
        self._check_common_patterns(policy)

        return self._generate_policy_report()

    def _check_length_policy(self, policy: Dict[str, Any]) -> None:
        """Check password length requirements."""
        min_length = policy.get("minimum_length", 0)
        max_length = policy.get("maximum_length", 0)

        if min_length == 0:
            self.findings.append({
                "severity": "critical",
                "issue": "No minimum password length specified",
                "description": "Minimum length requirement is essential for password security",
                "recommendation": f"Set minimum length to {self.RECOMMENDED_MIN_LENGTH} characters"
            })
        elif min_length < 8:
            self.findings.append({
                "severity": "critical",
                "issue": f"Minimum password length too short: {min_length}",
                "description": f"Minimum length of {min_length} is insufficient",
                "recommendation": f"Increase minimum length to at least {self.RECOMMENDED_MIN_LENGTH} characters"
            })
        elif min_length < self.RECOMMENDED_MIN_LENGTH:
            self.warnings.append({
                "severity": "high",
                "issue": f"Minimum password length below recommendation: {min_length}",
                "description": f"Industry standard recommends minimum {self.RECOMMENDED_MIN_LENGTH} characters",
                "recommendation": f"Consider increasing minimum length to {self.RECOMMENDED_MIN_LENGTH}"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": "Appropriate minimum length",
                "description": f"Minimum length of {min_length} characters meets recommendations"
            })

        if max_length > 0 and max_length < 64:
            self.warnings.append({
                "severity": "high",
                "issue": f"Maximum password length too restrictive: {max_length}",
                "description": "Limiting password length reduces security",
                "recommendation": f"Increase maximum length to at least {self.RECOMMENDED_MAX_LENGTH}"
            })

    def _check_complexity_policy(self, policy: Dict[str, Any]) -> None:
        """Check password complexity requirements."""
        requires_uppercase = policy.get("require_uppercase", False)
        requires_lowercase = policy.get("require_lowercase", False)
        requires_numbers = policy.get("require_numbers", False)
        requires_special = policy.get("require_special_chars", False)

        complexity_count = sum([
            requires_uppercase,
            requires_lowercase,
            requires_numbers,
            requires_special
        ])

        if complexity_count == 0:
            self.findings.append({
                "severity": "high",
                "issue": "No complexity requirements",
                "description": "Password complexity increases resistance to dictionary attacks",
                "recommendation": "Enable uppercase, lowercase, numbers, and special character requirements"
            })
        elif complexity_count < 3:
            self.warnings.append({
                "severity": "high",
                "issue": "Insufficient complexity requirements",
                "description": "Only {complexity_count} character types required",
                "recommendation": "Enable at least 3 character type requirements"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": "Strong complexity requirements",
                "description": f"All {complexity_count} character types required"
            })

        # Check for overly strict rules
        if policy.get("require_mixed_case") and policy.get("no_consecutive_chars"):
            self.warnings.append({
                "severity": "low",
                "issue": "Potentially overly strict complexity rules",
                "description": "Very strict rules may reduce usability without proportional security gain",
                "recommendation": "Balance security and usability"
            })

    def _check_history_policy(self, policy: Dict[str, Any]) -> None:
        """Check password history requirements."""
        history_count = policy.get("password_history_count", 0)

        if history_count == 0:
            self.warnings.append({
                "severity": "high",
                "issue": "No password history requirement",
                "description": "Users could repeatedly use the same password",
                "recommendation": f"Set password history to at least {self.RECOMMENDED_HISTORY_COUNT}"
            })
        elif history_count < 5:
            self.warnings.append({
                "severity": "medium",
                "issue": f"Low password history requirement: {history_count}",
                "description": "Password history of less than 5 is insufficient",
                "recommendation": f"Increase to {self.RECOMMENDED_HISTORY_COUNT} or more"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": "Appropriate password history",
                "description": f"Password history count of {history_count} meets recommendations"
            })

    def _check_expiration_policy(self, policy: Dict[str, Any]) -> None:
        """Check password expiration requirements."""
        max_age_days = policy.get("password_max_age_days", 0)
        min_age_days = policy.get("password_min_age_days", 0)

        # Check maximum age
        if max_age_days == 0:
            self.warnings.append({
                "severity": "medium",
                "issue": "No password expiration set",
                "description": "Periodic password changes help limit compromise impact",
                "recommendation": f"Set maximum password age to {self.RECOMMENDED_MAX_AGE_DAYS} days"
            })
        elif max_age_days > 365:
            self.findings.append({
                "severity": "high",
                "issue": f"Password expiration too long: {max_age_days} days",
                "description": "Passwords older than 365 days represent elevated risk",
                "recommendation": f"Set maximum age to {self.RECOMMENDED_MAX_AGE_DAYS} days or less"
            })
        elif max_age_days > self.RECOMMENDED_MAX_AGE_DAYS:
            self.warnings.append({
                "severity": "medium",
                "issue": f"Password expiration exceeds recommendation: {max_age_days} days",
                "description": f"Industry standard recommends {self.RECOMMENDED_MAX_AGE_DAYS} days",
                "recommendation": f"Consider reducing to {self.RECOMMENDED_MAX_AGE_DAYS} days"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": "Appropriate password expiration",
                "description": f"Password expiration of {max_age_days} days meets recommendations"
            })

        # Check minimum age
        if min_age_days > 0:
            if min_age_days > 7:
                self.warnings.append({
                    "severity": "medium",
                    "issue": f"Minimum age too high: {min_age_days} days",
                    "description": "Users may be unable to change compromised passwords quickly",
                    "recommendation": "Set minimum age to 1 day or less"
                })

    def _check_lockout_policy(self, policy: Dict[str, Any]) -> None:
        """Check account lockout policy."""
        lockout_config = policy.get("account_lockout", {})

        if not lockout_config or not lockout_config.get("enabled"):
            self.findings.append({
                "severity": "high",
                "issue": "Account lockout not configured",
                "description": "Lockout protects against brute force password attacks",
                "recommendation": "Enable account lockout"
            })
        else:
            max_attempts = lockout_config.get("max_attempts", 0)
            if max_attempts == 0:
                self.findings.append({
                    "severity": "high",
                    "issue": "No maximum attempts limit",
                    "description": "Unlimited attempts allow brute force attacks"
                })
            elif max_attempts > 10:
                self.warnings.append({
                    "severity": "high",
                    "issue": f"High maximum attempts: {max_attempts}",
                    "description": "Should lock after fewer failed attempts",
                    "recommendation": "Set maximum attempts to 5-10"
                })

            lockout_duration = lockout_config.get("lockout_duration_minutes", 0)
            if lockout_duration == 0:
                self.findings.append({
                    "severity": "high",
                    "issue": "No lockout duration specified",
                    "description": "Lockout should prevent further attempts for a period"
                })
            elif lockout_duration < 15:
                self.warnings.append({
                    "severity": "medium",
                    "issue": f"Short lockout duration: {lockout_duration} minutes",
                    "description": "Lockout duration should be at least 15 minutes",
                    "recommendation": "Increase lockout duration to 30-60 minutes"
                })

    def _check_hashing_algorithm(self, policy: Dict[str, Any]) -> None:
        """Check password hashing algorithm configuration."""
        hashing_config = policy.get("hashing", {})

        if not hashing_config:
            self.findings.append({
                "severity": "critical",
                "issue": "No password hashing algorithm configured",
                "description": "Password hashing is essential for security",
                "recommendation": "Configure a strong hashing algorithm (bcrypt, Argon2, PBKDF2)"
            })
            return

        algorithm = hashing_config.get("algorithm", "").lower()

        if not algorithm:
            self.findings.append({
                "severity": "critical",
                "issue": "Hashing algorithm not specified"
            })
        elif algorithm in ["md5", "sha1", "sha256", "sha512"]:
            self.findings.append({
                "severity": "critical",
                "issue": f"Weak hashing algorithm: {algorithm}",
                "description": f"{algorithm} is not suitable for password hashing",
                "recommendation": "Use bcrypt, Argon2, or PBKDF2 instead"
            })
        elif algorithm == "pbkdf2":
            iterations = hashing_config.get("iterations", 0)
            if iterations < 100000:
                self.findings.append({
                    "severity": "high",
                    "issue": f"Insufficient PBKDF2 iterations: {iterations}",
                    "description": "PBKDF2 should use at least 100,000 iterations",
                    "recommendation": "Increase iterations to 600,000 or more"
                })
        elif algorithm == "bcrypt":
            work_factor = hashing_config.get("work_factor", 0)
            if work_factor < 10:
                self.warnings.append({
                    "severity": "high",
                    "issue": f"Low bcrypt work factor: {work_factor}",
                    "description": "Work factor below 10 reduces security",
                    "recommendation": "Set work factor to 10-12"
                })
        elif algorithm == "argon2":
            self.info.append({
                "severity": "info",
                "issue": "Strong hashing algorithm: Argon2",
                "description": "Argon2 is an excellent choice for password hashing"
            })

    def _check_common_patterns(self, policy: Dict[str, Any]) -> None:
        """Check for prevention of common password patterns."""
        rejected_patterns = policy.get("rejected_patterns", [])

        if not rejected_patterns:
            self.warnings.append({
                "severity": "medium",
                "issue": "No pattern rejection configured",
                "description": "Users may choose predictable or unsafe patterns",
                "recommendation": "Configure pattern rejection for common weak patterns"
            })
        else:
            self.info.append({
                "severity": "info",
                "issue": f"{len(rejected_patterns)} patterns rejected",
                "description": f"Policy rejects {len(rejected_patterns)} common weak patterns"
            })

    def test_password(self, password: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test if a password meets policy requirements.

        Args:
            password: Password to test
            policy: Password policy to validate against

        Returns:
            Test result dictionary
        """
        results = {
            "password_valid": True,
            "errors": [],
            "warnings": [],
            "strengths": [],
            "score": 100
        }

        if not password:
            results["password_valid"] = False
            results["errors"].append("Password is empty")
            return results

        # Check length
        min_length = policy.get("minimum_length", 0)
        max_length = policy.get("maximum_length", 0)

        if len(password) < min_length:
            results["password_valid"] = False
            results["errors"].append(f"Password too short (minimum {min_length} characters)")
            results["score"] -= 30

        if max_length > 0 and len(password) > max_length:
            results["password_valid"] = False
            results["errors"].append(f"Password too long (maximum {max_length} characters)")
            results["score"] -= 30

        # Check complexity
        has_uppercase = bool(re.search(r'[A-Z]', password))
        has_lowercase = bool(re.search(r'[a-z]', password))
        has_numbers = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password))

        if policy.get("require_uppercase") and not has_uppercase:
            results["password_valid"] = False
            results["errors"].append("Password must contain uppercase letters")
            results["score"] -= 25

        if policy.get("require_lowercase") and not has_lowercase:
            results["password_valid"] = False
            results["errors"].append("Password must contain lowercase letters")
            results["score"] -= 25

        if policy.get("require_numbers") and not has_numbers:
            results["password_valid"] = False
            results["errors"].append("Password must contain numbers")
            results["score"] -= 25

        if policy.get("require_special_chars") and not has_special:
            results["password_valid"] = False
            results["errors"].append("Password must contain special characters")
            results["score"] -= 25

        # Check for common patterns
        common_patterns = ["123", "abc", "password", "qwerty", "111", "000", "sequential"]
        for pattern in common_patterns:
            if pattern.lower() in password.lower():
                results["warnings"].append(f"Contains common pattern: {pattern}")
                results["score"] -= 10

        # Positive feedback
        if len(password) >= 16:
            results["strengths"].append("Password length is excellent")

        if has_uppercase + has_lowercase + has_numbers + has_special >= 3:
            results["strengths"].append("Good character variety")

        results["score"] = max(0, results["score"])
        return results

    def _generate_policy_report(self) -> Dict[str, Any]:
        """Generate policy validation report."""
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
        description="Validate password policies and test passwords",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  password_policy_check.py --config policy.json
  password_policy_check.py --policy policy.json --test MyPassword123!
  password_policy_check.py --policy policy.json --test-password weak --output result.json
        """
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to password policy JSON file"
    )
    parser.add_argument(
        "-p", "--policy",
        type=str,
        help="Path to password policy JSON file (alias for --config)"
    )
    parser.add_argument(
        "-t", "--test",
        type=str,
        help="Test a password against the policy"
    )
    parser.add_argument(
        "-tp", "--test-password",
        type=str,
        help="Test a password against the policy"
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

    policy_file = args.config or args.policy
    if not policy_file:
        parser.error("--config or --policy is required")

    try:
        config_path = Path(policy_file)
        if not config_path.exists():
            print(f"Error: Policy file not found: {policy_file}", file=sys.stderr)
            return 1

        with open(config_path, 'r') as f:
            policy = json.load(f)

        validator = PasswordPolicyValidator()

        # If testing a password
        if args.test or args.test_password:
            password = args.test or args.test_password
            result = validator.test_password(password, policy)
        else:
            # Validate policy
            result = validator.validate_policy(policy)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Report written to: {args.output}")
        else:
            print(json.dumps(result, indent=2))

        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
