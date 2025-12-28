#!/usr/bin/env python3

###############################################################################
# generate_env_file.py
#
# Generates a .env file based on a Docker Compose file
# Extracts environment variables and pre-fills with defaults
#
# Usage:
#   ./generate_env_file.py --compose docker-compose.yml
#   ./generate_env_file.py --compose docker-compose.yml --output .env.local
#   ./generate_env_file.py --compose docker-compose.yml --template template.env
#
# Exit Codes:
#   0 - Success
#   1 - Error
#   2 - Invalid arguments
###############################################################################

import argparse
import json
import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class EnvGenerator:
    """Generate .env files from Docker Compose configurations."""

    COMMON_DEFAULTS = {
        "DEBUG": "false",
        "LOG_LEVEL": "info",
        "ENVIRONMENT": "development",
        "NODE_ENV": "development",
        "PYTHON_ENV": "development",
        "PORT": "8000",
        "DATABASE_PORT": "5432",
        "REDIS_PORT": "6379",
        "POSTGRES_PASSWORD": "change_me_in_production",
        "MYSQL_PASSWORD": "change_me_in_production",
        "MONGODB_PASSWORD": "change_me_in_production",
    }

    def __init__(self, compose_file: str, verbose: bool = False):
        """Initialize the environment generator.

        Args:
            compose_file: Path to the Docker Compose file
            verbose: Enable verbose output
        """
        self.compose_file = Path(compose_file)
        self.verbose = verbose
        self.compose_data = {}
        self.env_vars: Dict[str, str] = {}

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled.

        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        if self.verbose:
            print(f"[{level}] {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message
        """
        print(f"ERROR: {message}", file=sys.stderr)

    def load_compose_file(self) -> bool:
        """Load the Docker Compose file.

        Returns:
            True if successful, False otherwise
        """
        if not self.compose_file.exists():
            self.error(f"Compose file not found: {self.compose_file}")
            return False

        try:
            with open(self.compose_file, "r") as f:
                self.compose_data = yaml.safe_load(f) or {}
            self.log(f"Loaded compose file: {self.compose_file}")
            return True
        except yaml.YAMLError as e:
            self.error(f"Failed to parse YAML: {e}")
            return False
        except Exception as e:
            self.error(f"Failed to load compose file: {e}")
            return False

    def extract_env_vars_from_compose(self) -> None:
        """Extract environment variables from the compose file."""
        services = self.compose_data.get("services", {})

        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue

            self.log(f"Processing service: {service_name}")

            # Extract from environment section
            env = service_config.get("environment", {})
            if isinstance(env, dict):
                for key, value in env.items():
                    if value is not None:
                        self.env_vars[key] = str(value)
                    else:
                        self.env_vars[key] = ""
            elif isinstance(env, list):
                # Handle list format like ["KEY=value", "KEY2=value2"]
                for item in env:
                    if "=" in item:
                        key, value = item.split("=", 1)
                        self.env_vars[key] = value
                    else:
                        self.env_vars[item] = ""

            # Extract from env_file references
            env_files = service_config.get("env_file", [])
            if isinstance(env_files, str):
                env_files = [env_files]

            for env_file in env_files:
                self.log(f"  Referenced env file: {env_file}")
                self._extract_from_env_file(env_file)

    def _extract_from_env_file(self, env_file_path: str) -> None:
        """Extract variables from a referenced env file.

        Args:
            env_file_path: Path to the env file
        """
        file_path = self.compose_file.parent / env_file_path

        if not file_path.exists():
            self.log(f"Referenced env file not found: {file_path}", "WARNING")
            return

        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key not in self.env_vars:
                            self.env_vars[key] = value
        except Exception as e:
            self.log(f"Failed to read env file: {e}", "WARNING")

    def extract_variables_from_values(self) -> None:
        """Extract variable references from service values (${VAR})."""
        for service_name, service_config in self.compose_data.get("services", {}).items():
            if not isinstance(service_config, dict):
                continue

            config_str = json.dumps(service_config)
            pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
            matches = re.findall(pattern, config_str)

            for var_name in matches:
                if var_name not in self.env_vars:
                    self.env_vars[var_name] = self._get_default_value(var_name)

    def _get_default_value(self, var_name: str) -> str:
        """Get a sensible default value for a variable name.

        Args:
            var_name: Variable name

        Returns:
            Default value or empty string
        """
        if var_name in self.COMMON_DEFAULTS:
            return self.COMMON_DEFAULTS[var_name]

        # Pattern-based defaults
        if "PASSWORD" in var_name:
            return "change_me_in_production"
        if "TOKEN" in var_name or "SECRET" in var_name or "KEY" in var_name:
            return "your_secret_here"
        if "URL" in var_name or "HOST" in var_name or "ENDPOINT" in var_name:
            return "http://localhost:8000"
        if "PORT" in var_name:
            return "8000"
        if "USERNAME" in var_name or "USER" in var_name:
            return "admin"
        if "EMAIL" in var_name:
            return "user@example.com"

        return ""

    def generate_env_content(self) -> str:
        """Generate the .env file content.

        Returns:
            The formatted .env file content
        """
        lines = [
            "# Auto-generated environment variables from Docker Compose",
            "# Generated file - update values as needed for your environment",
            "#",
        ]

        # Sort variables for consistency
        sorted_vars = sorted(self.env_vars.items())

        for key, value in sorted_vars:
            if value:
                # Quote values with spaces or special characters
                if any(char in value for char in [" ", "$", '"', "'"]):
                    value = f'"{value}"'
                lines.append(f"{key}={value}")
            else:
                lines.append(f"{key}=")

        lines.append("")  # Trailing newline
        return "\n".join(lines)

    def save_env_file(self, output_file: str, overwrite: bool = False) -> bool:
        """Save the generated env file.

        Args:
            output_file: Path where to save the env file
            overwrite: Whether to overwrite existing files

        Returns:
            True if successful, False otherwise
        """
        output_path = Path(output_file)

        if output_path.exists() and not overwrite:
            self.error(f"File already exists: {output_file} (use --force to overwrite)")
            return False

        try:
            content = self.generate_env_content()
            with open(output_path, "w") as f:
                f.write(content)

            # Set restrictive permissions on the env file
            os.chmod(output_path, 0o600)

            self.log(f"Saved env file: {output_file}")
            return True
        except Exception as e:
            self.error(f"Failed to save env file: {e}")
            return False

    def print_env_vars(self) -> None:
        """Print all extracted variables to stdout."""
        if not self.env_vars:
            print("No environment variables found")
            return

        print(f"Found {len(self.env_vars)} environment variable(s):")
        print()

        sorted_vars = sorted(self.env_vars.items())
        for key, value in sorted_vars:
            if value:
                print(f"  {key}={value}")
            else:
                print(f"  {key}=")

    def generate(self) -> bool:
        """Run the full generation process.

        Returns:
            True if successful, False otherwise
        """
        if not self.load_compose_file():
            return False

        self.extract_env_vars_from_compose()
        self.extract_variables_from_values()

        self.log(f"Extracted {len(self.env_vars)} environment variables")

        return True


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error, 2 for invalid arguments)
    """
    parser = argparse.ArgumentParser(
        description="Generate .env files from Docker Compose files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --compose docker-compose.yml
  %(prog)s --compose docker-compose.yml --output .env.local
  %(prog)s --compose docker-compose.yml --output .env --force
  %(prog)s --compose docker-compose.yml --print
""",
    )

    parser.add_argument(
        "--compose",
        "-c",
        required=True,
        help="Path to Docker Compose file",
    )

    parser.add_argument(
        "--output",
        "-o",
        default=".env",
        help="Output .env file path (default: .env)",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing .env file",
    )

    parser.add_argument(
        "--print",
        "-p",
        action="store_true",
        help="Print variables to stdout instead of saving to file",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Create generator
    generator = EnvGenerator(args.compose, verbose=args.verbose)

    # Run generation
    if not generator.generate():
        return 1

    # Output results
    if args.print:
        generator.print_env_vars()
    else:
        if not generator.save_env_file(args.output, overwrite=args.force):
            return 1
        print(f"Generated .env file: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
