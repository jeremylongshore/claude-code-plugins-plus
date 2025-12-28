#!/usr/bin/env python3
"""
Ansible playbook validator.

Validates playbook syntax and structure using:
- YAML syntax validation
- Ansible-lint integration
- Task validation
- Handler validation
- Variable validation
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess
import yaml


class PlaybookValidator:
    """Validates Ansible playbooks."""

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: Enable strict validation mode
        """
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.playbooks = []

    def validate_file(self, file_path: str) -> bool:
        """
        Validate playbook file.

        Args:
            file_path: Path to playbook file

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.errors.append(f"File not found: {file_path}")
                return False

            if path.suffix.lower() not in ['.yaml', '.yml']:
                self.errors.append(f"Expected YAML file, got: {path.suffix}")
                return False

            # Load and validate YAML
            if not self._validate_yaml(file_path):
                return False

            # Validate syntax with ansible-playbook
            if not self._validate_syntax(file_path):
                return False

            # Validate structure
            if not self._validate_structure(file_path):
                return False

            # Run ansible-lint if available
            self._run_ansible_lint(file_path)

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
            return False

    def _validate_yaml(self, file_path: str) -> bool:
        """Validate YAML syntax."""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, list):
                self.errors.append("Playbook must be a YAML list (array)")
                return False

            if not data:
                self.errors.append("Playbook is empty")
                return False

            return True

        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {str(e)}")
            return False

    def _validate_syntax(self, file_path: str) -> bool:
        """Validate playbook syntax with ansible-playbook."""
        try:
            result = subprocess.run(
                ['ansible-playbook', '--syntax-check', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.errors.append(f"Playbook syntax error: {result.stderr}")
                return False

            return True

        except FileNotFoundError:
            self.warnings.append("ansible-playbook not found, skipping syntax check")
            return True
        except subprocess.TimeoutExpired:
            self.errors.append("Syntax check timeout")
            return False

    def _validate_structure(self, file_path: str) -> bool:
        """Validate playbook structure."""
        try:
            with open(file_path, 'r') as f:
                playbooks = yaml.safe_load(f)

            if not isinstance(playbooks, list):
                return True

            for idx, play in enumerate(playbooks):
                if not isinstance(play, dict):
                    self.errors.append(f"Play {idx}: must be a dictionary")
                    return False

                # Check required fields
                if 'name' not in play:
                    self.warnings.append(f"Play {idx}: missing 'name' field")

                if 'hosts' not in play:
                    self.errors.append(f"Play {idx}: missing 'hosts' field")
                    return False

                # Validate tasks
                if 'tasks' in play:
                    if not self._validate_tasks(play.get('tasks', []), f'Play {idx}'):
                        return False

                # Validate handlers
                if 'handlers' in play:
                    if not self._validate_handlers(play.get('handlers', []), f'Play {idx}'):
                        return False

                # Validate variables
                if 'vars' in play:
                    if not self._validate_vars(play.get('vars', {}), f'Play {idx}'):
                        return False

                self.playbooks.append({
                    'name': play.get('name', f'unnamed_play_{idx}'),
                    'hosts': play.get('hosts'),
                    'tasks': len(play.get('tasks', [])),
                    'handlers': len(play.get('handlers', [])),
                })

            return True

        except Exception as e:
            self.errors.append(f"Structure validation error: {str(e)}")
            return False

    def _validate_tasks(self, tasks: List[Any], context: str) -> bool:
        """Validate tasks."""
        if not isinstance(tasks, list):
            self.errors.append(f"{context}: tasks must be a list")
            return False

        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                self.errors.append(f"{context} task {idx}: must be a dictionary")
                return False

            # Check that task has either 'name' or a module
            has_name = 'name' in task
            has_module = any(k in task for k in self._get_common_modules())

            if not has_name:
                self.warnings.append(f"{context} task {idx}: missing 'name'")

            if not has_module and not has_name:
                self.errors.append(f"{context} task {idx}: missing task module")
                return False

            # Check for common issues
            if 'debug' in task:
                if 'msg' not in task['debug']:
                    self.warnings.append(f"{context} task {idx} (debug): prefer 'msg:' over 'var:'")

            if 'shell' in task or 'command' in task:
                if 'warn' not in task:
                    self.warnings.append(
                        f"{context} task {idx}: shell/command should set warn: false or use module"
                    )

        return True

    def _validate_handlers(self, handlers: List[Any], context: str) -> bool:
        """Validate handlers."""
        if not isinstance(handlers, list):
            self.errors.append(f"{context}: handlers must be a list")
            return False

        for idx, handler in enumerate(handlers):
            if not isinstance(handler, dict):
                self.errors.append(f"{context} handler {idx}: must be a dictionary")
                return False

            if 'name' not in handler:
                self.errors.append(f"{context} handler {idx}: missing 'name'")
                return False

        return True

    def _validate_vars(self, variables: Dict[str, Any], context: str) -> bool:
        """Validate variables."""
        if not isinstance(variables, dict):
            self.errors.append(f"{context}: vars must be a dictionary")
            return False

        # Check for common variable issues
        for key, value in variables.items():
            # Warn about empty string defaults
            if isinstance(value, str) and not value:
                self.warnings.append(f"{context}: variable '{key}' is empty")

        return True

    def _run_ansible_lint(self, file_path: str) -> None:
        """Run ansible-lint if available."""
        try:
            result = subprocess.run(
                ['ansible-lint', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                # Parse ansible-lint output
                for line in result.stdout.split('\n'):
                    if 'error' in line.lower():
                        self.errors.append(f"ansible-lint: {line}")
                    elif 'warning' in line.lower():
                        self.warnings.append(f"ansible-lint: {line}")

        except FileNotFoundError:
            self.warnings.append("ansible-lint not found, skipping linting")
        except subprocess.TimeoutExpired:
            self.warnings.append("ansible-lint timeout")

    def _get_common_modules(self) -> List[str]:
        """Get list of common Ansible modules."""
        return [
            'debug', 'shell', 'command', 'copy', 'template', 'file',
            'lineinfile', 'replace', 'service', 'package', 'apt', 'yum',
            'git', 'get_url', 'uri', 'wait_for', 'handlers', 'block',
            'set_fact', 'include', 'import_tasks', 'loop', 'when',
            'register', 'notify', 'changed_when', 'failed_when',
        ]

    def get_report(self) -> Dict[str, Any]:
        """Get validation report."""
        return {
            'valid': len(self.errors) == 0,
            'playbooks': self.playbooks,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'playbook_count': len(self.playbooks),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Ansible playbook syntax and structure'
    )
    parser.add_argument(
        'playbook_file',
        help='Path to Ansible playbook file (YAML)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Save validation report to JSON file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed validation report'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )

    args = parser.parse_args()

    try:
        validator = PlaybookValidator(strict=args.strict)
        is_valid = validator.validate_file(args.playbook_file)
        report = validator.get_report()

        # Check strict mode
        if args.strict and report['warning_count'] > 0:
            is_valid = False

        # Output report
        if args.verbose or not is_valid:
            print(json.dumps(report, indent=2))

        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Validation report saved to: {args.output}")

        sys.exit(0 if is_valid else 1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
