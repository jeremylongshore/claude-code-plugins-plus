#!/usr/bin/env python3
"""
Ansible playbook security scanner.

Scans playbook for security vulnerabilities including:
- Hardcoded credentials
- Insecure permissions
- Command injection risks
- Unsafe variable handling
- Missing authentication checks
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
import re


class PlaybookSecurityScanner:
    """Scans Ansible playbooks for security vulnerabilities."""

    # Security rules
    CREDENTIAL_PATTERNS = [
        r'password\s*[:=]\s*["\']?(?!{{)[^"\'\n]+["\']?',
        r'api_key\s*[:=]\s*["\']?[^"\'\n]+["\']?',
        r'secret\s*[:=]\s*["\']?[^"\'\n]+["\']?',
        r'token\s*[:=]\s*["\']?[^"\'\n]+["\']?',
        r'private_key\s*[:=]',
        r'aws_access_key',
        r'aws_secret_key',
    ]

    DANGEROUS_MODULES = {
        'shell': 'Shell module can lead to command injection',
        'command': 'Command module should use specific modules when possible',
        'raw': 'Raw module bypasses ansible modules',
        'lineinfile': 'Lineinfile can create configuration vulnerabilities',
    }

    UNSAFE_PATTERNS = {
        'become_pass': 'Hardcoded become password detected',
        'no_log: false': 'Logging of sensitive data enabled',
        'validate_certs: false': 'Certificate validation disabled',
        'verify_ssl: false': 'SSL verification disabled',
        'insecure: true': 'Insecure mode enabled',
    }

    def __init__(self):
        """Initialize scanner."""
        self.vulnerabilities = []
        self.warnings = []
        self.recommendations = []

    def scan_file(self, file_path: str) -> bool:
        """
        Scan playbook file for vulnerabilities.

        Args:
            file_path: Path to playbook file

        Returns:
            True if no vulnerabilities found
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.vulnerabilities.append(f"File not found: {file_path}")
                return False

            if path.suffix.lower() not in ['.yaml', '.yml']:
                self.vulnerabilities.append(f"Expected YAML file, got: {path.suffix}")
                return False

            # Scan file content as text first (for credentials)
            with open(file_path, 'r') as f:
                content = f.read()
                self._scan_raw_content(content)

            # Parse YAML and scan structure
            with open(file_path, 'r') as f:
                playbooks = yaml.safe_load(f)

            if isinstance(playbooks, list):
                for idx, play in enumerate(playbooks):
                    if isinstance(play, dict):
                        self._scan_play(play, idx)

            return len(self.vulnerabilities) == 0

        except yaml.YAMLError as e:
            self.vulnerabilities.append(f"YAML error: {str(e)}")
            return False
        except Exception as e:
            self.vulnerabilities.append(f"Scan error: {str(e)}")
            return False

    def _scan_raw_content(self, content: str) -> None:
        """Scan raw file content for credentials."""
        lines = content.split('\n')

        for idx, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue

            # Check for hardcoded credentials
            for pattern in self.CREDENTIAL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Verify it's not a variable reference or comment
                    if '{{' not in line and '}}' not in line:
                        self.vulnerabilities.append(
                            f"Line {idx}: Possible hardcoded credential: {line.strip()[:50]}"
                        )

            # Check for unsafe patterns
            for unsafe_pattern, description in self.UNSAFE_PATTERNS.items():
                if unsafe_pattern.lower() in line.lower():
                    self.warnings.append(f"Line {idx}: {description}")

    def _scan_play(self, play: Dict[str, Any], play_idx: int) -> None:
        """Scan individual play."""
        if 'tasks' in play:
            self._scan_tasks(play.get('tasks', []), f'Play {play_idx}')

        if 'handlers' in play:
            self._scan_tasks(play.get('handlers', []), f'Play {play_idx} handlers')

        if 'vars' in play:
            self._scan_vars(play.get('vars', {}), f'Play {play_idx}')

        if 'roles' in play:
            self._scan_roles(play.get('roles', []), f'Play {play_idx}')

    def _scan_tasks(self, tasks: List[Any], context: str) -> None:
        """Scan tasks for security issues."""
        if not isinstance(tasks, list):
            return

        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            # Check for dangerous modules
            for module, issue in self.DANGEROUS_MODULES.items():
                if module in task:
                    self.warnings.append(
                        f"{context} task {idx} ({task.get('name', 'unnamed')}): {issue}"
                    )

                    # Check for unquoted shell commands
                    if module in ['shell', 'command']:
                        cmd = task.get(module, '')
                        if self._has_injection_risk(cmd):
                            self.vulnerabilities.append(
                                f"{context} task {idx}: Possible command injection in {module}"
                            )

            # Check for unsafe sudo usage
            if 'become' in task and task.get('become'):
                if 'become_pass' in task:
                    self.vulnerabilities.append(
                        f"{context} task {idx}: Hardcoded become password detected"
                    )
                if 'become_method' not in task:
                    self.warnings.append(
                        f"{context} task {idx}: become without explicit become_method"
                    )

            # Check for unsafe variable handling
            if 'shell' in task or 'command' in task:
                cmd = task.get('shell') or task.get('command', '')
                if '{{' in cmd and '|' in cmd:
                    if 'quote' not in cmd and 'escape' not in cmd:
                        self.warnings.append(
                            f"{context} task {idx}: Variable in {cmd.split()[0] if cmd else ''} may not be properly escaped"
                        )

            # Check for no_log
            if 'register' in task:
                if 'no_log' not in task:
                    if any(sensitive in task.get('name', '').lower()
                           for sensitive in ['password', 'secret', 'token', 'key']):
                        self.warnings.append(
                            f"{context} task {idx}: Sensitive output not protected with no_log"
                        )

    def _scan_vars(self, variables: Dict[str, Any], context: str) -> None:
        """Scan variables for security issues."""
        if not isinstance(variables, dict):
            return

        for key, value in variables.items():
            # Check for credentials in variable names
            if any(cred_term in key.lower() for cred_term in
                   ['password', 'secret', 'key', 'token', 'credential']):
                if isinstance(value, str) and value and not value.startswith('{{'):
                    self.vulnerabilities.append(
                        f"{context}: Hardcoded credential in variable '{key}'"
                    )

    def _scan_roles(self, roles: List[Any], context: str) -> None:
        """Scan role usage."""
        if not isinstance(roles, list):
            return

        for idx, role in enumerate(roles):
            if isinstance(role, dict):
                if 'vars' in role:
                    self._scan_vars(role['vars'], f'{context} role {idx}')

    def _has_injection_risk(self, command: str) -> bool:
        """Check if command has injection risk."""
        injection_patterns = [
            r'\$\{.*\}',  # ${variable}
            r'\$\(.*\)',  # $(command)
            r'`.*`',      # backticks
        ]

        for pattern in injection_patterns:
            if re.search(pattern, command):
                return True

        return False

    def generate_recommendations(self) -> None:
        """Generate security recommendations."""
        if len(self.vulnerabilities) > 0:
            self.recommendations.append(
                "Fix all identified vulnerabilities before deployment"
            )

        if any('password' in v.lower() for v in self.vulnerabilities):
            self.recommendations.append(
                "Use Ansible Vault or Secret Manager for sensitive data"
            )

        if any('shell' in w.lower() or 'command' in w.lower() for w in self.warnings):
            self.recommendations.append(
                "Replace shell/command with specific Ansible modules when possible"
            )

        if any('become' in w.lower() for w in self.warnings):
            self.recommendations.append(
                "Use Ansible Vault for privilege escalation passwords"
            )

        if not self.recommendations:
            self.recommendations.append(
                "Playbook appears to follow security best practices"
            )

    def get_report(self) -> Dict[str, Any]:
        """Get security scan report."""
        self.generate_recommendations()

        return {
            'secure': len(self.vulnerabilities) == 0,
            'vulnerabilities': self.vulnerabilities,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'vulnerability_count': len(self.vulnerabilities),
            'warning_count': len(self.warnings),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scan Ansible playbook for security vulnerabilities'
    )
    parser.add_argument(
        'playbook_file',
        help='Path to Ansible playbook file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Save security report to JSON file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed security report'
    )
    parser.add_argument(
        '--fail-on-warning',
        action='store_true',
        help='Exit with error if warnings found'
    )

    args = parser.parse_args()

    try:
        scanner = PlaybookSecurityScanner()
        is_secure = scanner.scan_file(args.playbook_file)
        report = scanner.get_report()

        # Check fail-on-warning
        if args.fail_on_warning and report['warning_count'] > 0:
            is_secure = False

        # Output report
        if args.verbose or not is_secure:
            print(json.dumps(report, indent=2))
        else:
            print(f"Security scan complete: {len(report['vulnerabilities'])} vulnerabilities, "
                  f"{len(report['warnings'])} warnings")

        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Security report saved to: {args.output}")

        sys.exit(0 if is_secure else 1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
